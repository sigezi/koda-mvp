import os
from typing import Tuple, Any
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
from .errors import ConnectionError

# 加载环境变量
load_dotenv()

# 获取环境变量
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")
USER_ID: str | None = os.getenv("USER_ID")

def initialize_clients() -> Tuple[OpenAI, Any]:
    """
    初始化 OpenAI 和 Supabase 客户端
    
    Returns:
        Tuple[OpenAI, Any]: 包含 OpenAI 和 Supabase 客户端的元组
        
    Raises:
        ConnectionError: 当 API 密钥或 URL 无效时抛出
    """
    try:
        # 验证环境变量
        if not OPENAI_API_KEY:
            raise ConnectionError("OpenAI API 密钥未设置")
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ConnectionError("Supabase 凭证未设置")
            
        # 初始化 OpenAI 客户端
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
        # 初始化 Supabase 客户端
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        return openai_client, supabase
        
    except Exception as e:
        raise ConnectionError(f"初始化客户端失败: {str(e)}") 