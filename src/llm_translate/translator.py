"""
核心翻译模块 - 一次 API 调用，同时输出多个语言
"""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional

import httpx

from llm_translate.config import (
    API_BASE_URL,
    API_KEY,
    EU_LANGUAGES,
    EVALUATOR_MODEL,
)
from llm_translate.glossary import build_glossary_prompt


# 提示词模板缓存
_prompt_cache: Dict[str, str] = {}


def load_prompt_template(name: str, prompt_type: str) -> str:
    """
    加载提示词模板

    Args:
        name: 模板名称（如 'default'）或文件路径
        prompt_type: "translate" 或 "evaluate"

    Returns:
        模板内容字符串
    """
    cache_key = f"{prompt_type}_{name}"
    if cache_key in _prompt_cache:
        return _prompt_cache[cache_key]

    # 如果是文件路径，直接加载
    path = Path(name)
    if path.exists():
        template = path.read_text(encoding="utf-8")
        _prompt_cache[cache_key] = template
        return template

    # 否则从 prompts/ 目录加载
    prompts_dir = Path(__file__).parent.parent.parent / "prompts"
    template_file = prompts_dir / f"{prompt_type}_{name}.txt"

    if template_file.exists():
        template = template_file.read_text(encoding="utf-8")
        _prompt_cache[cache_key] = template
        return template

    raise FileNotFoundError(f"提示词模板不存在: {name} (尝试路径: {template_file})")


@dataclass
class MultiTranslateResult:
    """多语言翻译结果"""
    source_text: str
    source_lang: str
    translations: Dict[str, str]
    model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TranslationScore:
    """翻译评分"""
    lang_code: str
    accuracy: int
    fluency: int
    style: int
    overall: float
    comments: str


@dataclass
class EvaluationResult:
    """评估结果"""
    source_text: str
    model_evaluated: str
    evaluator_model: str
    scores: Dict[str, TranslationScore]
    latency_ms: float
    total_tokens: int


def _build_translate_prompt(
    text: str,
    source_lang: str,
    target_langs: List[str],
    glossary: Optional[str] = None,
    prompt_template: Optional[str] = None,
) -> str:
    """构建翻译提示词（业务一致格式）

    Args:
        text: 要翻译的文本
        source_lang: 源语言
        target_langs: 目标语言列表
        glossary: 术语表ID (fashion_hard, fashion_core, fashion_full, ecommerce, None)
        prompt_template: 提示词模板名称或路径，None 表示使用默认
    """
    # 术语表部分
    glossary_section = ""
    if glossary:
        glossary_section = f"""
## 术语表
{build_glossary_prompt(target_langs, glossary)}
"""

    # 构建输入 JSON
    langs_json = json.dumps(target_langs)
    input_json = f'{{"contents":["{text}"],"langs":{langs_json}}}'

    # 加载模板并填充变量
    template_name = prompt_template or "default"
    template = load_prompt_template(template_name, "translate")
    return template.format(input_json=input_json, glossary_section=glossary_section)


def _build_evaluate_prompt(
    source_text: str,
    source_lang: str,
    translations: Dict[str, str],
    prompt_template: Optional[str] = None,
) -> str:
    """构建评估提示词（大码女装电商专用）

    Args:
        source_text: 原文
        source_lang: 源语言
        translations: 翻译结果
        prompt_template: 提示词模板名称或路径，None 表示使用默认
    """
    # 构建输入 JSON
    input_data = {
        "contents": [source_text],
        "source_lang": source_lang,
        "translations": {lang: [text] for lang, text in translations.items()}
    }
    input_json = json.dumps(input_data, ensure_ascii=False)

    # 加载模板并填充变量
    template_name = prompt_template or "default"
    template = load_prompt_template(template_name, "evaluate")
    return template.format(input_json=input_json)


def _parse_json_response(content: str) -> dict:
    """解析可能包含 markdown 代码块的 JSON 响应"""
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content)


def _call_llm(
    prompt: str,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 120.0
) -> tuple[str, dict, float]:
    """调用 LLM API，返回 (内容, usage, 延迟ms)"""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    # gpt-5 系列不支持 temperature 参数，只能用默认值
    if not model.startswith("gpt-5"):
        payload["temperature"] = temperature
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    start_time = time.perf_counter()

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

    latency_ms = (time.perf_counter() - start_time) * 1000
    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})

    return content, usage, latency_ms


