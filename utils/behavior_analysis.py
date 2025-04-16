"""
行为分析模块

此模块负责分析宠物行为数据并生成建议。
包括情绪分析、行为模式识别和建议生成功能。
"""

import os
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta

from .types import PetProfile, LogEntry, EmotionType
from .errors import FlowiseError

class BehaviorAnalyzer:
    """行为分析器"""
    
    def __init__(self):
        """初始化行为分析器"""
        self.api_url = os.getenv("FLOWISE_API_URL")
        self.api_key = os.getenv("FLOWISE_API_KEY")
        
        if not self.api_url or not self.api_key:
            raise FlowiseError("FlowiseAI配置未设置")
    
    async def generate_behavior_recommendation(
        self,
        logs: List[LogEntry],
        pet_profile: PetProfile
    ) -> List[Dict[str, Any]]:
        """
        生成行为建议
        
        Args:
            logs: 宠物日志列表
            pet_profile: 宠物档案
            
        Returns:
            List[Dict[str, Any]]: 行为建议列表
        """
        try:
            # 准备请求数据
            request_data = {
                "pet_profile": pet_profile,
                "logs": logs,
                "analysis_time": datetime.now().isoformat()
            }
            
            # 调用Flowise API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_url}/prediction/behavior_analysis",
                headers=headers,
                json=request_data
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 如果没有连接到Flowise，使用模拟数据
            if not result or "error" in result:
                return self._generate_mock_recommendations(logs, pet_profile)
            
            return result["recommendations"]
            
        except Exception as e:
            # 如果API调用失败，使用模拟数据
            return self._generate_mock_recommendations(logs, pet_profile)
    
    def _generate_mock_recommendations(
        self,
        logs: List[LogEntry],
        pet_profile: PetProfile
    ) -> List[Dict[str, Any]]:
        """
        生成模拟的行为建议
        
        Args:
            logs: 宠物日志列表
            pet_profile: 宠物档案
            
        Returns:
            List[Dict[str, Any]]: 模拟的行为建议列表
        """
        # 分析最近的情绪趋势
        recent_logs = [log for log in logs if log["log_type"] == "mood"]
        recent_emotions = [log["emotion_type"] for log in recent_logs if log["emotion_type"]]
        
        # 生成建议
        recommendations = []
        
        # 1. 基于情绪的建议
        if recent_emotions:
            main_emotion = max(set(recent_emotions), key=recent_emotions.count)
            if main_emotion == EmotionType.ANXIOUS:
                recommendations.append({
                    "type": "情绪安抚",
                    "content": f"建议多陪伴{pet_profile['name']}，增加互动时间，帮助缓解焦虑情绪。",
                    "priority": "高",
                    "category": "情绪管理"
                })
            elif main_emotion == EmotionType.SAD:
                recommendations.append({
                    "type": "情绪提升",
                    "content": f"可以尝试带{pet_profile['name']}去公园玩耍，或者准备一些新玩具来提升心情。",
                    "priority": "中",
                    "category": "情绪管理"
                })
        
        # 2. 基于活动频率的建议
        activity_logs = [log for log in logs if log["log_type"] == "activity"]
        if len(activity_logs) < 3:
            recommendations.append({
                "type": "活动建议",
                "content": f"建议增加{pet_profile['name']}的活动量，每天至少进行30分钟的运动。",
                "priority": "中",
                "category": "运动健康"
            })
        
        # 3. 基于饮食的建议
        food_logs = [log for log in logs if log["log_type"] == "food"]
        if food_logs:
            last_food_log = food_logs[-1]
            if "挑食" in last_food_log["content"]:
                recommendations.append({
                    "type": "饮食建议",
                    "content": f"可以尝试更换{pet_profile['name']}的食物种类，或者添加一些营养补充剂。",
                    "priority": "中",
                    "category": "饮食管理"
                })
        
        # 4. 通用建议
        recommendations.append({
            "type": "日常关怀",
            "content": f"记得定期给{pet_profile['name']}梳理毛发，保持清洁卫生。",
            "priority": "低",
            "category": "日常护理"
        })
        
        return recommendations 