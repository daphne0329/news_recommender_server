from flask import Flask, request, jsonify
import pandas as pd
import random
from datetime import datetime

app = Flask(__name__)

# === 加载数据集 ===
df = pd.read_excel("Augmented_Dataset_with_Relevance.xlsx")

# === 映射设置 ===
topic_to_column = {
    "politic": "Relevance_Politic",
    "sport": "Relevance_Sport",
    "entertainment": "Relevance_Entertainment",
    "digital": "Relevance_Digital"
}

input_mapping = {
    "Politics": "politic",
    "Sports": "sport",
    "Entertainment": "entertainment",
    "Technology": "digital"
}

# === Serendipitous 文章提取函数 ===
def get_serendipitous(df, preferred, non_preferred):
    pool = df[df["Primary Topic"] == non_preferred]
    pool = pool.sort_values(by=topic_to_column[preferred], ascending=False)
    top_10_percent = pool.head(max(1, len(pool) // 10))
    return top_10_percent.sample(n=2, random_state=random.randint(0, 9999))

# === Preferred 文章提取函数 ===
def get_preferred(df, preferred, n=4):
    pool = df[df["Primary Topic"] == preferred]
    return pool.sample(n=n, random_state=random.randint(0, 9999))

@app.route('/generate-recommendation', methods=['POST'])
def generate_recommendation():
    data = request.get_json()
    raw_preferred = data.get("preferred")
    raw_non_preferred = data.get("non_preferred")

    preferred = input_mapping.get(raw_preferred)
    non_preferred = input_mapping.get(raw_non_preferred)

    if preferred not in topic_to_column or non_preferred not in topic_to_column:
        return jsonify({"error": "Invalid topic names"}), 400

    serendip = get_serendipitous(df, preferred, non_preferred).reset_index(drop=True)
    prefer = get_preferred(df, preferred, n=4).reset_index(drop=True)

    result = {
        "Today": datetime.today().strftime("%B %d, %Y")
    }

    # 返回 Serendipitous 推荐
    for i in range(2):
        result[f"Seren_Article{i+1}_Title"] = serendip.loc[i, "Title"]
        result[f"Seren_Article{i+1}_Summary"] = serendip.loc[i, "Content Summary"]
        result[f"Seren_Article{i+1}_Topic"] = serendip.loc[i, "Primary Topic"]

    # 返回 Preferred 推荐
    for i in range(4):
        result[f"Prefer_Article{i+1}_Title"] = prefer.loc[i, "Title"]
        result[f"Prefer_Article{i+1}_Summary"] = prefer.loc[i, "Content Summary"]
        result[f"Prefer_Article{i+1}_Topic"] = prefer.loc[i, "Primary Topic"]

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
