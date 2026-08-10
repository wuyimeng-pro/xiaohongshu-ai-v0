from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import base64
import time
import uuid
import hashlib
import secrets
import requests
import json
import pymysql
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
import jwt
from dotenv import load_dotenv

load_dotenv()
ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")

# 数据库连接参数（从 .env 读取，带本地开发默认值）
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'database': os.getenv('DB_NAME', 'xiaohongshu_ai'),
    'charset': 'utf8mb4'
}

# JWT 鉴权配置
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_EXPIRE_HOURS = 24 * 7
security = HTTPBearer(auto_error=False)

# 管理员邀请码：注册时填写该码可创建管理员账号（留空则无法注册管理员）
ADMIN_CODE = os.getenv("ADMIN_CODE", "")

# 上传图片保存目录（自动创建）
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 单张图片大小上限：20MB
MAX_FILE_SIZE = 20 * 1024 * 1024


def detect_image_type(content: bytes):
    """根据文件内容（魔数）识别真实图片类型，返回 (mime_type, 扩展名)；不认识则返回 None"""
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", ".gif"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp", ".webp"
    if content.startswith(b"BM"):
        return "image/bmp", ".bmp"
    return None


def hash_password(password: str) -> str:
    """使用 PBKDF2-SHA256 加盐哈希密码，不存明文"""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()
    return f"pbkdf2_sha256$100000${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return secrets.compare_digest(digest, expected)
    except Exception:
        return False


def create_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="请先登录")
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return payload


def get_db():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


class RegisterRequest(BaseModel):
    username: str
    password: str
    admin_code: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class RefineRequest(BaseModel):
    record_id: int
    instruction: str
    versions: int = 1


class UrlUploadRequest(BaseModel):
    url: str
    product_name: str = ""
    target_audience: str = ""
    tone_style: str = ""


class StreamRequest(BaseModel):
    url: str = ""
    record_id: Optional[int] = None
    product_name: str = ""
    target_audience: str = ""
    tone_style: str = ""
    instruction: str = ""


app = FastAPI()

# 上传目录静态访问（历史记录页展示图片用）
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Qwen-VL 文案生成后端已启动！"}


@app.post("/api/register")
def register(data: RegisterRequest, conn: pymysql.connections.Connection = Depends(get_db)):
    username = data.username.strip()
    password = data.password
    if not (3 <= len(username) <= 20):
        raise HTTPException(status_code=400, detail="账号长度需为 3~20 个字符")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="该账号已被注册")

    role = "admin" if ADMIN_CODE and data.admin_code.strip() == ADMIN_CODE else "user"
    cursor.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
        (username, hash_password(password), role),
    )
    conn.commit()
    user_id = cursor.lastrowid
    token = create_token(user_id, username, role)
    return {
        "status": "success",
        "token": token,
        "user": {"id": user_id, "username": username, "role": role},
    }


@app.post("/api/login")
def login(data: LoginRequest, conn: pymysql.connections.Connection = Depends(get_db)):
    username = data.username.strip()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = %s",
        (username,),
    )
    row = cursor.fetchone()
    if not row or not verify_password(data.password, row[2]):
        raise HTTPException(status_code=400, detail="账号或密码错误")

    token = create_token(row[0], row[1], row[3])
    return {
        "status": "success",
        "token": token,
        "user": {"id": row[0], "username": row[1], "role": row[3]},
    }


@app.post("/api/logout")
def logout():
    # JWT 为无状态鉴权：前端清除本地 token 即完成退出
    return {"status": "success", "message": "已退出登录"}


@app.get("/api/me")
def me(user: dict = Depends(get_current_user)):
    return {
        "status": "success",
        "user": {"id": int(user["sub"]), "username": user["username"], "role": user["role"]},
    }


