from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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


class LoginRequest(BaseModel):
    username: str
    password: str


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

    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, hash_password(password)),
    )
    conn.commit()
    user_id = cursor.lastrowid
    token = create_token(user_id, username, "user")
    return {
        "status": "success",
        "token": token,
        "user": {"id": user_id, "username": username, "role": "user"},
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
                  title, body, tags, created_at
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
            "title": r[6],
            "body": r[7],
            "tags": r[8].split(",") if r[8] else [],
            "created_at": r[9].strftime("%Y-%m-%d %H:%M:%S") if r[9] else None,
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
