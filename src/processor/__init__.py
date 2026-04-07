"""
AI 处理器模块
支持多模型：Kimi / DeepSeek
"""
from src.processor.ai_processor import (
    BaseAIProcessor,
    KimiProcessor,
    DeepSeekProcessor,
    AIProcessorFactory,
    get_ai_processor,
    AIContentProcessor,  # 本地 AI 处理（审核和备用）
)

__all__ = [
    'BaseAIProcessor',
    'KimiProcessor',
    'DeepSeekProcessor',
    'AIProcessorFactory',
    'get_ai_processor',
    'AIContentProcessor',
]
