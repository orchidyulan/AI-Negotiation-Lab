from openai import OpenAI
import json

client = OpenAI(
    api_key="sk-2a48b88154234a8487f79efac930729e",
    base_url="https://api.deepseek.com"
)

# ======================
# 1. 状态系统
# ======================

buyer_state = {
    "initial_budget": 85,
    "current_offer": 85,
    "hard_ceiling": 95,
    "history": [],
    "last_message": ""
}

seller_state = {
    "initial_price": 120,
    "current_price": 120,
    "min_price": 105,
    "history": [],
    "last_message": ""
}

topic = "服务报价谈判：初始价格120元"

# ======================
# 2. Prompt
# ======================

def build_buyer_prompt(state):
    return f"""
你是买方A。

预算上限：{state['hard_ceiling']}
历史：{state['history'][-3:]}
上一轮卖方：{state['last_message']}

要求：
- 必须推进谈判
- 不允许超过预算
- 不允许重复表达
"""

def build_seller_prompt(state):
    return f"""
你是卖方B。

底价：{state['min_price']}
历史：{state['history'][-3:]}
上一轮买方：{state['last_message']}

要求：
- 不允许低于底价
- 必须推进谈判
- 不允许重复表达
"""

# ======================
# 3. 谈判循环
# ======================

for i in range(3):
    print(f"\n===== 第{i+1}轮谈判 =====")

    # 买方
    buyer_resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": build_buyer_prompt(buyer_state)},
            {"role": "user", "content": topic}
        ]
    ).choices[0].message.content

    print("A:", buyer_resp)

    buyer_state["history"].append(buyer_resp)
    buyer_state["last_message"] = buyer_resp

    # 卖方
    seller_resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": build_seller_prompt(seller_state)},
            {"role": "user", "content": buyer_resp}
        ]
    ).choices[0].message.content

    print("B:", seller_resp)

    seller_state["history"].append(seller_resp)
    seller_state["last_message"] = seller_resp

# ======================
# 4. 规则评分系统
# ======================

def rule_score(buyer_state, seller_state):
    buyer = min(100,
        (buyer_state["initial_budget"] - 80) * 2 +
        len(buyer_state["history"]) * 10
    )

    seller = min(100,
        (seller_state["initial_price"] - seller_state["min_price"]) * 2 +
        len(seller_state["history"]) * 10
    )

    return buyer, seller

# ======================
# 5. 策略识别（LLM）
# ======================

strategy_prompt = f"""
请分析以下谈判记录，输出JSON：

买方：
{buyer_state["history"]}

卖方：
{seller_state["history"]}

输出格式：
{{
  "buyer_strategy": "",
  "seller_strategy": "",
  "dominant_side": "buyer/seller"
}}
"""

strategy_resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是谈判策略分析器"},
        {"role": "user", "content": strategy_prompt}
    ]
).choices[0].message.content

try:
    strategy_json = json.loads(strategy_resp)
except:
    strategy_json = {
        "buyer_strategy": "unknown",
        "seller_strategy": "unknown",
        "dominant_side": "unknown"
    }

# ======================
# 6. LLM裁判（最终判断）
# ======================

judge_prompt = f"""
你是谈判裁判，请综合判断胜者。

规则评分：
- 买方分数
- 卖方分数

策略分析：
{strategy_json}

谈判记录：
买方：{buyer_state["history"]}
卖方：{seller_state["history"]}

请输出：
1. 最终胜者（buyer or seller）
2. 理由（简洁）
3. 置信度（0-1）
"""

judge_resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是严谨的谈判裁判"},
        {"role": "user", "content": judge_prompt}
    ]
).choices[0].message.content

# ======================
# 7. 规则评分
# ======================

buyer_score, seller_score = rule_score(buyer_state, seller_state)

# ======================
# 8. 最终融合输出
# ======================

print("\n===== 规则评分 =====")
print("买方:", buyer_score)
print("卖方:", seller_score)

print("\n===== 策略分析 =====")
print(strategy_json)

print("\n===== LLM裁判 =====")
print(judge_resp)

print("\n===== 最终统一结论 =====")
print("✔ 系统已完成三层融合评估（Rule + Strategy + Judge）")