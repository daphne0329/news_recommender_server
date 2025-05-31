from flask import Flask, request, jsonify
import pandas as pd
import random
from datetime import datetime

app = Flask(__name__)

# === 加载数据集 ===
df = pd.read_excel("Augmented_Dataset_with_Relevance.xlsx")

# === Topic 编码与列名映射 ===
recode_to_topic = {
    1: "politic",
    2: "sport",
    3: "entertainment",
    4: "digital"
}

topic_to_column = {
    "politic": "Relevance_Politic",
    "sport": "Relevance_Sport",
    "entertainment": "Relevance_Entertainment",
    "digital": "Relevance_Digital"
}

@app.route('/generate-recommendation', methods=['POST'])
def generate_recommendation():
    data = request.get_json()

    try:
        preferred_code = int(data.get("preferred"))
        non_preferred_code = int(data.get("non_preferred"))
    except (ValueError, TypeError):
        return jsonify({"error": "Topic codes must be integers"}), 400

    preferred = recode_to_topic.get(preferred_code)
    non_preferred = recode_to_topic.get(non_preferred_code)

    if preferred not in topic_to_column or non_preferred not in topic_to_column:
        return jsonify({"error": "Invalid topic codes"}), 400

    # Step 1: Serendipitous 推荐
    serendip_pool = df[df["Primary Topic"] == non_preferred]
    serendip_pool = serendip_pool.sort_values(by=topic_to_column[preferred], ascending=False)
    top_10_percent = serendip_pool.head(max(1, len(serendip_pool) // 10))
    if len(top_10_percent) < 2:
        return jsonify({"error": "Not enough serendipitous candidates"}), 500
    serendipitous = top_10_percent.sample(n=2, random_state=random.randint(0, 9999))

    # Step 2: 偏好推荐（确保与serendipitous不重复）
    serendip_ids = serendipitous["ArticleID"].tolist()
    preferred_pool = df[(df["Primary Topic"] == preferred) & (~df["ArticleID"].isin(serendip_ids))]
    if len(preferred_pool) < 6:
        return jsonify({"error": "Not enough preferred candidates"}), 500
    preferred_articles = preferred_pool.sample(n=6, random_state=random.randint(0, 9999))

    # Step 3: 构造 JSON 返回
    result = {}

    for i in range(2):
        result[f"Seren_Article{i+1}_Title"] = serendipitous.iloc[i]["Title"]
        result[f"Seren_Article{i+1}_Summary"] = serendipitous.iloc[i]["Content Summary"]
        result[f"Seren_Article{i+1}_Topic"] = serendipitous.iloc[i]["Primary Topic"]

    for i in range(6):
        result[f"Prefer_Article{i+1}_Title"] = preferred_articles.iloc[i]["Title"]
        result[f"Prefer_Article{i+1}_Summary"] = preferred_articles.iloc[i]["Content Summary"]
        result[f"Prefer_Article{i+1}_Topic"] = preferred_articles.iloc[i]["Primary Topic"]

    # 加入当前日期
    result["Today"] = datetime.now().strftime("%B %d, %Y")

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
