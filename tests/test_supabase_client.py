"""
测试 Supabase 客户端模块的功能

此模块包含对 Supabase 数据库操作相关功能的测试，包括：
- 宠物档案查询
- 日志记录操作
- 错误处理
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from utils.types import PetProfile, LogEntry, LogType
from utils.supabase_client import get_pet_by_id, get_supabase

# 模拟宠物数据
MOCK_PET_DATA: Dict[str, Any] = {
    "id": "pet_001",
    "user_id": "user_001",
    "name": "小白",
    "species": "cat",
    "breed": "英短",
    "age": 2.5,
    "weight": 4.2,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00",
    "avatar_url": "https://example.com/avatar.jpg",
    "description": "一只活泼可爱的英短猫咪"
}

@pytest.mark.asyncio
async def test_get_pet_by_id():
    """
    测试通过 ID 获取宠物档案功能
    
    验证：
    1. 能正确获取宠物信息
    2. 返回的数据结构符合 PetProfile 类型
    3. 异常处理正常工作
    """
    # 模拟 Supabase 响应
    mock_response = MagicMock()
    mock_response.data = [MOCK_PET_DATA]
    
    with patch("utils.supabase_client.get_supabase") as mock_supabase:
        # 设置模拟返回值
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # 测试正常情况
        pet = await get_pet_by_id("pet_001")
        assert pet is not None
        assert isinstance(pet, dict)
        assert pet["id"] == "pet_001"
        assert pet["name"] == "小白"
        assert pet["species"] == "cat"
        
        # 测试异常情况
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("数据库查询失败")
        with pytest.raises(Exception):
            await get_pet_by_id("pet_001")

@pytest.mark.asyncio
async def test_get_pet_by_id_not_found():
    """
    测试获取不存在的宠物档案
    
    验证：
    1. 当宠物 ID 不存在时返回 None
    2. 不会抛出异常
    """
    # 模拟空响应
    mock_response = MagicMock()
    mock_response.data = []
    
    with patch("utils.supabase_client.get_supabase") as mock_supabase:
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        pet = await get_pet_by_id("non_existent_pet")
        assert pet is None

@pytest.mark.asyncio
async def test_get_pet_by_id_invalid_data():
    """
    测试获取格式不正确的宠物数据
    
    验证：
    1. 当返回的数据格式不正确时抛出异常
    2. 异常信息包含具体的错误原因
    """
    # 模拟格式不正确的数据
    mock_response = MagicMock()
    mock_response.data = [{"id": "pet_001"}]  # 缺少必要字段
    
    with patch("utils.supabase_client.get_supabase") as mock_supabase:
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            await get_pet_by_id("pet_001")
        assert "数据格式不正确" in str(exc_info.value) 