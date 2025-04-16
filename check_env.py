import os
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 必需的环境变量列表
REQUIRED_ENV_VARS: Dict[str, str] = {
    'OPENAI_API_KEY': 'OpenAI API密钥',
    'SUPABASE_URL': 'Supabase项目URL',
    'SUPABASE_KEY': 'Supabase API密钥',
    'USER_ID': '用户ID'
}

# 可选的环境变量列表
OPTIONAL_ENV_VARS: Dict[str, str] = {
    'FLOWISE_API_URL': 'FlowiseAI API URL',
    'FLOWISE_API_KEY': 'FlowiseAI API密钥'
}

def validate_env() -> None:
    """
    验证所有必需的环境变量是否已正确设置
    
    Raises:
        ValueError: 当任何必需的环境变量未设置时抛出
    """
    missing_vars: List[str] = []
    
    # 检查所有必需的环境变量
    for var_name, var_description in REQUIRED_ENV_VARS.items():
        if not os.getenv(var_name):
            missing_vars.append(f"{var_name} ({var_description})")
    
    # 如果有缺失的环境变量，抛出异常
    if missing_vars:
        error_message = "以下必需的环境变量未设置：\n"
        error_message += "\n".join(f"- {var}" for var in missing_vars)
        error_message += "\n\n请在.env文件中设置这些变量。"
        raise ValueError(error_message)
    
    # 验证 Supabase URL 格式
    supabase_url = os.getenv('SUPABASE_URL', '')
    if not supabase_url.startswith(('http://', 'https://')):
        raise ValueError("SUPABASE_URL 必须是有效的 HTTP/HTTPS URL")
    
    # 验证 OpenAI API 密钥格式
    openai_key = os.getenv('OPENAI_API_KEY', '')
    if not openai_key.startswith('sk-'):
        raise ValueError("OPENAI_API_KEY 格式不正确，应以 'sk-' 开头")
    
    # 验证可选的 FlowiseAI URL 格式（如果提供）
    flowise_url = os.getenv('FLOWISE_API_URL')
    if flowise_url and not flowise_url.startswith(('http://', 'https://')):
        raise ValueError("FLOWISE_API_URL 必须是有效的 HTTP/HTTPS URL") 