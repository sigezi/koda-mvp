"""
环境配置模块

此模块负责加载和管理环境变量，提供全局配置常量。
所有敏感信息（如API密钥）都通过环境变量加载。
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# Supabase 配置
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

# OpenAI 配置
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = "gpt-4-turbo-preview"  # 默认使用 GPT-4 Turbo

# FlowiseAI 配置
FLOWISE_API_URL: Optional[str] = os.getenv("FLOWISE_API_URL")
FLOWISE_API_KEY: Optional[str] = os.getenv("FLOWISE_API_KEY")

# 用户配置
USER_ID: Optional[str] = os.getenv("USER_ID")

# 应用配置
APP_NAME: str = "Koda · AI 宠物伙伴"
APP_VERSION: str = "1.0.0"
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

def validate_config() -> None:
    """
    验证必要的环境变量是否已设置
    
    Raises:
        ValueError: 当必要的环境变量未设置时抛出
    """
    required_vars = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "USER_ID": USER_ID,
        "FLOWISE_API_URL": FLOWISE_API_URL,
        "FLOWISE_API_KEY": FLOWISE_API_KEY
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"缺少必要的环境变量: {', '.join(missing_vars)}\n"
            "请在 .env 文件中设置这些变量"
        ) 