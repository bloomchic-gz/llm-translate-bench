"""
命令行入口
"""

import argparse
import json
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from llm_translate.config import (
    API_KEY,
    EU_LANGUAGES,
    AVAILABLE_MODELS,
    DEFAULT_TARGET_LANGS,
    EVALUATOR_MODEL,
    get_model_short_name,
)
from llm_translate.translator import (
    multi_translate,
    evaluate_translations,
    MultiTranslateResult,
)

console = Console()


def print_result(result: MultiTranslateResult):
    """打印翻译结果"""
    # 显示源文本
    source_display = "\n".join(f"{i+1}. {t}" for i, t in enumerate(result.source_texts))
    console.print(Panel.fit(
        f"[bold]源文本 ({result.source_lang}) - {len(result.source_texts)} 条[/bold]\n{source_display}",
        border_style="blue"
    ))
    console.print()

    if not result.success:
        console.print(f"[red]翻译失败: {result.error}[/red]")
        return

    # 多文本：每个文本一个表格
    for idx, source_text in enumerate(result.source_texts):
        if len(result.source_texts) > 1:
            console.print(f"[bold cyan]#{idx+1}[/bold cyan] {source_text}")

        table = Table(
            title=f"翻译结果 (模型: {result.model})" if len(result.source_texts) == 1 else None,
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("语言", style="bold", width=15)
        table.add_column("翻译结果", width=60)

        for lang_code in sorted(result.translations.keys()):
            lang_name = EU_LANGUAGES.get(lang_code, lang_code)
            trans_list = result.translations[lang_code]
            trans_text = trans_list[idx] if idx < len(trans_list) else ""
            table.add_row(lang_name, trans_text)

        console.print(table)
        console.print()

    console.print(
        f"[dim]单次 API 调用 | {len(result.source_texts)} 条文本 | 延迟: {result.latency_ms:.0f}ms | "
        f"Tokens: {result.total_tokens} (输入: {result.prompt_tokens}, 输出: {result.completion_tokens})[/dim]"
    )


def print_evaluation(eval_result, translation_model: str, evaluator_model: str = None):
    """打印评估结果"""
    eval_model_name = get_model_short_name(evaluator_model) if evaluator_model else "Opus 4.5"
    table = Table(
        title=f"翻译质量评分 (评估模型: {eval_model_name})",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("语言", style="bold", width=20)
    table.add_column("分数", justify="center", width=10)

    total_overall = 0
    count = 0

    def score_color(s):
        """根据100分制分数返回颜色"""
        if s >= 85:
            return "green"
        elif s >= 70:
            return "yellow"
        return "red"

    for lang_code in sorted(eval_result.scores.keys()):
        score = eval_result.scores[lang_code]
        lang_name = EU_LANGUAGES.get(lang_code, lang_code)

        table.add_row(
            lang_name,
            f"[bold {score_color(score.overall)}]{score.overall:.0f}[/]",
        )
        total_overall += score.overall
        count += 1

    console.print(table)

    if count > 0:
        avg = total_overall / count
        color = "green" if avg >= 85 else "yellow" if avg >= 70 else "red"
        console.print(f"\n[bold]平均分: [{color}]{avg:.1f}/100[/][/bold]")

    console.print(f"[dim]评估耗时: {eval_result.latency_ms:.0f}ms | Tokens: {eval_result.total_tokens}[/dim]")


def print_evaluation_multi(eval_result, translation_model: str, evaluator_model: str = None):
    """打印多文本评估结果"""
    eval_model_name = get_model_short_name(evaluator_model) if evaluator_model else "Opus 4.5"
    num_texts = len(eval_result.source_texts)

    def score_color(s):
        if s >= 85:
            return "green"
        elif s >= 70:
            return "yellow"
        return "red"

    # 汇总表格
    table = Table(
        title=f"翻译质量评分 - {num_texts} 条文本 (评估模型: {eval_model_name})",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("语言", style="bold", width=20)
    table.add_column("平均分", justify="center", width=10)
    table.add_column("分数分布", width=40)

    total_overall = 0
    count = 0

    for lang_code in sorted(eval_result.scores.keys()):
        score = eval_result.scores[lang_code]
        lang_name = EU_LANGUAGES.get(lang_code, lang_code)

        # 分数分布
        if score.individual_scores:
            scores_str = ", ".join(str(int(s)) for s in score.individual_scores[:10])
            if len(score.individual_scores) > 10:
                scores_str += f"... (+{len(score.individual_scores)-10})"
        else:
            scores_str = "-"

        table.add_row(
            lang_name,
            f"[bold {score_color(score.overall)}]{score.overall:.1f}[/]",
            f"[dim]{scores_str}[/dim]",
        )
        total_overall += score.overall
        count += 1

    console.print(table)

    if count > 0:
        avg = total_overall / count
        color = "green" if avg >= 85 else "yellow" if avg >= 70 else "red"
        console.print(f"\n[bold]总平均分: [{color}]{avg:.1f}/100[/][/bold]")

    console.print(f"[dim]评估耗时: {eval_result.latency_ms:.0f}ms | Tokens: {eval_result.total_tokens} | 文本数: {num_texts}[/dim]")


def cmd_translate(args):
    """翻译命令"""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
        texts = [text]
    elif args.texts:
        texts = args.texts
    else:
        console.print("[red]错误: 请提供要翻译的文本[/red]")
        return 1

    if not API_KEY:
        console.print("[red]错误: 未设置 API_KEY，请在 .env 文件中配置[/red]")
        return 1

    console.print(Panel.fit("[bold blue]多语言翻译 - 一次 API 调用[/bold blue]", border_style="blue"))
    console.print(f"模型: {args.model}")
    console.print(f"源语言: {args.source}")
    console.print(f"目标语言: {', '.join(args.targets)} ({len(args.targets)}个)")
    console.print(f"文本数量: {len(texts)}")
    if args.glossary:
        console.print(f"术语表: {args.glossary}")
    console.print()

    console.print("[cyan]正在翻译...[/cyan]")
    result = multi_translate(
        texts=texts,
        source_lang=args.source,
        target_langs=args.targets,
        model=args.model,
        glossary=args.glossary,
        translate_prompt=args.translate_prompt,
    )

    print_result(result)

    if args.eval and result.success:
        console.print()
        eval_model_short = get_model_short_name(args.evaluator_model)
        console.print(f"[cyan]正在使用 {eval_model_short} 评估翻译质量 ({len(texts)} 条文本)...[/cyan]")
        eval_result = evaluate_translations(
            source_texts=texts,
            translations=result.translations,
            source_lang=args.source,
            evaluator_model=args.evaluator_model,
            evaluate_prompt=args.evaluate_prompt,
        )
        console.print()
        print_evaluation_multi(eval_result, args.model, args.evaluator_model)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        console.print(f"[green]结果已保存到: {args.output}[/green]")

    return 0 if result.success else 1


@dataclass
class SingleResult:
    """单个测试结果"""
    text_type: str
    text: str
    success: bool
    latency_ms: float
    score: Optional[float]  # 第一个评估模型的分数（兼容）
    error: Optional[str] = None
    # 详细结果
    translations: Optional[dict] = None  # 各语言翻译结果
    eval_scores: Optional[dict] = None   # 各语言评估详情（第一个评估模型）
    eval_latency_ms: Optional[float] = None  # 评估耗时（第一个评估模型）
    # 多评估模型支持
    multi_eval: Optional[dict] = None  # {evaluator_model: {score, eval_scores, eval_latency_ms, tokens}}
    # 翻译 Token 统计
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    # 评估 Token 统计（第一个评估模型，兼容）
    eval_prompt_tokens: Optional[int] = None
    eval_completion_tokens: Optional[int] = None
    eval_total_tokens: Optional[int] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "text_type": self.text_type,
            "text": self.text,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "score": self.score,
            "error": self.error,
            "translations": self.translations,
            "eval_scores": self.eval_scores,
            "eval_latency_ms": self.eval_latency_ms,
            "multi_eval": self.multi_eval,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "eval_prompt_tokens": self.eval_prompt_tokens,
            "eval_completion_tokens": self.eval_completion_tokens,
            "eval_total_tokens": self.eval_total_tokens,
        }


def cmd_benchmark(args):
    """基准测试命令"""
    # 加载测试数据
    data_file = Path(args.data)
    if not data_file.exists():
        console.print(f"[red]错误: 测试数据文件不存在: {data_file}[/red]")
        return 1

    with open(data_file, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    titles = test_data.get("titles", [])
    descriptions = test_data.get("descriptions", [])
    all_texts = [(t, "title") for t in titles] + [(d, "description") for d in descriptions]

    models = args.models or AVAILABLE_MODELS
    target_langs = args.targets

    glossary = getattr(args, 'glossary', None)
    concurrency = getattr(args, 'concurrency', 1)
    translate_prompt = getattr(args, 'translate_prompt', None)
    evaluate_prompt = getattr(args, 'evaluate_prompt', None)
    evaluator_models = getattr(args, 'evaluator_model', [EVALUATOR_MODEL])
    if isinstance(evaluator_models, str):
        evaluator_models = [evaluator_models]

    console.print(f"\n[bold blue]{'=' * 60}[/bold blue]")
    console.print("[bold blue]电商翻译全模型基准测试[/bold blue]")
    console.print(f"[bold blue]{'=' * 60}[/bold blue]")
    console.print(f"\n模型数量: {len(models)}")
    console.print(f"测试文本: {len(titles)} 标题 + {len(descriptions)} 描述")
    console.print(f"目标语言: {len(target_langs)} 个")
    console.print(f"并发度: {concurrency} (每模型)")
    if not args.no_eval:
        eval_names = [get_model_short_name(m) for m in evaluator_models]
        console.print(f"评估模型: {', '.join(eval_names)} ({len(evaluator_models)}个)")
    if glossary:
        console.print(f"术语表: {glossary}")

    results = []
    lock = threading.Lock()

    def test_model(model: str) -> dict:
        """测试单个模型"""
        model_short = get_model_short_name(model)
        model_results = [None] * len(all_texts)  # 预分配保持顺序
        start_time = time.time()
        completed_count = [0]  # 用列表以便在闭包中修改

        def process_single(idx: int, text: str, text_type: str) -> None:
            """处理单个文本"""
            try:
                result = multi_translate(
                    texts=text,
                    source_lang="en",
                    target_langs=target_langs,
                    model=model,
                    glossary=glossary,
                    translate_prompt=translate_prompt,
                )

                score = None
                eval_scores = None
                eval_latency_ms = None
                eval_prompt_tokens = None
                eval_completion_tokens = None
                eval_total_tokens = None
                multi_eval = {}

                if not args.no_eval and result.success:
                    translations_dict = result.get_single_translations()

                    # 对每个评估模型进行评估
                    for eval_idx, eval_model in enumerate(evaluator_models):
                        try:
                            eval_result = evaluate_translations(
                                source_texts=text,
                                translations=translations_dict,
                                source_lang="en",
                                evaluator_model=eval_model,
                                evaluate_prompt=evaluate_prompt,
                            )

                            if eval_result.scores:
                                eval_score = sum(s.overall for s in eval_result.scores.values()) / len(eval_result.scores)
                                eval_lang_scores = {
                                    lang: int(s.overall)
                                    for lang, s in eval_result.scores.items()
                                }

                                # 存储到多评估结果（包含token信息）
                                eval_model_short = get_model_short_name(eval_model)
                                multi_eval[eval_model_short] = {
                                    "score": eval_score,
                                    "eval_scores": eval_lang_scores,
                                    "eval_latency_ms": eval_result.latency_ms,
                                    "prompt_tokens": eval_result.prompt_tokens,
                                    "completion_tokens": eval_result.completion_tokens,
                                    "total_tokens": eval_result.total_tokens,
                                }

                                # 第一个评估模型的结果作为默认（兼容旧格式）
                                if eval_idx == 0:
                                    score = eval_score
                                    eval_scores = eval_lang_scores
                                    eval_latency_ms = eval_result.latency_ms
                                    eval_prompt_tokens = eval_result.prompt_tokens
                                    eval_completion_tokens = eval_result.completion_tokens
                                    eval_total_tokens = eval_result.total_tokens
                        except Exception as eval_err:
                            eval_model_short = get_model_short_name(eval_model)
                            multi_eval[eval_model_short] = {
                                "score": None,
                                "error": str(eval_err),
                            }

                model_results[idx] = SingleResult(
                    text_type=text_type,
                    text=text,  # 保存完整原文
                    success=result.success,
                    latency_ms=result.latency_ms,
                    score=score,
                    error=result.error if not result.success else None,
                    translations=result.get_single_translations() if result.success else None,
                    eval_scores=eval_scores,
                    eval_latency_ms=eval_latency_ms,
                    multi_eval=multi_eval if multi_eval else None,
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    total_tokens=result.total_tokens,
                    eval_prompt_tokens=eval_prompt_tokens,
                    eval_completion_tokens=eval_completion_tokens,
                    eval_total_tokens=eval_total_tokens,
                )

                with lock:
                    completed_count[0] += 1
                    console.print(f"  [{model_short}] {completed_count[0]}/{len(all_texts)} 完成" +
                                  (f", 评分: {score:.0f}" if score else ""))

            except Exception as e:
                model_results[idx] = SingleResult(
                    text_type=text_type,
                    text=text,  # 保存完整原文
                    success=False,
                    latency_ms=0,
                    score=None,
                    error=str(e),
                )
                with lock:
                    completed_count[0] += 1

        # 使用线程池并发处理
        if concurrency > 1:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []
                for i, (text, text_type) in enumerate(all_texts):
                    futures.append(executor.submit(process_single, i, text, text_type))
                # 等待所有任务完成
                for f in futures:
                    f.result()
        else:
            # 串行处理
            for i, (text, text_type) in enumerate(all_texts):
                process_single(i, text, text_type)

        total_time = time.time() - start_time
        # 过滤 None 值（并发时的安全检查）
        valid_results = [r for r in model_results if r is not None]
        success_count = sum(1 for r in valid_results if r.success)
        title_scores = [r.score for r in valid_results if r.text_type == "title" and r.score]
        desc_scores = [r.score for r in valid_results if r.text_type == "description" and r.score]
        all_scores = [r.score for r in valid_results if r.score]
        latencies = [r.latency_ms for r in valid_results if r.success]

        # 计算各评估模型的平均分
        multi_eval_scores = {}
        for eval_model_short in [get_model_short_name(m) for m in evaluator_models]:
            scores_for_eval = []
            for r in valid_results:
                if r.multi_eval and eval_model_short in r.multi_eval:
                    s = r.multi_eval[eval_model_short].get("score")
                    if s is not None:
                        scores_for_eval.append(s)
            if scores_for_eval:
                multi_eval_scores[eval_model_short] = sum(scores_for_eval) / len(scores_for_eval)

        return {
            "model": model,
            "model_short": model_short,
            "title_avg_score": sum(title_scores) / len(title_scores) if title_scores else None,
            "desc_avg_score": sum(desc_scores) / len(desc_scores) if desc_scores else None,
            "overall_avg_score": sum(all_scores) / len(all_scores) if all_scores else None,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "success_rate": f"{success_count}/{len(valid_results)}",
            "total_time_s": total_time,
            # 多评估模型分数
            "multi_eval_scores": multi_eval_scores,
            # 详细结果
            "details": [r.to_dict() for r in valid_results],
        }

    console.print(f"\n[bold cyan]开始并行测试 {len(models)} 个模型[/bold cyan]\n")

    with ThreadPoolExecutor(max_workers=len(models)) as executor:
        futures = {executor.submit(test_model, m): m for m in models}
        for future in as_completed(futures):
            model = futures[future]
            try:
                result = future.result()
                with lock:
                    results.append(result)
                score_str = f"评分 {result['overall_avg_score']:.1f}/100, " if result['overall_avg_score'] else ""
                console.print(
                    f"[green]✓ {result['model_short']} 完成: "
                    f"{score_str}"
                    f"耗时 {result['total_time_s']:.1f}s[/green]"
                )
            except Exception as e:
                console.print(f"[red]✗ {get_model_short_name(model)} 失败: {e}[/red]")

    # 打印结果表格
    results.sort(key=lambda x: x["overall_avg_score"] or 0, reverse=True)

    # 获取评估模型短名称列表
    eval_model_names = [get_model_short_name(m) for m in evaluator_models]
    multi_eval_mode = len(evaluator_models) > 1

    table = Table(
        title="\n电商翻译全模型测试结果",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("排名", justify="center", width=4)
    table.add_column("模型", style="bold", width=20)

    if multi_eval_mode:
        # 多评估模型：为每个评估模型添加一列
        for eval_name in eval_model_names:
            # 简化名称
            short_name = eval_name.replace("Gemini ", "G").replace("Claude ", "C").replace(" Flash", "F").replace(" Lite", "L").replace(" Pro", "P")
            table.add_column(short_name, justify="center", width=10)
    else:
        table.add_column("标题评分", justify="center", width=10)
        table.add_column("描述评分", justify="center", width=10)
        table.add_column("总评分", justify="center", width=10)

    table.add_column("平均延迟", justify="center", width=10)
    table.add_column("成功率", justify="center", width=8)

    def score_fmt(s):
        if s is None:
            return "[dim]N/A[/dim]"
        color = "green" if s >= 90 else "yellow" if s >= 80 else "red"
        return f"[{color}]{s:.1f}[/]"

    for i, r in enumerate(results, 1):
        rank = f"🏆{i}" if i == 1 else f"  {i}"

        if multi_eval_mode:
            # 多评估模型：显示每个评估模型的分数
            row = [rank, r["model_short"]]
            for eval_name in eval_model_names:
                score = r.get("multi_eval_scores", {}).get(eval_name)
                row.append(score_fmt(score))
            row.append(f"{r['avg_latency_ms']:.0f}ms")
            row.append(r["success_rate"])
            table.add_row(*row)
        else:
            table.add_row(
                rank,
                r["model_short"],
                score_fmt(r["title_avg_score"]),
                score_fmt(r["desc_avg_score"]),
                f"[bold]{score_fmt(r['overall_avg_score'])}[/bold]",
                f"{r['avg_latency_ms']:.0f}ms",
                r["success_rate"],
            )

    console.print(table)

    # 保存结果
    test_time = time.strftime("%Y-%m-%d %H:%M:%S")
    # 使用毫秒级时间戳避免文件名冲突
    timestamp = f"{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}"

    # 生成输出文件名
    if args.output:
        output_file = Path(args.output)
        details_file = output_file.parent / "details" / output_file.name
    else:
        output_file = Path(f"results/benchmark_{timestamp}.json")
        details_file = Path(f"results/details/benchmark_{timestamp}.json")

    # 汇总结果（不含详细数据）
    summary_results = []
    for r in results:
        summary = {k: v for k, v in r.items() if k != "details"}
        summary_results.append(summary)

    summary_output = {
        "test_time": test_time,
        "config": {
            "data_file": str(data_file),
            "models_count": len(results),
            "titles_count": len(titles),
            "descriptions_count": len(descriptions),
            "target_langs": target_langs,
            "glossary": glossary,
            "concurrency": concurrency,
            "eval_enabled": not args.no_eval,
            "evaluator_models": evaluator_models if not args.no_eval else None,
        },
        "results": summary_results,
    }

    # 详细结果（含翻译和评估明细）
    details_output = {
        "test_time": test_time,
        "config": summary_output["config"],
        "results": results,  # 包含 details
    }

    # 保存汇总结果
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary_output, f, ensure_ascii=False, indent=2)

    # 保存详细结果
    details_file.parent.mkdir(parents=True, exist_ok=True)
    with open(details_file, "w", encoding="utf-8") as f:
        json.dump(details_output, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]汇总结果: {output_file}[/green]")
    console.print(f"[green]详细结果: {details_file}[/green]")
    return 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="llm-translate",
        description="LLM 多语言翻译基准测试工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # translate 命令
    p_translate = subparsers.add_parser("translate", help="翻译文本")
    p_translate.add_argument("texts", nargs="*", help="要翻译的文本（支持多个）")
    p_translate.add_argument("-f", "--file", help="从文件读取文本")
    p_translate.add_argument(
        "-t", "--targets",
        nargs="+",
        default=DEFAULT_TARGET_LANGS,
        help="目标语言代码列表"
    )
    p_translate.add_argument("-s", "--source", default="en", help="源语言代码")
    p_translate.add_argument("-m", "--model", default="gemini-2.5-flash-lite", help="使用的模型")
    p_translate.add_argument("-g", "--glossary", help="术语表 (fashion_hard, fashion_core, fashion_full, ecommerce)")
    p_translate.add_argument("-o", "--output", help="保存结果到 JSON 文件")
    p_translate.add_argument("-e", "--eval", action="store_true", help="使用 Opus 4.5 评估质量")
    p_translate.add_argument("-tp", "--translate-prompt", help="翻译提示词模板 (名称或文件路径)")
    p_translate.add_argument("-ep", "--evaluate-prompt", help="评估提示词模板 (名称或文件路径)")
    p_translate.add_argument("-em", "--evaluator-model", default=EVALUATOR_MODEL, help="评估模型 (默认: Opus 4.5)")
    p_translate.set_defaults(func=cmd_translate)

    # benchmark 命令
    p_benchmark = subparsers.add_parser("benchmark", help="运行基准测试")
    p_benchmark.add_argument(
        "-d", "--data",
        default="data/ecommerce.json",
        help="测试数据文件"
    )
    p_benchmark.add_argument(
        "-m", "--models",
        nargs="+",
        help="要测试的模型列表（默认测试所有模型）"
    )
    p_benchmark.add_argument(
        "-t", "--targets",
        nargs="+",
        default=DEFAULT_TARGET_LANGS,
        help="目标语言代码列表"
    )
    p_benchmark.add_argument("--no-eval", action="store_true", help="跳过质量评估")
    p_benchmark.add_argument(
        "-c", "--concurrency",
        type=int,
        default=1,
        help="每个模型的并发度 (默认: 1，即串行)"
    )
    p_benchmark.add_argument(
        "-g", "--glossary",
        help="术语表 (fashion_hard, fashion_core, fashion_full, ecommerce)"
    )
    p_benchmark.add_argument(
        "-o", "--output",
        default=None,
        help="输出文件 (默认: results/benchmark_YYYYMMDD_HHMMSS.json)"
    )
    p_benchmark.add_argument("-tp", "--translate-prompt", help="翻译提示词模板 (名称或文件路径)")
    p_benchmark.add_argument("-ep", "--evaluate-prompt", help="评估提示词模板 (名称或文件路径)")
    p_benchmark.add_argument("-em", "--evaluator-model", nargs="+", default=[EVALUATOR_MODEL], help="评估模型，支持多个 (默认: Opus 4.5)")
    p_benchmark.set_defaults(func=cmd_benchmark)

    # models 命令
    p_models = subparsers.add_parser("models", help="列出可用模型")
    def cmd_models(args):
        for m in AVAILABLE_MODELS:
            console.print(f"  {m}")
        return 0
    p_models.set_defaults(func=cmd_models)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
