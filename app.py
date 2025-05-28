from flask import Flask, request, jsonify
import pandas as pd
import random
from datetime import datetime

app = Flask(__name__)

# === 加载数据集 ===
df = pd.read_excel("Augmented_Dataset_with_Relevance.xlsx")

# === topic列映射 ===
topic_to_column = {
    "politic": "Relevance_Politic",
    "sport": "Relevance_Sport",
    "entertainment": "Relevance_Entertainment",
    "digital": "Relevance_Digital"
}

# === 数字转topic映射 ===
code_to_topic = {
    1: "politic",
    2: "sport",
    3: "entertainment",
    4: "digital"
}

@app.route('/generate-recommendation', methods=['POST'])
def generate():
    data = request.get_json()
    preferred_code = data.get("preferred")
    non_preferred_code = data.get("non_preferred")

    preferred = code_to_topic.get(preferred_code)
    non_preferred = code_to_topic.get(non_preferred_code)

    if preferred not in topic_to_column or non_preferred not in topic_to_column:
        return jsonify({"error": "Invalid topic names"}), 400

    # Step 1: Serendipitous 推荐池（non-preferred主题 + 与preferred最相关）
    serendip_pool = df[df["Primary Topic"] == non_preferred]
    serendip_pool = serendip_pool.sort_values(by=topic_to_column[preferred], ascending=False)
    top_10_percent = serendip_pool.head(max(1, len(serendip_pool) // 10))
    if len(top_10_percent) < 2:
        return jsonify({"error": "Not enough serendipitous candidates"}), 500
    serendip_articles = top_10_percent.sample(n=2, random_state=random.randint(0, 9999))

    # Step 2: 偏好主题推荐池
    preferred_pool = df[df["Primary Topic"] == preferred]
    if len(preferred_pool) < 6:
        return jsonify({"error": "Not enough preferred candidates"}), 500
    preferred_articles = preferred_pool.sample(n=6, random_state=random.randint(0, 9999))

    # Step 3: 构造返回数据
    result = {}

    # === Seren 推荐 2篇 ===
    for i in range(2):
        result[f"Seren_Article{i+1}_Title"] = serendip_articles.iloc[i]["Title"]
        result[f"Seren_Article{i+1}_Summary"] = serendip_articles.iloc[i]["Content Summary"]
        result[f"Seren_Article{i+1}_Topic"] = serendip_articles.iloc[i]["Primary Topic"].capitalize()

    # === Preferred 推荐 6篇 ===
    for i in range(6):
        result[f"Prefer_Article{i+1}_Title"] = preferred_articles.iloc[i]["Title"]
        result[f"Prefer_Article{i+1}_Summary"] = preferred_articles.iloc[i]["Content Summary"]
        result[f"Prefer_Article{i+1}_Topic"] = preferred_articles.iloc[i]["Primary Topic"].capitalize()

    # === 日期与天气 ===
    result["Today"] = datetime.now().strftime("%B %d, %Y")
    result["Weather"] = "19°C · Munich"

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
