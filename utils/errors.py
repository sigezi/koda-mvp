"""
错误处理模块

此模块定义了应用程序中使用的自定义异常类。
每个异常类都包含详细的错误信息和处理建议。
"""

class KodaError(Exception):
    """Koda 应用程序的基础异常类"""
    def __init__(self, message: str, details: str = ""):
        self.message = message
        self.details = details
        super().__init__(f"{message}\n{details}" if details else message)

class ConnectionError(KodaError):
    """连接错误"""
    def __init__(self, message: str = "连接失败", details: str = ""):
        super().__init__(
            message,
            f"{details}\n请检查：\n1. 网络连接\n2. API 密钥和 URL\n3. 服务状态"
        )

class DatabaseError(KodaError):
    """数据库操作错误"""
    def __init__(self, message: str = "数据库操作失败", details: str = ""):
        super().__init__(
            message,
            f"{details}\n请检查：\n1. 数据库连接\n2. SQL 语句\n3. 数据完整性"
        )

class SupabaseConnectionError(KodaError):
    """Supabase 连接错误"""
    def __init__(self, message: str = "无法连接到 Supabase 数据库", details: str = ""):
        super().__init__(
            message,
            f"{details}\n请检查：\n1. 网络连接\n2. Supabase URL 和密钥\n3. 数据库状态"
        )

class SupabaseQueryError(KodaError):
    """Supabase 查询错误"""
    def __init__(self, message: str = "数据库查询失败", details: str = ""):
        super().__init__(
            message,
            f"{details}\n请检查：\n1. 查询语法\n2. 数据格式\n3. 权限设置"
        )

class OpenAIRequestError(KodaError):
    """OpenAI API 请求错误"""
    def __init__(self, message: str = "OpenAI API 请求失败", details: str = ""):
        super().__init__(
            message,
            f"{details}\n请检查：\n1. API 密钥\n2. 请求限制\n3. 网络连接"
        )

class FlowiseError(KodaError):
    """Flowise API 请求错误"""
    def __init__(self, message: str = "Flowise API 请求失败", details: str = ""):
        super().__init__(
            message,
            f"{details}\n请检查：\n1. API 密钥\n2. 请求限制\n3. 网络连接\n4. 模型配置"
        )

class ValidationError(KodaError):
    """数据验证错误"""
    def __init__(self, message: str = "数据验证失败", details: str = ""):
        super().__init__(
            message,
            f"{details}\n请检查：\n1. 必填字段\n2. 数据格式\n3. 数据范围"
        )

def handle_error(error: Exception) -> None:
    """
    统一错误处理函数
    
    Args:
        error: 需要处理的异常
        
    Note:
        此函数会根据异常类型提供相应的错误信息和处理建议
    """
    if isinstance(error, KodaError):
        print(f"❌ {error.message}")
        if error.details:
            print(f"💡 处理建议：\n{error.details}")
    else:
        print(f"❌ 未预期的错误：{str(error)}")
        print("💡 请检查日志获取更多信息") 