"""项目配置"""

import os
from dotenv import load_dotenv

load_dotenv()

# API 配置
API_BASE_URL = os.getenv("API_BASE_URL", "https://litellm.test.bloomeverybody.work")
API_KEY = os.getenv("API_KEY", "")

# 欧盟主要语言
EU_LANGUAGES = {
    "de": "German (Deutsch)",
    "fr": "French (Français)",
    "es": "Spanish (Español)",
    "it": "Italian (Italiano)",
    "pt": "Portuguese (Português)",
    "nl": "Dutch (Nederlands)",
    "pl": "Polish (Polski)",
    "sv": "Swedish (Svenska)",
    "da": "Danish (Dansk)",
    "fi": "Finnish (Suomi)",
    "el": "Greek (Ελληνικά)",
    "cs": "Czech (Čeština)",
    "ro": "Romanian (Română)",
    "hu": "Hungarian (Magyar)",
}

# 默认目标语言
DEFAULT_TARGET_LANGS = ["de", "fr", "es", "it", "pt", "nl", "pl"]

# 可用模型列表
AVAILABLE_MODELS = [
    # Claude 系列
    "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0",
    # Qwen 系列
    "dashscope/qwen3-max",
    "dashscope/qwen-max",
    "dashscope/qwen-plus",
    "dashscope/qwen-turbo",
    "dashscope/qwen-flash",
    # Llama 系列
    "bedrock/us.meta.llama3-3-70b-instruct-v1:0",
    # Amazon Nova 系列
    "bedrock/us.amazon.nova-pro-v1:0",
    "bedrock/us.amazon.nova-lite-v1:0",
    # Gemini 系列
    "gemini-3-flash-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

# 评估模型
EVALUATOR_MODEL = "bedrock/us.anthropic.claude-opus-4-5-20251101-v1:0"

# 模型短名称映射
MODEL_SHORT_NAMES = {
    "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0": "Claude Sonnet 4.5",
    "bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0": "Claude Haiku 4.5",
    "dashscope/qwen3-max": "Qwen3-Max",
    "dashscope/qwen-max": "Qwen-Max",
    "dashscope/qwen-plus": "Qwen-Plus",
    "dashscope/qwen-turbo": "Qwen-Turbo",
    "dashscope/qwen-flash": "Qwen-Flash",
    "bedrock/us.meta.llama3-3-70b-instruct-v1:0": "Llama 3.3 70B",
    "bedrock/us.amazon.nova-pro-v1:0": "Nova Pro",
    "bedrock/us.amazon.nova-lite-v1:0": "Nova Lite",
    "gemini-3-flash-preview": "Gemini 3 Flash",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite",
}


def get_model_short_name(model: str) -> str:
    """获取模型短名称"""
    return MODEL_SHORT_NAMES.get(model, model.split("/")[-1][:20])
