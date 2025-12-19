"""
LLM 多语言翻译基准测试工具

支持一次 API 调用同时翻译到多个语言，并使用 LLM 评估翻译质量。
"""

from llm_translate.translator import (
    multi_translate,
    evaluate_translations,
    MultiTranslateResult,
    TranslationScore,
    EvaluationResult,
)
from llm_translate.config import (
    EU_LANGUAGES,
    DEFAULT_TARGET_LANGS,
    AVAILABLE_MODELS,
)

__version__ = "1.0.0"
__all__ = [
    "multi_translate",
    "evaluate_translations",
    "MultiTranslateResult",
    "TranslationScore",
    "EvaluationResult",
    "EU_LANGUAGES",
    "DEFAULT_TARGET_LANGS",
    "AVAILABLE_MODELS",
]
