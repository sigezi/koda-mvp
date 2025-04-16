"""
环境变量检查脚本

此脚本用于验证所有必需的环境变量是否存在且格式正确。
在应用启动前运行此脚本可以及早发现配置问题。
"""

import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class EnvVar:
    """环境变量配置类"""
    name: str
    required: bool = True
    pattern: Optional[str] = None
    description: str = ""

# 定义所需的环境变量及其验证规则
REQUIRED_ENV_VARS: List[EnvVar] = [
    EnvVar(
        name="OPENAI_API_KEY",
        pattern=r"^sk-[A-Za-z0-9]{48}$",
        description="OpenAI API密钥，格式应为'sk-'开头的51个字符"
    ),
    EnvVar(
        name="SUPABASE_URL",
        pattern=r"^https?://[^\s/$.?#].[^\s]*$",
        description="Supabase项目URL，应为有效的HTTPS URL"
    ),
    EnvVar(
        name="SUPABASE_KEY",
        pattern=r"^ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$",
        description="Supabase项目密钥，应为有效的JWT格式"
    ),
    EnvVar(
        name="FLOWISE_API_URL",
        pattern=r"^https?://[^\s/$.?#].[^\s]*$",
        description="Flowise API URL，应为有效的HTTP(S) URL"
    ),
    EnvVar(
        name="FLOWISE_API_KEY",
        required=False,
        description="Flowise API密钥（可选）"
    ),
    EnvVar(
        name="USER_ID",
        pattern=r"^[A-Za-z0-9_-]+$",
        description="用户ID，仅允许字母、数字、下划线和连字符"
    ),
    EnvVar(
        name="DEBUG",
        required=False,
        pattern=r"^(true|false)$",
        description="调试模式开关，值应为'true'或'false'"
    ),
    EnvVar(
        name="LOG_LEVEL",
        required=False,
        pattern=r"^(debug|info|warning|error|critical)$",
        description="日志级别，应为标准日志级别之一"
    ),
    EnvVar(
        name="PORT",
        required=False,
        pattern=r"^\d+$",
        description="应用端口号，应为数字"
    ),
    EnvVar(
        name="ENVIRONMENT",
        required=False,
        pattern=r"^(development|staging|production)$",
        description="运行环境，应为'development'、'staging'或'production'"
    )
]

def check_env_vars() -> Dict[str, List[str]]:
    """
    检查环境变量是否符合要求

    Returns:
        Dict[str, List[str]]: 包含错误和警告信息的字典
    """
    errors: List[str] = []
    warnings: List[str] = []

    for env_var in REQUIRED_ENV_VARS:
        value = os.getenv(env_var.name)
        
        # 检查必需的环境变量是否存在
        if env_var.required and not value:
            errors.append(f"缺少必需的环境变量: {env_var.name}")
            continue
            
        # 如果变量存在且有模式要求，则验证其格式
        if value and env_var.pattern:
            if not re.match(env_var.pattern, value):
                if env_var.required:
                    errors.append(
                        f"环境变量 {env_var.name} 格式不正确。{env_var.description}"
                    )
                else:
                    warnings.append(
                        f"可选环境变量 {env_var.name} 格式不正确。{env_var.description}"
                    )

    return {
        "errors": errors,
        "warnings": warnings
    }

def main():
    """主函数：运行环境变量检查并打印结果"""
    print("正在检查环境变量...")
    results = check_env_vars()
    
    if results["errors"]:
        print("\n❌ 发现错误:")
        for error in results["errors"]:
            print(f"  - {error}")
            
    if results["warnings"]:
        print("\n⚠️ 发现警告:")
        for warning in results["warnings"]:
            print(f"  - {warning}")
            
    if not results["errors"] and not results["warnings"]:
        print("\n✅ 所有环境变量配置正确！")
    
    # 如果有错误，返回非零状态码
    return len(results["errors"]) > 0

if __name__ == "__main__":
    exit(main()) 