@app.get("/api/records")
def list_records(
    user: dict = Depends(get_current_user),
    conn: pymysql.connections.Connection = Depends(get_db),
):
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, image_name, image_path, product_name, target_audience, tone_style,
                  instruction, title, body, tags, created_at
           FROM generation_records
           WHERE user_id = %s
           ORDER BY id DESC""",
        (int(user["sub"]),),
    )
    rows = cursor.fetchall()
    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "image_name": r[1],
            "image_path": r[2],
            "product_name": r[3],
            "target_audience": r[4],
            "tone_style": r[5],
            "instruction": r[6],
            "title": r[7],
            "body": r[8],
            "tags": r[9].split(",") if r[9] else [],
            "created_at": r[10].strftime("%Y-%m-%d %H:%M:%S") if r[10] else None,
        })
    return {"status": "success", "records": records}


@app.post("/api/refine")
def refine_copy(
    data: RefineRequest,
    user: dict = Depends(get_current_user),
    conn: pymysql.connections.Connection = Depends(get_db),
):
    instruction = data.instruction.strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="请填写修改意见")
    if not (1 <= data.versions <= 3):
        raise HTTPException(status_code=400, detail="版本数需为 1~3")

    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, user_id, image_name, image_path, product_name, target_audience,
                  tone_style, title, body, tags
           FROM generation_records WHERE id = %s""",
        (data.record_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    if row[1] != int(user["sub"]):
        raise HTTPException(status_code=403, detail="只能调优自己的记录")

    image_name, image_rel, product_name, target_audience, tone_style = row[2], row[3], row[4], row[5], row[6]
    title, body, tags = row[7], row[8], row[9]

    # 读取原图并转 Base64
    image_file = Path(__file__).resolve().parent / image_rel
    if not image_file.exists():
        raise HTTPException(status_code=400, detail="原图文件不存在，无法调优")
    content = image_file.read_bytes()
    detected = detect_image_type(content)
    mime_type = detected[0] if detected else "image/jpeg"
    image_data_url = f"data:{mime_type};base64,{base64.b64encode(content).decode('utf-8')}"

    prompt = (
        "你是一位资深的小红书文案博主。下面是之前基于某张图片生成的文案：\n"
        f"标题：{title}\n正文：{body}\n标签：{tags}\n\n"
        f"请根据用户的修改意见重新生成小红书文案。\n修改意见：{instruction}\n\n"
        "要求：\n"
        "1. 标题20字以内；正文种草口吻、分段清晰；标签3到5个。\n"
        "2. 必须保留并围绕原图片内容，同时严格满足修改意见。\n"
        f"3. 需要生成 {data.versions} 个版本，每个版本在满足修改意见的前提下风格有所不同。\n"
        "4. 请严格按以下 JSON 格式返回（不要返回多余废话）：\n"
        '{"versions": [{"title": "标题", "body": "正文", "tags": ["#标签1", "#标签2"]}]}'
    )

    payload = {
        "model": "qwen-vl-plus",
        "input": {
            "messages": [
                {"role": "user", "content": [{"image": image_data_url}, {"text": prompt}]}
            ]
        },
    }
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {ALIYUN_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="调用阿里云服务超时，请稍后重试")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"调用阿里云服务失败: {e}")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"阿里云 API 调用失败: {response.text}")

    result = response.json()
    ai_text = result["output"]["choices"][0]["message"]["content"][0]["text"]
    cleaned_text = ai_text.replace("```json", "").replace("```", "").strip()
    start = cleaned_text.find("{")
    end = cleaned_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise HTTPException(status_code=502, detail="模型返回内容无法解析，请重试")
    result_data = json.loads(cleaned_text[start:end + 1])

    raw_versions = result_data.get("versions")
    if not isinstance(raw_versions, list) or len(raw_versions) == 0:
        raw_versions = [result_data]

    versions = []
    for i, v in enumerate(raw_versions[:data.versions]):
        v_title = (v.get("title") or f"版本{i + 1}").strip()
        v_body = (v.get("body") or "").strip()
        v_tags = v.get("tags") or []
        tags_str = ",".join(v_tags)
        cursor.execute(
            """INSERT INTO generation_records
               (user_id, parent_id, image_name, image_path, product_name, target_audience,
                tone_style, instruction, title, body, tags)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                int(user["sub"]),
                data.record_id,
                image_name,
                image_rel,
                product_name,
                target_audience,
                tone_style,
                instruction,
                v_title,
                v_body,
                tags_str,
            ),
        )
        versions.append({
            "id": cursor.lastrowid,
            "title": v_title,
            "body": v_body,
            "tags": v_tags,
        })
    conn.commit()
    return {"status": "success", "versions": versions}


def get_current_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return user


@app.get("/api/admin/stats")
def admin_stats(
    user: dict = Depends(get_current_admin),
    conn: pymysql.connections.Connection = Depends(get_db),
):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM generation_records")
    total_records = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM generation_records WHERE DATE(created_at) = CURDATE()"
    )
    today_records = cursor.fetchone()[0]
    cursor.execute(
        """SELECT DATE(created_at) AS d, COUNT(*) AS cnt
           FROM generation_records
           WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
           GROUP BY DATE(created_at)
           ORDER BY d"""
    )
    daily = [
        {"date": r[0].strftime("%m-%d") if r[0] else "未知", "count": r[1]}
        for r in cursor.fetchall()
    ]
    return {
        "status": "success",
        "stats": {
            "total_users": total_users,
            "total_records": total_records,
            "today_records": today_records,
            "daily": daily,
        },
    }


@app.get("/api/admin/users")
def admin_users(
    user: dict = Depends(get_current_admin),
    conn: pymysql.connections.Connection = Depends(get_db),
):
    cursor = conn.cursor()
    cursor.execute(
        """SELECT u.id, u.username, u.role, u.created_at, COUNT(r.id) AS generation_count
           FROM users u
           LEFT JOIN generation_records r ON r.user_id = u.id
           GROUP BY u.id, u.username, u.role, u.created_at
           ORDER BY u.id"""
    )
    users = []
    for r in cursor.fetchall():
        users.append({
            "id": r[0],
            "username": r[1],
            "role": r[2],
            "created_at": r[3].strftime("%Y-%m-%d %H:%M:%S") if r[3] else None,
            "generation_count": r[4],
        })
    return {"status": "success", "users": users}


@app.get("/api/admin/records")
def admin_records(
    user: dict = Depends(get_current_admin),
    conn: pymysql.connections.Connection = Depends(get_db),
):
    cursor = conn.cursor()
    cursor.execute(
        """SELECT r.id, u.username, r.image_name, r.image_path, r.title, r.tags, r.created_at
           FROM generation_records r
           LEFT JOIN users u ON r.user_id = u.id
           ORDER BY r.id DESC
           LIMIT 200"""
    )
    records = []
    for r in cursor.fetchall():
        records.append({
            "id": r[0],
            "username": r[1] or "未知用户",
            "image_name": r[2],
            "image_path": r[3],
            "title": r[4],
            "tags": r[5].split(",") if r[5] else [],
            "created_at": r[6].strftime("%Y-%m-%d %H:%M:%S") if r[6] else None,
        })
    return {"status": "success", "records": records}


@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    product_name: str = Form(""),
    target_audience: str = Form(""),
    tone_style: str = Form(""),
    user: dict = Depends(get_current_user),
):
    try:
        content = await file.read()

        if not content:
            return {"status": "error", "message": "上传的图片为空"}

        if len(content) > MAX_FILE_SIZE:
            return {"status": "error", "message": f"图片大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）"}

        detected = detect_image_type(content)
        if detected is None:
            return {"status": "error", "message": "不支持的图片格式，仅支持 JPEG/PNG/GIF/WebP/BMP"}
        mime_type, ext = detected

        # 保存原图到 uploads 目录，文件名带时间戳避免覆盖
        saved_name = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        saved_path = UPLOAD_DIR / saved_name
        with open(saved_path, "wb") as f:
            f.write(content)
        saved_rel = f"uploads/{saved_name}"

        # 图片转 Base64
        base64_img = base64.b64encode(content).decode('utf-8')
        image_data_url = f"data:{mime_type};base64,{base64_img}"

        # 调用阿里云百炼 API
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {ALIYUN_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = """你是一个资深的小红书文案博主。请根据我提供的图片，生成一篇小红书种草文案。
要求：
1. 标题：20字以内，引人注目，符合小红书爆款风格。
2. 正文：用种草口吻，分段清晰，自然流畅。
3. 话题标签：3到5个相关的 #话题标签。
请严格按以下 JSON 格式返回（不要返回多余的废话）：
{"title": "这里写标题", "body": "这里写正文", "tags": ["#标签1", "#标签2", "#标签3"]}"""

        # 用户可选输入：组装进提示词，影响生成结果
        optional_parts = []
        if product_name.strip():
            optional_parts.append(f"产品名称：{product_name.strip()}")
        if target_audience.strip():
            optional_parts.append(f"目标人群：{target_audience.strip()}")
        if tone_style.strip():
            optional_parts.append(f"语气风格：{tone_style.strip()}")
        if optional_parts:
            prompt += "\n\n补充信息（生成文案时必须围绕这些信息展开，并在文案中自然体现）：\n" + "\n".join(
                f"- {part}" for part in optional_parts
            )

        payload = {
            "model": "qwen-vl-plus",
            "input": {
                "messages": [
                    {"role": "user", "content": [{"image": image_data_url}, {"text": prompt}]}
                ]
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "调用阿里云服务超时，请稍后重试"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"调用阿里云服务失败: {e}"}
        
        if response.status_code == 200:
            result = response.json()
            ai_text = result["output"]["choices"][0]["message"]["content"][0]["text"]
            cleaned_text = ai_text.replace("```json", "").replace("```", "").strip()
            # 容错解析：只取第一个 { 到最后一个 } 之间的内容
            start = cleaned_text.find("{")
            end = cleaned_text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return {"status": "error", "message": "模型返回内容无法解析，请重试"}
            result_data = json.loads(cleaned_text[start:end + 1])
            
            title = result_data.get("title", "生成标题失败")
            body = result_data.get("body", "生成正文失败")
            tags = ",".join(result_data.get("tags", []))

            # 🟢 把数据写入 MySQL 数据库（失败也会明确告诉前端）
            db_saved = False
            db_error = None
            record_id = None
            conn = None
            try:
                conn = pymysql.connect(**DB_CONFIG)
                cursor = conn.cursor()
                sql = "INSERT INTO generation_records (user_id, image_name, image_path, product_name, target_audience, tone_style, title, body, tags) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (
                    int(user["sub"]),
                    file.filename,
                    saved_rel,
                    product_name.strip() or None,
                    target_audience.strip() or None,
                    tone_style.strip() or None,
                    title,
                    body,
                    tags,
                ))
                conn.commit()
                record_id = cursor.lastrowid
                db_saved = True
                print(f"✅ 文案已成功存入数据库！标题：{title}")
            except Exception as e:
                db_error = str(e)
                print(f"❌ 数据库存入失败: {e}")
            finally:
                if conn:
                    conn.close()

            result = {
                "status": "success",
                "id": record_id,
                "title": title,
                "body": body,
                "tags": result_data.get("tags", []),
                "db_saved": db_saved,
                "image_path": saved_rel,
            }
            if db_error:
                result["db_error"] = f"文案生成成功，但保存到数据库失败：{db_error}"
            return result
        else:
            return {"status": "error", "message": f"阿里云 API 调用失败: {response.text}"}
    except Exception as e:
        return {"status": "error", "message": f"服务端内部错误: {str(e)}"}


@app.post("/api/upload-by-url")
def upload_by_url(
    data: UrlUploadRequest,
    user: dict = Depends(get_current_user),
):
    image_url = data.url.strip()
    parsed = urlparse(image_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="请输入有效的图片 URL（http/https）")

    # 下载在线图片
    try:
        resp = requests.get(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=30,
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="下载图片超时，请稍后重试")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"下载图片失败: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"下载图片失败，HTTP {resp.status_code}")

    content = resp.content
    if not content:
        raise HTTPException(status_code=400, detail="图片内容为空")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"图片大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")

    detected = detect_image_type(content)
    if detected is None:
        raise HTTPException(status_code=400, detail="不支持的图片格式，仅支持 JPEG/PNG/GIF/WebP/BMP")
    mime_type, ext = detected

    # 保存图片
    saved_name = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    saved_path = UPLOAD_DIR / saved_name
    with open(saved_path, "wb") as f:
        f.write(content)
    saved_rel = f"uploads/{saved_name}"

    base64_img = base64.b64encode(content).decode('utf-8')
    image_data_url = f"data:{mime_type};base64,{base64_img}"

    prompt = """你是一个资深的小红书文案博主。请根据我提供的图片，生成一篇小红书种草文案。
要求：
1. 标题：20字以内，引人注目，符合小红书爆款风格。
2. 正文：用种草口吻，分段清晰，自然流畅。
3. 话题标签：3到5个相关的 #话题标签。
请严格按以下 JSON 格式返回（不要返回多余的废话）：
{"title": "这里写标题", "body": "这里写正文", "tags": ["#标签1", "#标签2", "#标签3"]}"""

    optional_parts = []
    if data.product_name.strip():
        optional_parts.append(f"产品名称：{data.product_name.strip()}")
    if data.target_audience.strip():
        optional_parts.append(f"目标人群：{data.target_audience.strip()}")
    if data.tone_style.strip():
        optional_parts.append(f"语气风格：{data.tone_style.strip()}")
    if optional_parts:
        prompt += "\n\n补充信息（生成文案时必须围绕这些信息展开，并在文案中自然体现）：\n" + "\n".join(
            f"- {part}" for part in optional_parts
        )

    payload = {
        "model": "qwen-vl-plus",
        "input": {
            "messages": [
                {"role": "user", "content": [{"image": image_data_url}, {"text": prompt}]}
            ]
        },
    }
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {ALIYUN_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="调用阿里云服务超时，请稍后重试")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"调用阿里云服务失败: {e}")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"阿里云 API 调用失败: {response.text}")

    result = response.json()
    ai_text = result["output"]["choices"][0]["message"]["content"][0]["text"]
    cleaned_text = ai_text.replace("```json", "").replace("```", "").strip()
    start = cleaned_text.find("{")
    end = cleaned_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise HTTPException(status_code=502, detail="模型返回内容无法解析，请重试")
    result_data = json.loads(cleaned_text[start:end + 1])

    title = result_data.get("title", "生成标题失败")
    body = result_data.get("body", "生成正文失败")
    tags = ",".join(result_data.get("tags", []))

    db_saved = False
    db_error = None
    record_id = None
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        sql = "INSERT INTO generation_records (user_id, image_name, image_path, product_name, target_audience, tone_style, title, body, tags) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (
            int(user["sub"]),
            image_url[:255],
            saved_rel,
            data.product_name.strip() or None,
            data.target_audience.strip() or None,
            data.tone_style.strip() or None,
            title,
            body,
            tags,
        ))
        conn.commit()
        record_id = cursor.lastrowid
        db_saved = True
        print(f"✅ 文案已成功存入数据库！标题：{title}")
    except Exception as e:
        db_error = str(e)
        print(f"❌ 数据库存入失败: {e}")
    finally:
        if conn:
            conn.close()

    result = {
        "status": "success",
        "id": record_id,
        "title": title,
        "body": body,
        "tags": result_data.get("tags", []),
        "db_saved": db_saved,
        "image_path": saved_rel,
        "image_url": image_url,
    }
    if db_error:
        result["db_error"] = f"文案生成成功，但保存到数据库失败：{db_error}"
    return result


def sse_event(event_type: str, **data) -> str:
    payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def build_stream_prompt(
    product_name: str,
    target_audience: str,
    tone_style: str,
    instruction: str = "",
    existing_copy: str = "",
) -> str:
    if instruction and existing_copy:
        prompt = (
            "你是一位资深的小红书文案博主。下面是之前基于某张图片生成的文案：\n"
            f"{existing_copy}\n\n"
            f"请根据用户的修改意见重新生成一篇小红书文案。\n修改意见：{instruction}\n\n"
        )
    else:
        prompt = "你是一个资深的小红书文案博主。请根据我提供的图片，生成一篇小红书种草文案。\n"
    prompt += (
        "要求：\n"
        "1. 标题：20字以内，引人注目，符合小红书爆款风格。\n"
        "2. 正文：用种草口吻，分段清晰，自然流畅。\n"
        "3. 话题标签：3到5个相关的 #话题标签。\n"
    )
    optional_parts = []
    if product_name.strip():
        optional_parts.append(f"产品名称：{product_name.strip()}")
    if target_audience.strip():
        optional_parts.append(f"目标人群：{target_audience.strip()}")
    if tone_style.strip():
        optional_parts.append(f"语气风格：{tone_style.strip()}")
    if optional_parts:
        prompt += "\n补充信息（生成文案时必须围绕这些信息展开，并在文案中自然体现）：\n" + "\n".join(
            f"- {part}" for part in optional_parts
        )
    prompt += (
        "\n请严格按以下 JSON 格式返回（不要返回多余废话）：\n"
        '{"title": "这里写标题", "body": "这里写正文", "tags": ["#标签1", "#标签2", "#标签3"]}'
    )
    return prompt


def resolve_stream_image(data: StreamRequest, user: dict):
    """解析图片来源（URL 或历史记录），返回图片上下文 dict"""
    if data.record_id is not None:
        conn = pymysql.connect(**DB_CONFIG)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT user_id, image_name, image_path, product_name, target_audience,
                          tone_style, title, body, tags
                   FROM generation_records WHERE id = %s""",
                (data.record_id,),
            )
            row = cursor.fetchone()
        finally:
            conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="记录不存在")
        if row[0] != int(user["sub"]):
            raise HTTPException(status_code=403, detail="只能基于自己的记录生成")
        image_name, image_rel = row[1], row[2]
        product_name = data.product_name.strip() or (row[3] or "")
        target_audience = data.target_audience.strip() or (row[4] or "")
        tone_style = data.tone_style.strip() or (row[5] or "")
        existing_copy = f"标题：{row[6]}\n正文：{row[7]}\n标签：{row[8]}"
        image_file = Path(__file__).resolve().parent / image_rel
        if not image_file.exists():
            raise HTTPException(status_code=400, detail="原图文件不存在")
        content = image_file.read_bytes()
    elif data.url.strip():
        image_url = data.url.strip()
        parsed = urlparse(image_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise HTTPException(status_code=400, detail="请输入有效的图片 URL（http/https）")
        try:
            resp = requests.get(
                image_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=30,
            )
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="下载图片超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"下载图片失败: {e}")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"下载图片失败，HTTP {resp.status_code}")
        content = resp.content
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"图片大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")
        image_name = image_url[:255]
        image_rel = None
        product_name = data.product_name
        target_audience = data.target_audience
        tone_style = data.tone_style
        existing_copy = ""
    else:
        raise HTTPException(status_code=400, detail="需要提供在线图片 URL 或历史记录 ID")

    detected = detect_image_type(content)
    if detected is None:
        raise HTTPException(status_code=400, detail="不支持的图片格式，仅支持 JPEG/PNG/GIF/WebP/BMP")
    mime_type, ext = detected

    # 保存图片（URL 来源需要落盘；记录来源复用原图路径）
    if image_rel is None:
        saved_name = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        saved_path = UPLOAD_DIR / saved_name
        with open(saved_path, "wb") as f:
            f.write(content)
        image_rel = f"uploads/{saved_name}"

    image_data_url = f"data:{mime_type};base64,{base64.b64encode(content).decode('utf-8')}"
    return {
        "image_data_url": image_data_url,
        "image_name": image_name,
        "image_rel": image_rel,
        "product_name": product_name,
        "target_audience": target_audience,
        "tone_style": tone_style,
        "existing_copy": existing_copy,
        "instruction": data.instruction.strip(),
        "parent_id": data.record_id,
    }


