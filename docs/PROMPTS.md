# 多语言翻译提示词

## 1. 翻译提示词 (Translation Prompt)

一次 API 调用，同时翻译成多个语言，返回 JSON 格式。

```
You are a professional translator. Translate the following text from {source_lang} to multiple languages simultaneously.

Source text ({source_lang}):
{text}

Target languages: {lang_list}

Requirements:
1. Provide accurate, natural translations for each target language
2. Return ONLY a valid JSON object with language codes as keys
3. Do not include any explanation or additional text

Return format (JSON only):
{
  "de": "German translation here",
  "fr": "French translation here",
  ...
}

Translations:
```

### 变量说明

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{source_lang}` | 源语言 | `en` / `English` |
| `{text}` | 要翻译的文本 | `Hello, how are you?` |
| `{lang_list}` | 目标语言列表 | `de (German), fr (French), es (Spanish)` |

### 使用示例

```
You are a professional translator. Translate the following text from English to multiple languages simultaneously.

Source text (English):
Ditsy Floral Ruffle Layered Hem Dress - Elegant style with Round Neck, Lantern Sleeve, and Side seam pocket.

Target languages: de (German), fr (French), es (Spanish), it (Italian), pt (Portuguese), nl (Dutch), pl (Polish)

Requirements:
1. Provide accurate, natural translations for each target language
2. Return ONLY a valid JSON object with language codes as keys
3. Do not include any explanation or additional text

Return format (JSON only):
{
  "de": "German translation here",
  "fr": "French translation here",
  ...
}

Translations:
```

### 期望输出

```json
{
  "de": "Kleid mit Rüschensaum und zartem Blumenmuster – Eleganter Stil mit Rundhalsausschnitt, Laternenärmeln und Seitennähtentasche.",
  "fr": "Robe à volants et imprimé floral – Style élégant avec col rond, manches lanterne et poche latérale.",
  "es": "Vestido con dobladillo en capas de volantes y estampado floral – Estilo elegante con cuello redondo, manga farol y bolsillo lateral.",
  "it": "Vestito con orlo a balze e stampa floreale – Stile elegante con scollo rotondo, maniche a lanterna e tasca laterale.",
  "pt": "Vestido com bainha em camadas de babados e estampa floral – Estilo elegante com gola redonda, manga lanterna e bolso lateral.",
  "nl": "Jurk met ruches en bloemenprint – Elegante stijl met ronde hals, lantaarnmouwen en zijnaadzak.",
  "pl": "Sukienka z falbankami i drobnym kwiatowym wzorem – Elegancki styl z okrągłym dekoltem, rękawami typu latarenka i kieszenią w szwie bocznym."
}
```

---

## 2. 翻译质量评估提示词 (Evaluation Prompt)

使用强大的 LLM (如 Claude Opus 4.5) 对翻译结果进行质量评分。

```
You are an expert translation quality evaluator. Evaluate the following translations from {source_lang}.

Source text ({source_lang}):
{source_text}

Translations to evaluate:
{translations_text}

For each translation, score on these criteria (1-10 scale):
1. Accuracy: How accurately does it convey the original meaning?
2. Fluency: How natural and fluent is the translation?
3. Style: How well does it preserve the tone and style?

Return ONLY a valid JSON object in this exact format:
{
  "de": {"accuracy": 9, "fluency": 8, "style": 8, "overall": 8.3, "comments": "brief comment"},
  "fr": {"accuracy": 9, "fluency": 9, "style": 9, "overall": 9.0, "comments": "brief comment"},
  ...
}

Evaluation:
```

### 变量说明

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{source_lang}` | 源语言 | `English` |
| `{source_text}` | 原文 | `Hello, how are you?` |
| `{translations_text}` | 各语言翻译结果 | 见下方格式 |

### translations_text 格式

```
[de] German (Deutsch):
Hallo, wie geht es dir?

[fr] French (Français):
Bonjour, comment allez-vous ?

[es] Spanish (Español):
Hola, ¿cómo estás?
```

### 期望输出

```json
{
  "de": {"accuracy": 10, "fluency": 10, "style": 9, "overall": 9.7, "comments": "Natural German greeting"},
  "fr": {"accuracy": 10, "fluency": 10, "style": 10, "overall": 10.0, "comments": "Perfect formal French"},
  "es": {"accuracy": 10, "fluency": 10, "style": 9, "overall": 9.7, "comments": "Natural informal Spanish"}
}
```

---

## 3. 评分标准说明

| 维度 | 英文 | 评估内容 | 权重 |
|-----|------|---------|-----|
| **准确性** | Accuracy | 翻译是否准确传达原文含义 | 高 |
| **流畅度** | Fluency | 翻译是否自然流畅 | 中 |
| **风格** | Style | 翻译是否保持原文语气风格 | 中 |

### 评分解读

| 分数 | 等级 | 说明 |
|-----|------|------|
| 9-10 | 优秀 | 接近完美，可直接使用 |
| 8-8.9 | 良好 | 质量高，小瑕疵可接受 |
| 7-7.9 | 一般 | 基本可用，建议人工审核 |
| <7 | 较差 | 不建议直接使用 |

---

## 4. API 调用参数建议

```json
{
  "model": "gemini-2.5-flash-lite",
  "messages": [{"role": "user", "content": "{prompt}"}],
  "temperature": 0.3,
  "max_tokens": 4096
}
```

| 参数 | 推荐值 | 说明 |
|-----|-------|------|
| `temperature` | 0.3 | 较低温度保证翻译一致性 |
| `max_tokens` | 4096 | 多语言输出需要足够空间 |

---

## 5. 支持的欧盟语言代码

| 代码 | 语言 | 英文名 |
|-----|------|-------|
| de | 德语 | German |
| fr | 法语 | French |
| es | 西班牙语 | Spanish |
| it | 意大利语 | Italian |
| pt | 葡萄牙语 | Portuguese |
| nl | 荷兰语 | Dutch |
| pl | 波兰语 | Polish |
| sv | 瑞典语 | Swedish |
| da | 丹麦语 | Danish |
| fi | 芬兰语 | Finnish |
| el | 希腊语 | Greek |
| cs | 捷克语 | Czech |
| ro | 罗马尼亚语 | Romanian |
| hu | 匈牙利语 | Hungarian |

---

## 6. 电商翻译最佳模型推荐

| 场景 | 推荐模型 | 评分 | 万次成本 |
|-----|---------|------|---------|
| 大批量翻译 | Gemini 2.5 Flash Lite | 8.48 | $1.60 |
| 质量优先 | Gemini 3 Flash | 9.08 | $11.00 |
| 极致低成本 | Qwen-Plus | 7.87 | $1.20 |
