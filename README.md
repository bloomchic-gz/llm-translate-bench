# LLM 多语言翻译基准测试

一次 API 调用同时翻译多条文本到多个语言，并使用 Claude Opus 4.5 评估翻译质量。

## 功能特性

- **多文本批量翻译**: 一次 API 调用，同时翻译多条文本到多个语言
- **质量评估**: 使用 Claude Opus 4.5 进行 100 分制评估
- **基准测试**: 支持 23 个模型的并行测试
- **电商优化**: 针对大码女装商品标题、描述翻译优化

## 安装

```bash
# 克隆项目
git clone https://github.com/bloomchic-gz/llm-translate-bench.git
cd llm-translate-bench

# 安装（可编辑模式）
pip install -e .

# 配置 API
cp .env.example .env
# 编辑 .env 填入 API_KEY
```

## 快速开始

```bash
# 单文本翻译
llm-translate translate "Hello, how are you?"

# 多文本批量翻译（一次 API 调用）
llm-translate translate "Floral Dress" "V Neck T-Shirt" "High Waist Jeans"

# 翻译并评估质量
llm-translate translate "Floral Dress" --eval

# 多文本翻译+评估
llm-translate translate "text1" "text2" "text3" --eval

# 指定模型和目标语言
llm-translate translate "Hello" -m gemini-3-flash-preview -t de fr es

# 运行基准测试
llm-translate benchmark

# 测试指定模型，设置并发
llm-translate benchmark -m gemini-3-flash-preview qwen3-max -c 5

# 列出可用模型
llm-translate models
```

## 项目结构

```
llm-translate-bench/
├── README.md
├── pyproject.toml
├── .env.example
├── src/
│   └── llm_translate/
│       ├── config.py      # 配置
│       ├── translator.py  # 核心翻译
│       ├── glossary.py    # 术语表
│       └── cli.py         # 命令行
├── prompts/                     # 提示词模板
│   ├── translate_default.txt    # 默认翻译提示词
│   ├── translate_english.txt    # 英文版翻译提示词
│   ├── evaluate_default.txt     # 默认评估提示词
│   └── evaluate_english.txt     # 英文版评估提示词
├── data/
│   ├── ecommerce.json           # 测试数据
│   └── product_titles_2000.txt  # 2000条商品标题
├── results/               # 汇总结果
│   └── details/           # 详细翻译和评估结果
└── docs/
    ├── BENCHMARK.md       # 基准测试报告
    └── PROMPTS.md         # 提示词文档
```

## 最新测试结果 (100词 x 4模型)

| 排名 | 模型 | 评分 | 延迟 | 成本/万次 |
|:---:|------|:----:|-----:|----------:|
| 🥇 | **Gemini 3 Flash** | **92.0** | 2174ms | $11 |
| 🥈 | Qwen3-Max | 90.5 | 5954ms | $9 |
| 🥉 | Gemini 2.5 Flash Lite | 90.1 | 1638ms | $1.60 |
| 4 | Claude Haiku 4.5 | 89.6 | 2420ms | $15 |

> 完整测试报告见 [docs/BENCHMARK.md](docs/BENCHMARK.md)

### 提示词对比 (中文 vs 英文)

| 模型 | 中文提示词 | 英文提示词 | 差异 |
|------|:----------:|:----------:|:----:|
| Gemini 3 Flash | 92.7 | 92.6 | -0.1 |
| Qwen3-Max | 91.8 | 91.4 | -0.4 |
| Gemini 2.5 Flash Lite | 90.8 | 91.5 | +0.7 |
| Claude Haiku 4.5 | 89.9 | 90.6 | +0.7 |

> 差异 <1 分，两种提示词效果相当

## CLI 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-m, --model` | 翻译模型 | `-m gemini-3-flash-preview` |
| `-t, --targets` | 目标语言 | `-t de fr es it` |
| `-tp, --translate-prompt` | 翻译提示词 | `-tp english` |
| `-ep, --evaluate-prompt` | 评估提示词 | `-ep english` |
| `-em, --evaluator-model` | 评估模型 | `-em gemini-2.5-flash-lite` |
| `-c, --concurrency` | 并发数 | `-c 5` |
| `--eval` | 启用评估 | `--eval` |
| `--no-eval` | 跳过评估 | `--no-eval` |

## 目标语言

默认支持 4 种欧盟语言：

| 代码 | 语言 |
|-----|------|
| de | 德语 |
| fr | 法语 |
| es | 西班牙语 |
| it | 意大利语 |

可扩展到 14 种欧盟语言（pt, nl, pl, sv, da, fi, el, cs, ro, hu）。

## API 配置

项目使用 LiteLLM 代理，支持多种模型提供商：

```env
API_BASE_URL=https://your-litellm-proxy.com
API_KEY=your-api-key
```

## License

MIT
