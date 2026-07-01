from openai import OpenAI
import json

client = OpenAI(
    api_key="sk-2a48b88154234a8487f79efac930729e",
    base_url="https://api.deepseek.com"
)

# ======================
# 1. CASE系统（平台核心）
# ======================

CASES = {
    "case1": {
        "name": "服务报价谈判",
        "topic": "服务报价120元，买方希望压价",
        "buyer_budget": 85,
        "seller_price": 120,
        "seller_min": 105
    },
    "case2": {
        "name": "咨询服务谈判",
        "topic": "咨询服务报价200元",
        "buyer_budget": 150,
        "seller_price": 200,
        "seller_min": 170
    }
}

# ======================
# 2. 核心引擎
# ======================

def run_negotiation(case_id="case1"):

    case = CASES[case_id]

    buyer_state = {
        "initial_budget": case["buyer_budget"],
        "hard_ceiling": case["buyer_budget"] + 10,
        "history": [],
        "last_message": ""
    }

    seller_state = {
        "initial_price": case["seller_price"],
        "min_price": case["seller_min"],
        "history": [],
        "last_message": ""
    }

    print(f"\n===== 开始谈判：{case['name']} =====")

    # ======================
    # 3. 谈判循环
    # ======================

    for i in range(3):
        print(f"\n--- 第{i+1}轮 ---")

        # 买方
        buyer_prompt = f"""
你是买方。
预算上限：{buyer_state['hard_ceiling']}
上一轮卖方：{buyer_state['last_message']}
"""

        buyer_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": buyer_prompt},
                {"role": "user", "content": case["topic"]}
            ]
        ).choices[0].message.content

        print("A:", buyer_resp)

        buyer_state["history"].append(buyer_resp)
        buyer_state["last_message"] = buyer_resp

        # 卖方
        seller_prompt = f"""
你是卖方。
底价：{seller_state['min_price']}
上一轮买方：{seller_state['last_message']}
"""

        seller_resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": seller_prompt},
                {"role": "user", "content": buyer_resp}
            ]
        ).choices[0].message.content

        print("B:", seller_resp)

        seller_state["history"].append(seller_resp)
        seller_state["last_message"] = seller_resp

    # ======================
    # 4. 评分系统
    # ======================

    buyer_score = min(100, len(buyer_state["history"]) * 15)
    seller_score = min(100, len(seller_state["history"]) * 15)

    winner = "buyer" if buyer_score > seller_score else "seller"

    # ======================
    # 5. 结构化输出（平台核心）
    # ======================

    result = {
        "case": case["name"],
        "winner": winner,
        "buyer_score": buyer_score,
        "seller_score": seller_score,
        "buyer_dialogue": buyer_state["history"],
        "seller_dialogue": seller_state["history"]
    }

    print("\n===== 平台输出 =====")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


# ======================
# 6. 运行入口（平台体验）
# ======================

if __name__ == "__main__":
    print("可选case：case1 / case2")
    case_id = input("请输入case：")
    run_negotiation(case_id)