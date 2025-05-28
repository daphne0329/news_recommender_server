from flask import Flask, request, jsonify
import pandas as pd
import random

app = Flask(__name__)

# === 加载增强后的数据集 ===
df = pd.read_excel("Augmented_Dataset_with_Relevance.xlsx")

# === 后端识别用的标准 Topic 列名 ===
topic_to_column = {
    "politic": "Relevance_Politic",
    "sport": "Relevance_Sport",
    "entertainment": "Relevance_Entertainment",
    "digital": "Relevance_Digital"
}

# === 来自 Qualtrics 的选项文本与真实 Topic 字段的映射 ===
input_mapping = {
    "Politics": "politic",
    "Sports": "sport",
    "Entertainment": "entertainment",
    "Technology": "digital"
}

# === Qualtrics Recode Value（数字） → 文本映射 ===
code_to_text = {
    "1": "Politics",
    "2": "Sports",
    "3": "Entertainment",
    "4": "Technology"
}

@app.route('/generate-recommendation', methods=['POST'])
def generate_recommendation():
    data = request.get_json()

    # 从 JSON 请求中获取 raw 文字或数字 code（转为字符串处理）
    raw_preferred = str(data.get("preferred"))
    raw_non_preferred = str(data.get("non_preferred"))

    # 如果是数字（Qualtrics Recode），转换为英文文本
    if raw_preferred in code_to_text:
        raw_preferred = code_to_text[raw_preferred]
    if raw_non_preferred in code_to_text:
        raw_non_preferred = code_to_text[raw_non_preferred]

    # 执行映射转换为后端用的字段名
    preferred = input_mapping.get(raw_preferred)
    non_preferred = input_mapping.get(raw_non_preferred)

    # 合法性校验
    if preferred not in topic_to_column or non_preferred not in topic_to_column:
        return jsonify({"error": "Invalid topic names"}), 400

    # === Step 1: 生成 serendipitous 推荐池 ===
    serendip_pool = df[df["Primary Topic"] == non_preferred]
    serendip_pool = serendip_pool.sort_values(
        by=topic_to_column[preferred], ascending=False
    )
    top_10_percent = serendip_pool.head(max(1, len(serendip_pool) // 10))
    if len(top_10_percent) < 2:
        return jsonify({"error": "Not enough serendipitous candidates"}), 500
    serendipitous = top_10_percent.sample(n=2, random_state=random.randint(0, 9999))

    # === Step 2: 抽取 4 篇偏好主题的推荐 ===
    preferred_pool = df[df["Primary Topic"] == preferred]
    if len(preferred_pool) < 4:
        return jsonify({"error": "Not enough preferred candidates"}), 500
    preferred_articles = preferred_pool.sample(n=4, random_state=random.randint(0, 9999))

    # === Step 3: 合并 + 打乱顺序 ===
    articles = pd.concat([serendipitous, preferred_articles]).sample(frac=1).reset_index(drop=True)

    # === Step 4: 构造返回 JSON ===
    result = {}
    for i in range(6):
        result[f"Article{i+1}_Title"] = articles.iloc[i]["Title"]
        result[f"Article{i+1}_Summary"] = articles.iloc[i]["Content Summary"]

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
