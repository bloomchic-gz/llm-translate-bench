"""
核心翻译模块 - 一次 API 调用，同时输出多个语言
"""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple

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
    source_texts: List[str]
    source_lang: str
    translations: Dict[str, List[str]]  # {lang: [text1, text2, ...]}
    model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def source_text(self) -> str:
        """兼容旧接口：返回第一个源文本"""
        return self.source_texts[0] if self.source_texts else ""

    def get_single_translations(self) -> Dict[str, str]:
        """兼容旧接口：返回单文本翻译结果"""
        return {lang: texts[0] if texts else "" for lang, texts in self.translations.items()}


@dataclass
class TranslationScore:
    """翻译评分"""
    lang_code: str
    accuracy: int
    fluency: int
    style: int
    overall: float  # 平均分
    comments: str
    individual_scores: Optional[List[float]] = None  # 各条文本的分数


@dataclass
class EvaluationResult:
    """评估结果"""
    source_texts: List[str]
    model_evaluated: str
    evaluator_model: str
    scores: Dict[str, TranslationScore]
    latency_ms: float
    total_tokens: int
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def source_text(self) -> str:
        """兼容旧接口"""
        return self.source_texts[0] if self.source_texts else ""


def _build_translate_prompt(
    texts: List[str],
    source_lang: str,
    target_langs: List[str],
    glossary: Optional[str] = None,
    prompt_template: Optional[str] = None,
) -> Tuple[str, str]:
    """构建翻译提示词（业务一致格式）

    Args:
        texts: 要翻译的文本列表
        source_lang: 源语言
        target_langs: 目标语言列表
        glossary: 术语表ID (fashion_hard, fashion_core, fashion_full, ecommerce, None)
        prompt_template: 提示词模板名称或路径，None 表示使用默认

    Returns:
        (system_prompt, user_prompt) 元组
    """
    # 术语表部分
    glossary_section = ""
    if glossary:
        glossary_section = f"""
## 术语表
{build_glossary_prompt(target_langs, glossary)}
"""

    # 构建输入 JSON
    input_data = {"contents": texts, "langs": target_langs}
    input_json = json.dumps(input_data, ensure_ascii=False)

    # 加载模板作为 system prompt
    template_name = prompt_template or "default"
    template = load_prompt_template(template_name, "translate")
    system_prompt = template.format(glossary_section=glossary_section)

    # input_json 作为 user prompt
    return system_prompt, input_json


def _build_evaluate_prompt(
    source_texts: List[str],
    source_lang: str,
    translations: Dict[str, List[str]],
    prompt_template: Optional[str] = None,
) -> Tuple[str, str]:
    """构建评估提示词（大码女装电商专用）

    Args:
        source_texts: 原文列表
        source_lang: 源语言
        translations: 翻译结果 {lang: [text1, text2, ...]}
        prompt_template: 提示词模板名称或路径，None 表示使用默认

    Returns:
        (system_prompt, user_prompt) 元组
    """
    # 构建输入 JSON
    input_data = {
        "contents": source_texts,
        "source_lang": source_lang,
        "translations": translations
    }
    input_json = json.dumps(input_data, ensure_ascii=False)

    # 加载模板作为 system prompt
    template_name = prompt_template or "default"
    system_prompt = load_prompt_template(template_name, "evaluate")

    # input_json 作为 user prompt
    return system_prompt, input_json


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
    user_prompt: str,
    model: str,
    system_prompt: str = "",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 120.0
) -> tuple[str, dict, float]:
    """调用 LLM API，返回 (内容, usage, 延迟ms)

    Args:
        user_prompt: 用户消息
        model: 模型名称
        system_prompt: 系统消息（可选）
        temperature: 温度参数
        max_tokens: 最大 token 数
        timeout: 超时时间
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model,
        "messages": messages,
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
    texts: List[str],
    source_lang: str = "en",
    target_langs: Optional[List[str]] = None,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    glossary: Optional[str] = None,
    translate_prompt: Optional[str] = None,
) -> MultiTranslateResult:
    """
    一次 API 调用翻译多个文本到多个语言

    Args:
        texts: 要翻译的文本列表
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
    # 兼容单文本输入
    if isinstance(texts, str):
        texts = [texts]

    if target_langs is None:
        target_langs = ["de", "fr", "es", "it", "pt", "nl", "pl"]

    system_prompt, user_prompt = _build_translate_prompt(
        texts, source_lang, target_langs,
        glossary=glossary,
        prompt_template=translate_prompt,
    )
    start_time = time.perf_counter()

    try:
        content, usage, latency_ms = _call_llm(
            user_prompt=user_prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw_translations = _parse_json_response(content)

        # 格式: {"de": ["译文1", "译文2"], "fr": ["译文1", "译文2"]}
        translations = {}
        for lang, trans_list in raw_translations.items():
            if isinstance(trans_list, list):
                translations[lang] = trans_list
            elif isinstance(trans_list, str):
                translations[lang] = [trans_list]  # 兼容旧格式

        return MultiTranslateResult(
            source_texts=texts,
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
            source_texts=texts,
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
            source_texts=texts,
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
    source_texts: List[str],
    translations: Dict[str, List[str]],
    source_lang: str = "en",
    evaluator_model: str = EVALUATOR_MODEL,
    evaluate_prompt: Optional[str] = None,
) -> EvaluationResult:
    """
    使用 LLM 评估翻译质量

    Args:
        source_texts: 原文列表
        translations: 翻译结果 {lang_code: [text1, text2, ...]}
        source_lang: 源语言代码
        evaluator_model: 评估模型
        evaluate_prompt: 评估提示词模板名称或路径

    Returns:
        EvaluationResult: 评估结果
    """
    # 兼容单文本输入
    if isinstance(source_texts, str):
        source_texts = [source_texts]
    if translations and isinstance(next(iter(translations.values())), str):
        translations = {lang: [text] for lang, text in translations.items()}

    system_prompt, user_prompt = _build_evaluate_prompt(
        source_texts, source_lang, translations,
        prompt_template=evaluate_prompt,
    )
    start_time = time.perf_counter()

    try:
        content, usage, latency_ms = _call_llm(
            user_prompt=user_prompt,
            model=evaluator_model,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=4096,  # 多文本需要更大空间
            timeout=300.0,    # 多文本需要更长时间
        )
        scores_data = _parse_json_response(content)

        # 格式: {"de": [95, 88, 92], "fr": [90, 85, 91]} -> TranslationScore
        scores = {}
        for lang_code, score_value in scores_data.items():
            if isinstance(score_value, list):
                # 计算平均分
                avg_score = sum(score_value) / len(score_value) if score_value else 0
                scores[lang_code] = TranslationScore(
                    lang_code=lang_code,
                    accuracy=0,
                    fluency=0,
                    style=0,
                    overall=avg_score,  # 平均分
                    comments="",
                    individual_scores=score_value,  # 各条分数
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
            source_texts=source_texts,
            model_evaluated="",
            evaluator_model=evaluator_model,
            scores=scores,
            latency_ms=latency_ms,
            total_tokens=usage.get("total_tokens", 0),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )

    except Exception:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return EvaluationResult(
            source_texts=source_texts,
            model_evaluated="",
            evaluator_model=evaluator_model,
            scores={},
            latency_ms=latency_ms,
            total_tokens=0,
            prompt_tokens=0,
            completion_tokens=0,
        )