def qwen_stream_text(image_data_url: str, prompt: str):
    """调用 DashScope OpenAI 兼容流式接口，逐段产出文本"""
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {ALIYUN_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-vl-plus",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "stream": True,
    }
    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=60) as resp:
            if resp.status_code != 200:
                yield f"ERROR:{resp.text[:200]}"
                return
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                except Exception:
                    continue
                if delta:
                    yield delta
    except requests.exceptions.Timeout:
        yield "ERROR:调用阿里云服务超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        yield f"ERROR:调用阿里云服务失败: {e}"


def generate_stream_events(ctx: dict, user: dict):
    """SSE 事件生成器：逐字输出 → 解析保存 → done/error"""
    prompt = build_stream_prompt(
        ctx["product_name"],
        ctx["target_audience"],
        ctx["tone_style"],
        ctx["instruction"],
        ctx["existing_copy"],
    )
    accumulated = ""
    for piece in qwen_stream_text(ctx["image_data_url"], prompt):
        if piece.startswith("ERROR:"):
            yield sse_event("error", message=piece[6:])
            return
        accumulated += piece
        yield sse_event("delta", content=piece)

    cleaned = accumulated.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        yield sse_event("error", message="模型返回内容无法解析，请重试")
        return
    try:
        result_data = json.loads(cleaned[start:end + 1])
    except Exception:
        yield sse_event("error", message="模型返回内容无法解析，请重试")
        return

    title = result_data.get("title", "生成标题失败")
    body = result_data.get("body", "")
    tags_list = result_data.get("tags", [])
    tags = ",".join(tags_list)

    record_id = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        sql = "INSERT INTO generation_records (user_id, parent_id, image_name, image_path, product_name, target_audience, tone_style, instruction, title, body, tags) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (
            int(user["sub"]),
            ctx["parent_id"],
            ctx["image_name"],
            ctx["image_rel"],
            ctx["product_name"].strip() or None,
            ctx["target_audience"].strip() or None,
            ctx["tone_style"].strip() or None,
            ctx["instruction"] or None,
            title,
            body,
            tags,
        ))
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
    except Exception as e:
        print(f"❌ 数据库存入失败: {e}")

    yield sse_event("done", id=record_id, title=title, body=body, tags=tags_list, db_saved=record_id is not None)


