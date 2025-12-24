# 多语言翻译提示词

## 1. 翻译提示词 (Translation Prompt)

大码女装电商专用翻译提示词，一次 API 调用同时翻译成多个语言，返回 JSON 格式。

```
你是大码女装（Plus Size Women's Fashion）电商翻译专家。

## 任务
将电商内容从英语翻译到指定的目标语言，包括：
- 商品相关：标题、描述、属性、标签等
- 运营相关：活动标题、营销文案等
- 文章相关：博客、穿搭指南、品牌故事等

## 输入格式
{"contents":["text1","text2"],"langs":["de","fr","es","it"]}

## 输出格式
只输出一行有效JSON，格式为：{"de":["..."],"fr":["..."],"es":["..."],"it":["..."]}
- 每个语言键对应一个数组
- 数组内元素数量与输入contents数量相同
- 禁止输出任何解释文字

## 示例
输入：{"contents":["Floral Dress"],"langs":["de","fr","es","it"]}
输出：{"de":["Blumenkleid"],"fr":["Robe fleurie"],"es":["Vestido floral"],"it":["Vestito floreale"]}

## 翻译规则
1. 保持原文的简洁风格，不要过度展开
2. 保留占位符 {{ xxx }} 原样不翻译，xxx 为任意变量名
3. 保留换行符和 HTML 标签原样不变
4. 翻译结果必须是纯目标语言，禁止混入其他语言（占位符和HTML标签除外）
5. 服装专业术语必须准确翻译为目标语言的对应术语

## 输入
{input_json}

## 输出
```

### 变量说明

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{input_json}` | 输入 JSON | `{"contents":["Floral Dress"],"langs":["de","fr"]}` |

### 使用示例

**输入：**
```json
{"contents":["Floral Ruffle Hem Dress","V Neck T-Shirt"],"langs":["de","fr","es","it"]}
```

**输出：**
```json
{"de":["Blumenkleid mit Rüschensaum","V-Ausschnitt T-Shirt"],"fr":["Robe fleurie à ourlet volant","T-shirt col en V"],"es":["Vestido floral con dobladillo de volantes","Camiseta cuello en V"],"it":["Vestito floreale con orlo a balze","T-shirt scollo a V"]}
```

---

## 2. 翻译质量评估提示词 (Evaluation Prompt)

使用 Claude Opus 4.5 对翻译结果进行质量评分，100 分制。

```
你是大码女装电商翻译质量评估专家。

## 任务
评估翻译结果的质量并打分。

## 输入格式
{"contents":["原文1","原文2"],"source_lang":"en","translations":{"de":["德语译文1","德语译文2"],"fr":["法语译文1","法语译文2"]}}

## 输出格式
只输出JSON对象，每个语言对应一个分数数组（与原文一一对应）：
{"de":[95,88],"fr":[90,85]}

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
输入：{"contents":["Floral Dress","V Neck T-Shirt"],"source_lang":"en","translations":{"de":["Blumenkleid","V-Ausschnitt T-Shirt"],"fr":["Robe fleurie","T-shirt col en V"]}}
输出：{"de":[95,92],"fr":[93,90]}

输入：{"contents":["连衣裙"],"source_lang":"zh","translations":{"en":["Dress (连衣裙)"]}}
输出：{"en":[55]}

## 评估输入
{input_json}

## 评估输出
```

### 变量说明

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{input_json}` | 评估输入 JSON | `{"contents":["Floral Dress"],"source_lang":"en","translations":{"de":["Blumenkleid"]}}` |

### 期望输出

```json
{"de":[95],"fr":[93],"es":[91],"it":[90]}
```

---

## 3. 评分标准说明

### 100 分制评分档位

| 分数 | 等级 | 说明 |
|-----|------|------|
| 95-100 | 完美 | 准确流畅，术语专业，可直接使用 |
| 85-94 | 优秀 | 准确自然，极小瑕疵，建议使用 |
| 70-84 | 良好 | 意思正确，表达略有不足，可用 |
| 50-69 | 合格 | 有明显问题，建议人工审核 |
| 30-49 | 较差 | 部分意思偏差，需要修改 |
| 1-29 | 严重错误 | 意思错误或混合语言，不可用 |

### 扣分项详情

| 问题类型 | 扣分 | 示例 |
|---------|------|------|
| 混合语言 | -30 | `Kleid (dress)`, `裙子 dress` |
| 服装术语不准确 | -15 | Ruffle 译为"褶皱"而非"荷叶边" |
| 过度展开 | -10 | 标题翻译过长，添加不必要修饰 |
| 漏译关键词 | -10 | 漏掉 V Neck、Floral 等关键词 |
| 语法错误 | -10 | 目标语言语法不正确 |
| 风格不符 | -5 | 不符合电商标题简洁风格 |

---

## 4. API 调用参数建议

### 翻译调用

```json
{
  "model": "gemini-2.5-flash-lite",
  "messages": [{"role": "user", "content": "{prompt}"}],
  "temperature": 0.3,
  "max_tokens": 4096
}
```

### 评估调用

```json
{
  "model": "bedrock/us.anthropic.claude-opus-4-5-20251101-v1:0",
  "messages": [{"role": "user", "content": "{prompt}"}],
  "temperature": 0.1,
  "max_tokens": 2048
}
```

| 参数 | 翻译推荐值 | 评估推荐值 | 说明 |
|-----|-----------|-----------|------|
| `temperature` | 0.3 | 0.1 | 翻译需要一定创造性，评估需要稳定性 |
| `max_tokens` | 4096 | 2048 | 多语言输出需要足够空间 |

---

## 5. 默认目标语言

| 代码 | 语言 | 英文名 |
|-----|------|-------|
| de | 德语 | German |
| fr | 法语 | French |
| es | 西班牙语 | Spanish |
| it | 意大利语 | Italian |

### 扩展支持语言

| 代码 | 语言 | 英文名 |
|-----|------|-------|
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

## 6. 电商翻译模型推荐

基于 100 条商品标题测试结果（2024-12-24）：

| 排名 | 模型 | 评分 | 延迟 | 成功率 | 推荐场景 |
|-----|------|------|------|--------|---------|
| 1 | Qwen3-Max | 92.3 | 7.2s | 100% | 质量优先 |
| 2 | Gemini 2.5 Flash Lite | 90.7 | 2.0s | 100% | 性价比首选 |
| 3 | Claude Haiku 4.5 | 87.9 | 2.8s | 100% | 稳定可靠 |

### 推荐配置

| 场景 | 推荐模型 | 理由 |
|-----|---------|------|
| 大批量翻译 | Gemini 2.5 Flash Lite | 速度快、成本低、质量好 |
| 质量优先 | Qwen3-Max | 评分最高 |
| 稳定性优先 | Claude Haiku 4.5 | Bedrock 托管，稳定性好 |
