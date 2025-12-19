# CLAUDE.md - Claude Code 项目指南

## 项目概述

LLM 多语言翻译基准测试工具，用于评估不同 LLM 模型在电商商品翻译场景下的性能。

**核心功能：**
- 一次 API 调用同时翻译到 7 种欧盟语言
- 使用 Claude Opus 4.5 评估翻译质量（准确性、流畅度、风格）
- 支持 14+ 个模型的并行基准测试

## 项目结构

```
src/llm_translate/
├── config.py      # 配置：API、模型列表、语言代码
├── translator.py  # 核心：multi_translate(), evaluate_translations()
└── cli.py         # 命令行入口

data/ecommerce.json    # 测试数据（titles + descriptions）
results/               # 测试结果输出目录
docs/PRICING.md        # 模型定价对比
docs/PROMPTS.md        # 翻译和评估提示词
```

## 常用命令

```bash
# 安装项目
pip install -e .

# 翻译测试
llm-translate translate "Hello world"
llm-translate translate "Floral Print Dress" -m gemini-2.5-flash-lite --eval

# 基准测试（所有模型）
llm-translate benchmark

# 测试指定模型
llm-translate benchmark -m gemini-2.5-flash-lite qwen3-max

# 跳过评估（快速测试）
llm-translate benchmark --no-eval

# 列出可用模型
llm-translate models
```

## 添加新模型

1. 编辑 `src/llm_translate/config.py`：
   - 添加模型 ID 到 `AVAILABLE_MODELS` 列表
   - 添加短名称到 `MODEL_SHORT_NAMES` 字典

2. 测试新模型：
```bash
llm-translate translate "Test text" -m "新模型ID" --eval
```

3. 如果测试通过，运行完整基准测试：
```bash
llm-translate benchmark -m "新模型ID"
```

## API 配置

项目使用 LiteLLM 代理，配置在 `.env` 文件：

```env
API_BASE_URL=https://litellm.test.bloomeverybody.work
API_KEY=your-api-key
```

支持的模型提供商：
- AWS Bedrock: `bedrock/us.xxx`
- 阿里云 Dashscope: `dashscope/xxx`
- Google Gemini: `gemini-xxx`

## 测试数据格式

`data/ecommerce.json` 格式：
```json
{
  "titles": ["商品标题1", "商品标题2", ...],
  "descriptions": ["商品描述1", "商品描述2", ...]
}
```

## 结果输出

基准测试结果保存在 `results/benchmark.json`：
```json
{
  "test_time": "2025-12-19 10:00:00",
  "models_count": 14,
  "results": [
    {
      "model": "gemini-2.5-flash-lite",
      "model_short": "Gemini 2.5 Flash Lite",
      "title_avg_score": 8.18,
      "desc_avg_score": 9.07,
      "overall_avg_score": 8.48,
      "avg_latency_ms": 2356,
      "success_rate": "15/15"
    }
  ]
}
```

## 常见任务

### 快速测试单个模型翻译质量
```bash
llm-translate translate "Ditsy Floral Ruffle Hem Dress" -m MODEL_ID --eval
```

### 对比两个模型
```bash
llm-translate benchmark -m model1 model2
```

### 更新定价文档
编辑 `docs/PRICING.md`，更新模型评分和价格信息。

### 添加新测试数据
编辑 `data/ecommerce.json`，添加新的 titles 或 descriptions。

## 代码修改指南

### 修改翻译提示词
编辑 `src/llm_translate/translator.py` 中的 `_build_translate_prompt()` 函数。

### 修改评估提示词
编辑 `src/llm_translate/translator.py` 中的 `_build_evaluate_prompt()` 函数。

### 修改评估模型
编辑 `src/llm_translate/config.py` 中的 `EVALUATOR_MODEL` 常量。

### 添加新的目标语言
编辑 `src/llm_translate/config.py`：
- 添加语言到 `EU_LANGUAGES` 字典
- 可选：添加到 `DEFAULT_TARGET_LANGS` 列表

## 注意事项

1. **API 限速**：不同模型有独立的限速，基准测试使用并行执行避免阻塞
2. **评估成本**：使用 Opus 4.5 评估会增加成本，测试时可用 `--no-eval` 跳过
3. **超时设置**：翻译超时 120s，评估超时 180s
4. **JSON 解析**：部分模型返回 markdown 代码块，已自动处理
