# LLM 多语言翻译基准测试

一次 API 调用同时翻译到多个语言，并使用 Claude Opus 4.5 评估翻译质量。

## 功能特性

- **多语言翻译**: 一次 API 调用，同时输出 7+ 种语言翻译
- **质量评估**: 使用 Claude Opus 4.5 评估准确性、流畅度、风格
- **基准测试**: 支持 21 个模型的并行测试
- **电商优化**: 针对商品标题、描述翻译优化

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
# 翻译文本
llm-translate translate "Hello, how are you?"

# 指定模型和目标语言
llm-translate translate "Hello" -m gemini-2.5-flash-lite -t de fr es

# 翻译并评估质量
llm-translate translate "Hello" --eval

# 运行基准测试
llm-translate benchmark

# 测试指定模型
llm-translate benchmark -m gemini-2.5-flash-lite qwen3-max

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
│       ├── __init__.py
│       ├── config.py      # 配置
│       ├── translator.py  # 核心翻译
│       └── cli.py         # 命令行
├── data/
│   └── ecommerce.json     # 测试数据
├── results/               # 测试结果
├── tests/
└── docs/
    ├── PRICING.md         # 模型定价
    └── PROMPTS.md         # 提示词
```

## 支持的模型

| 模型 | 评分 | 成本/万次 | 备注 |
|-----|------|----------|------|
| Gemini 2.5 Pro | 9.11 | $37 | 质量最高 |
| Gemini 3 Flash | 9.08 | $11 | 高质快速 |
| Gemini 2.5 Flash | 9.04 | $9 | |
| GPT-5 Mini | 8.80 | $40 | GPT最佳 |
| Claude Sonnet 4.5 | 8.78 | $58 | |
| GPT-5.1 | 8.71 | $32 | 快速高质 |
| Qwen3-Max | 8.61 | $9 | |
| GPT-4.1 | 8.61 | $32 | |
| Claude Haiku 4.5 | 8.60 | $15 | |
| **Gemini 2.5 Flash Lite** | **8.48** | **$1.60** | **性价比之王** |
| GPT-4.1-mini | 8.46 | $6 | GPT经济 |

> 完整 21 个模型定价见 [docs/PRICING.md](docs/PRICING.md)

## 目标语言

默认支持 7 种欧盟语言：

| 代码 | 语言 |
|-----|------|
| de | 德语 |
| fr | 法语 |
| es | 西班牙语 |
| it | 意大利语 |
| pt | 葡萄牙语 |
| nl | 荷兰语 |
| pl | 波兰语 |

## API 配置

项目使用 LiteLLM 代理，支持多种模型提供商：

```env
API_BASE_URL=https://your-litellm-proxy.com
API_KEY=your-api-key
```

## License

MIT
