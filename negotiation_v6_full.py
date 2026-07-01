from openai import OpenAI

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
# 2. Prompt 构建
# ======================

def build_buyer_prompt(state):
    return f"""
你是买方A（谈判者）。

当前状态：
- 初始预算：{state['initial_budget']}
- 当前出价：{state['current_offer']}
- 最高可接受价格：{state['hard_ceiling']}

上一轮卖方回应：
{state['last_message']}

最近历史：
{state['history'][-3:]}

规则：
- 不允许超过预算
- 必须基于上一轮继续谈判
- 不允许重复之前内容
- 必须推进谈判（不能停滞）
"""

def build_seller_prompt(state):
    return f"""
你是卖方B（谈判者）。

当前状态：
- 初始价格：{state['initial_price']}
- 当前报价：{state['current_price']}
- 最低价格：{state['min_price']}

上一轮买方回应：
{state['last_message']}

最近历史：
{state['history'][-3:]}

规则：
- 不允许低于最低价
- 必须基于买方最新回应调整策略
- 不允许重复上一轮
- 必须推动谈判进展
"""

# ======================
# 3. 谈判循环（核心）
# ======================

for i in range(3):
    print(f"\n===== 第{i+1}轮谈判 =====")

    # ===== 买方 =====
    buyer_prompt = build_buyer_prompt(buyer_state)

    buyer_resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": buyer_prompt},
            {"role": "user", "content": topic}
        ]
    ).choices[0].message.content

    print("A(买方):", buyer_resp)

    buyer_state["history"].append(buyer_resp)
    buyer_state["last_message"] = buyer_resp

    # ===== 卖方 =====
    seller_prompt = build_seller_prompt(seller_state)

    seller_resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": seller_prompt},
            {"role": "user", "content": buyer_resp}
        ]
    ).choices[0].message.content

    print("B(卖方):", seller_resp)

    seller_state["history"].append(seller_resp)
    seller_state["last_message"] = seller_resp

# ======================
# 4. LLM总结
# ======================

summary = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": "你是谈判分析专家，请分析本次谈判的策略、让步路径和结果"
        },
        {
            "role": "user",
            "content": f"""
买方状态：
{buyer_state}

卖方状态：
{seller_state}
"""
        }
    ]
)

print("\n===== 谈判总结 =====")
print(summary.choices[0].message.content)


# ======================
# 5. 评分系统（v1）
# ======================

def score_negotiation(buyer_state, seller_state):
    buyer_score = 0
    seller_score = 0

    # 买方：压价能力 + 活跃度
    buyer_score += (buyer_state["initial_budget"] - 80) * 2
    buyer_score += len(buyer_state["history"]) * 10

    # 卖方：守价能力 + 活跃度
    seller_score += (seller_state["initial_price"] - seller_state["min_price"]) * 2
    seller_score += len(seller_state["history"]) * 10

    buyer_score = min(100, buyer_score)
    seller_score = min(100, seller_score)

    winner = "buyer" if buyer_score > seller_score else "seller"

    return {
        "buyer_score": buyer_score,
        "seller_score": seller_score,
        "winner": winner
    }


# ======================
# 6. 输出评分（注意：必须顶格）
# ======================

result = score_negotiation(buyer_state, seller_state)

print("\n===== 谈判评分 =====")
print("买方得分:", result["buyer_score"])
print("卖方得分:", result["seller_score"])
print("胜方:", result["winner"])