@app.post("/api/stream")
def stream_generate(
    data: StreamRequest,
    user: dict = Depends(get_current_user),
):
    ctx = resolve_stream_image(data, user)
    return StreamingResponse(
        generate_stream_events(ctx, user),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/stream-upload")
async def stream_upload(
    file: UploadFile = File(...),
    product_name: str = Form(""),
    target_audience: str = Form(""),
    tone_style: str = Form(""),
    user: dict = Depends(get_current_user),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传的图片为空")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"图片大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")
    detected = detect_image_type(content)
    if detected is None:
        raise HTTPException(status_code=400, detail="不支持的图片格式，仅支持 JPEG/PNG/GIF/WebP/BMP")
    mime_type, ext = detected
    saved_name = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    saved_path = UPLOAD_DIR / saved_name
    with open(saved_path, "wb") as f:
        f.write(content)
    image_rel = f"uploads/{saved_name}"
    image_data_url = f"data:{mime_type};base64,{base64.b64encode(content).decode('utf-8')}"
    ctx = {
        "image_data_url": image_data_url,
        "image_name": file.filename,
        "image_rel": image_rel,
        "product_name": product_name,
        "target_audience": target_audience,
        "tone_style": tone_style,
        "existing_copy": "",
        "instruction": "",
        "parent_id": None,
    }
    return StreamingResponse(
        generate_stream_events(ctx, user),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
