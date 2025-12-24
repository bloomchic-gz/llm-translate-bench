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
    console.print(Panel.fit(
        f"[bold]源文本 ({result.source_lang})[/bold]\n{result.source_text}",
        border_style="blue"
    ))
    console.print()

    if not result.success:
        console.print(f"[red]翻译失败: {result.error}[/red]")
        return

    table = Table(
        title=f"翻译结果 (模型: {result.model})",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("语言", style="bold", width=15)
    table.add_column("翻译结果", width=60)

    for lang_code in sorted(result.translations.keys()):
        lang_name = EU_LANGUAGES.get(lang_code, lang_code)
        table.add_row(lang_name, result.translations[lang_code])

    console.print(table)
    console.print()
    console.print(
        f"[dim]单次 API 调用 | 延迟: {result.latency_ms:.0f}ms | "
        f"Tokens: {result.total_tokens} (输入: {result.prompt_tokens}, 输出: {result.completion_tokens})[/dim]"
    )


def print_evaluation(eval_result, translation_model: str):
    """打印评估结果"""
    table = Table(
        title="翻译质量评分 (评估模型: Opus 4.5)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("语言", style="bold", width=17)
    table.add_column("准确性", justify="center", width=6)
    table.add_column("流畅度", justify="center", width=6)
    table.add_column("风格", justify="center", width=6)
    table.add_column("综合分", justify="center", width=6)
    table.add_column("评语", width=40)

    total_overall = 0
    count = 0

    def score_color(s):
        if s >= 9:
            return "green"
        elif s >= 7:
            return "yellow"
        return "red"

    for lang_code in sorted(eval_result.scores.keys()):
        score = eval_result.scores[lang_code]
        lang_name = EU_LANGUAGES.get(lang_code, lang_code)
        comments = score.comments[:40] + "..." if len(score.comments) > 40 else score.comments

        table.add_row(
            lang_name,
            f"[{score_color(score.accuracy)}]{score.accuracy}[/]",
            f"[{score_color(score.fluency)}]{score.fluency}[/]",
            f"[{score_color(score.style)}]{score.style}[/]",
            f"[bold {score_color(score.overall)}]{score.overall:.1f}[/]",
            comments
        )
        total_overall += score.overall
        count += 1

    console.print(table)

    if count > 0:
        avg = total_overall / count
        color = "green" if avg >= 8 else "yellow" if avg >= 6 else "red"
        console.print(f"\n[bold]平均综合分: [{color}]{avg:.2f}/10[/][/bold]")

    console.print(f"[dim]评估耗时: {eval_result.latency_ms:.0f}ms | Tokens: {eval_result.total_tokens}[/dim]")


def cmd_translate(args):
    """翻译命令"""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text
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
    if args.glossary:
        console.print(f"术语表: {args.glossary}")
    console.print()

    console.print("[cyan]正在翻译...[/cyan]")
    result = multi_translate(
        text=text,
        source_lang=args.source,
        target_langs=args.targets,
        model=args.model,
        glossary=args.glossary,
    )

    print_result(result)

    if args.eval and result.success:
        console.print()
        console.print("[cyan]正在使用 Opus 4.5 评估翻译质量...[/cyan]")
        eval_result = evaluate_translations(
            source_text=text,
            translations=result.translations,
            source_lang=args.source,
        )
        console.print()
        print_evaluation(eval_result, args.model)

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
    score: Optional[float]
    error: Optional[str] = None


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

    console.print(f"\n[bold blue]{'=' * 60}[/bold blue]")
    console.print("[bold blue]电商翻译全模型基准测试[/bold blue]")
    console.print(f"[bold blue]{'=' * 60}[/bold blue]")
    console.print(f"\n模型数量: {len(models)}")
    console.print(f"测试文本: {len(titles)} 标题 + {len(descriptions)} 描述")
    console.print(f"目标语言: {len(target_langs)} 个")
    console.print(f"并发度: {concurrency} (每模型)")
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
                    text=text,
                    source_lang="en",
                    target_langs=target_langs,
                    model=model,
                    glossary=glossary,
                )

                score = None
                if not args.no_eval and result.success:
                    eval_result = evaluate_translations(
                        source_text=text,
                        translations=result.translations,
                        source_lang="en",
                    )
                    if eval_result.scores:
                        score = sum(s.overall for s in eval_result.scores.values()) / len(eval_result.scores)

                model_results[idx] = SingleResult(
                    text_type=text_type,
                    text=text[:50] + "..." if len(text) > 50 else text,
                    success=result.success,
                    latency_ms=result.latency_ms,
                    score=score,
                )

                with lock:
                    completed_count[0] += 1
                    console.print(f"  [{model_short}] {completed_count[0]}/{len(all_texts)} 完成" +
                                  (f", 评分: {score:.1f}" if score else ""))

            except Exception as e:
                model_results[idx] = SingleResult(
                    text_type=text_type,
                    text=text[:50] + "...",
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

        return {
            "model": model,
            "model_short": model_short,
            "title_avg_score": sum(title_scores) / len(title_scores) if title_scores else None,
            "desc_avg_score": sum(desc_scores) / len(desc_scores) if desc_scores else None,
            "overall_avg_score": sum(all_scores) / len(all_scores) if all_scores else None,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "success_rate": f"{success_count}/{len(valid_results)}",
            "total_time_s": total_time,
        }

    console.print(f"\n[bold cyan]开始并行测试 {len(models)} 个模型[/bold cyan]\n")

    with ThreadPoolExecutor(max_workers=len(models)) as executor:
        futures = {executor.submit(test_model, m): m for m in models}
        for future in as_completed(futures):
            model = futures[future]
            try:
                result = future.result()
                results.append(result)
                score_str = f"评分 {result['overall_avg_score']:.2f}/10, " if result['overall_avg_score'] else ""
                console.print(
                    f"[green]✓ {result['model_short']} 完成: "
                    f"{score_str}"
                    f"耗时 {result['total_time_s']:.1f}s[/green]"
                )
            except Exception as e:
                console.print(f"[red]✗ {get_model_short_name(model)} 失败: {e}[/red]")

    # 打印结果表格
    results.sort(key=lambda x: x["overall_avg_score"] or 0, reverse=True)

    table = Table(
        title="\n电商翻译全模型测试结果",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("排名", justify="center", width=4)
    table.add_column("模型", style="bold", width=22)
    table.add_column("标题评分", justify="center", width=10)
    table.add_column("描述评分", justify="center", width=10)
    table.add_column("总评分", justify="center", width=10)
    table.add_column("平均延迟", justify="center", width=10)
    table.add_column("成功率", justify="center", width=8)

    for i, r in enumerate(results, 1):
        def score_fmt(s):
            if s is None:
                return "[dim]N/A[/dim]"
            color = "green" if s >= 9 else "yellow" if s >= 8 else "red"
            return f"[{color}]{s:.2f}[/]"

        rank = f"🏆{i}" if i == 1 else f"  {i}"
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
    output = {
        "test_time": test_time,
        "models_count": len(results),
        "results": results,
    }

    # 生成输出文件名（带时间戳）
    if args.output:
        output_file = Path(args.output)
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = Path(f"results/benchmark_{timestamp}.json")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    console.print(f"\n[green]结果已保存到: {output_file}[/green]")
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
    p_translate.add_argument("text", nargs="?", help="要翻译的文本")
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
