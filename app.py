from flask import Flask, request, jsonify
import pandas as pd
import random

app = Flask(__name__)

# === 加载数据集 ===
df = pd.read_excel("Augmented_Dataset_with_Relevance.xlsx")

# === Topic 到相关性列的映射 ===
topic_to_column = {
    "politic": "Relevance_Politic",
    "sport": "Relevance_Sport",
    "entertainment": "Relevance_Entertainment",
    "digital": "Relevance_Digital"
}

@app.route('/generate-recommendation', methods=['POST'])
def generate_recommendation():
    data = request.get_json()
    preferred = data.get("preferred")
    non_preferred = data.get("non_preferred")

    if preferred not in topic_to_column or non_preferred not in topic_to_column:
        return jsonify({"error": "Invalid topic names"}), 400

    # === Step 1: 筛选 serendipitous 候选 ===
    serendip_pool = df[df["Primary Topic"] == non_preferred]
    serendip_pool = serendip_pool.sort_values(
        by=topic_to_column[preferred], ascending=False
    )
    top_10_percent = serendip_pool.head(max(1, len(serendip_pool) // 10))
    if len(top_10_percent) < 2:
        return jsonify({"error": "Not enough serendipitous candidates"}), 500
    serendipitous = top_10_percent.sample(n=2, random_state=random.randint(0, 9999))

    # === Step 2: 筛选 preferred 文章 ===
    preferred_pool = df[df["Primary Topic"] == preferred]
    if len(preferred_pool) < 4:
        return jsonify({"error": "Not enough preferred candidates"}), 500
    preferred_articles = preferred_pool.sample(n=4, random_state=random.randint(0, 9999))

    # === Step 3: 混洗，生成6篇文章 ===
    articles = pd.concat([serendipitous, preferred_articles]).sample(frac=1).reset_index(drop=True)

    # === Step 4: 返回 JSON 响应 ===
    result = {}
    for i in range(6):
        result[f"Article{i+1}_Title"] = articles.iloc[i]["Title"]
        result[f"Article{i+1}_Summary"] = articles.iloc[i]["Content Summary"]

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
