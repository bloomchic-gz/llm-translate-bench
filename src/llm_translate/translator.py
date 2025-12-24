"""
核心翻译模块 - 一次 API 调用，同时输出多个语言
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

import httpx

from llm_translate.config import (
    API_BASE_URL,
    API_KEY,
    EU_LANGUAGES,
    EVALUATOR_MODEL,
)
from llm_translate.glossary import build_glossary_prompt


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
) -> str:
    """构建翻译提示词（业务一致格式）

    Args:
        text: 要翻译的文本
        source_lang: 源语言
        target_langs: 目标语言列表
        glossary: 术语表ID (fashion_hard, fashion_core, fashion_full, ecommerce, None)
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

    return f"""你是大码女装（Plus Size Women's Fashion）电商翻译专家。

## 任务
将电商内容从英语翻译到指定的目标语言，包括：
- 商品相关：标题、描述、属性、标签等
- 运营相关：活动标题、营销文案等
- 文章相关：博客、穿搭指南、品牌故事等

## 输入格式
{{"contents":["text1","text2"],"langs":["de","fr","es","it"]}}

## 输出格式
只输出一行有效JSON，格式为：{{"de":["..."],"fr":["..."],"es":["..."],"it":["..."]}}
- 每个语言键对应一个数组
- 数组内元素数量与输入contents数量相同
- 禁止输出任何解释文字

## 示例
输入：{{"contents":["Floral Dress"],"langs":["de","fr","es","it"]}}
输出：{{"de":["Blumenkleid"],"fr":["Robe fleurie"],"es":["Vestido floral"],"it":["Vestito floreale"]}}

## 翻译规则
1. 保持原文的简洁风格，不要过度展开
2. 保留占位符 {{{{ xxx }}}} 原样不翻译，xxx 为任意变量名
3. 翻译结果必须是纯目标语言，禁止混入其他语言（占位符除外）
4. 服装专业术语必须准确翻译为目标语言的对应术语
{glossary_section}
## 输入
{input_json}

## 输出"""


def _build_evaluate_prompt(source_text: str, source_lang: str, translations: Dict[str, str]) -> str:
    """构建评估提示词（大码女装电商专用）"""
    # 构建输入 JSON
    input_data = {
        "contents": [source_text],
        "source_lang": source_lang,
        "translations": {lang: [text] for lang, text in translations.items()}
    }
    input_json = json.dumps(input_data, ensure_ascii=False)

    return f"""你是大码女装电商翻译质量评估专家。

## 任务
评估翻译结果的质量并打分。

## 输入格式
{{"contents":["原文1","原文2"],"source_lang":"en","translations":{{"de":["德语译文1","德语译文2"],"fr":["法语译文1","法语译文2"]}}}}

## 输出格式
只输出JSON对象，每个语言对应一个分数数组（与原文一一对应）：
{{"de":[95,88],"fr":[90,85]}}

## 评分标准 (1-100)
- 95-100: 完美翻译，准确流畅，术语专业
- 85-94: 优秀翻译，准确自然，极小瑕疵
- 70-84: 良好翻译，意思正确，表达略有不足
- 50-69: 合格翻译，有明显问题
- 30-49: 较差翻译，部分意思偏差
- 1-29: 严重错误，意思错误或混合语言

## 扣分项
- 混合语言（如 "Kleid (dress)"）：-30分
- 服装术语不准确：-15分
- 过度展开或漏译：-10分
- 语法错误：-10分

## 示例
输入：{{"contents":["Floral Dress","V Neck T-Shirt"],"source_lang":"en","translations":{{"de":["Blumenkleid","V-Ausschnitt T-Shirt"],"fr":["Robe fleurie","T-shirt col en V"]}}}}
输出：{{"de":[95,92],"fr":[93,90]}}

输入：{{"contents":["连衣裙"],"source_lang":"zh","translations":{{"en":["Dress (连衣裙)"]}}}}
输出：{{"en":[55]}}

## 评估输入
{input_json}

## 评估输出"""


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

    Returns:
        MultiTranslateResult: 翻译结果
    """
    if target_langs is None:
        target_langs = ["de", "fr", "es", "it", "pt", "nl", "pl"]

    prompt = _build_translate_prompt(
        text, source_lang, target_langs,
        glossary=glossary
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
) -> EvaluationResult:
    """
    使用 LLM 评估翻译质量

    Args:
        source_text: 原文
        translations: 翻译结果 {lang_code: text}
        source_lang: 源语言代码
        evaluator_model: 评估模型

    Returns:
        EvaluationResult: 评估结果
    """
    prompt = _build_evaluate_prompt(source_text, source_lang, translations)
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
