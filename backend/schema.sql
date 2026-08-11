-- ============================================================
-- 小红书文案生成平台 - 数据库初始化脚本
-- 用法（在项目 backend 目录下执行）：
--   mysql -uroot -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS xiaohongshu_ai
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE xiaohongshu_ai;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 文案生成记录表
CREATE TABLE IF NOT EXISTS generation_records (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT DEFAULT NULL,
  parent_id INT DEFAULT NULL,
  image_name VARCHAR(255) DEFAULT NULL,
  image_path VARCHAR(255) DEFAULT NULL,
  product_name VARCHAR(255) DEFAULT NULL,
  target_audience VARCHAR(255) DEFAULT NULL,
  tone_style VARCHAR(255) DEFAULT NULL,
  instruction VARCHAR(500) DEFAULT NULL,
  title VARCHAR(100) DEFAULT NULL,
  body TEXT,
  tags VARCHAR(255) DEFAULT NULL,
  is_favorite TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