def multi_translate(
    text: str,
    source_lang: str = "en",
    target_langs: Optional[List[str]] = None,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    glossary: Optional[str] = None,
    translate_prompt: Optional[str] = None,
) -> MultiTranslateResult:
    """
    一次 API 调用翻译到多个语言

    Args:
        text: 要翻译的文本
        source_lang: 源语言代码
        target_langs: 目标语言代码列表
        model: 使用的模型
        temperature: 温度参数
        max_tokens: 最大 token 数
        glossary: 术语表ID (fashion_mini, fashion_full, ecommerce, None)
        translate_prompt: 翻译提示词模板名称或路径

    Returns:
        MultiTranslateResult: 翻译结果
    """
    if target_langs is None:
        target_langs = ["de", "fr", "es", "it", "pt", "nl", "pl"]

    prompt = _build_translate_prompt(
        text, source_lang, target_langs,
        glossary=glossary,
        prompt_template=translate_prompt,
    )
    start_time = time.perf_counter()

    try:
        content, usage, latency_ms = _call_llm(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw_translations = _parse_json_response(content)

        # 新格式: {"de": ["译文1"], "fr": ["译文1"]} -> {"de": "译文1", "fr": "译文1"}
        translations = {}
        for lang, trans_list in raw_translations.items():
            if isinstance(trans_list, list) and len(trans_list) > 0:
                translations[lang] = trans_list[0]
            elif isinstance(trans_list, str):
                translations[lang] = trans_list  # 兼容旧格式

        return MultiTranslateResult(
            source_text=text,
            source_lang=source_lang,
            translations=translations,
            model=model,
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            success=True,
        )

    except json.JSONDecodeError as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return MultiTranslateResult(
            source_text=text,
            source_lang=source_lang,
            translations={},
            model=model,
            latency_ms=latency_ms,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            success=False,
            error=f"JSON 解析失败: {e}",
        )

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return MultiTranslateResult(
            source_text=text,
            source_lang=source_lang,
            translations={},
            model=model,
            latency_ms=latency_ms,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            success=False,
            error=str(e),
        )


def evaluate_translations(
    source_text: str,
    translations: Dict[str, str],
    source_lang: str = "en",
    evaluator_model: str = EVALUATOR_MODEL,
    evaluate_prompt: Optional[str] = None,
) -> EvaluationResult:
    """
    使用 LLM 评估翻译质量

    Args:
        source_text: 原文
        translations: 翻译结果 {lang_code: text}
        source_lang: 源语言代码
        evaluator_model: 评估模型
        evaluate_prompt: 评估提示词模板名称或路径

    Returns:
        EvaluationResult: 评估结果
    """
    prompt = _build_evaluate_prompt(
        source_text, source_lang, translations,
        prompt_template=evaluate_prompt,
    )
    start_time = time.perf_counter()

    try:
        content, usage, latency_ms = _call_llm(
            prompt=prompt,
            model=evaluator_model,
            temperature=0.1,
            max_tokens=2048,
            timeout=180.0,
        )
        scores_data = _parse_json_response(content)

        # 新格式: {"de": [95], "fr": [90]} -> TranslationScore
        scores = {}
        for lang_code, score_value in scores_data.items():
            # 支持新格式（数组）和旧格式（字典）
            if isinstance(score_value, list):
                # 新格式：取第一个分数，转换为 0-10 分制用于 overall
                raw_score = score_value[0] if score_value else 0
                scores[lang_code] = TranslationScore(
                    lang_code=lang_code,
                    accuracy=0,
                    fluency=0,
                    style=0,
                    overall=raw_score / 10,  # 100分制转10分制
                    comments="",
                )
            else:
                # 旧格式兼容
                scores[lang_code] = TranslationScore(
                    lang_code=lang_code,
                    accuracy=score_value.get("accuracy", 0),
                    fluency=score_value.get("fluency", 0),
                    style=score_value.get("style", 0),
                    overall=score_value.get("overall", 0),
                    comments=score_value.get("comments", ""),
                )

        return EvaluationResult(
            source_text=source_text,
            model_evaluated="",
            evaluator_model=evaluator_model,
            scores=scores,
            latency_ms=latency_ms,
            total_tokens=usage.get("total_tokens", 0),
        )

    except Exception:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return EvaluationResult(
            source_text=source_text,
            model_evaluated="",
            evaluator_model=evaluator_model,
            scores={},
            latency_ms=latency_ms,
            total_tokens=0,
        )
