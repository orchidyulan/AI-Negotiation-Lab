from openai import OpenAI

client = OpenAI(
    api_key="sk-2a48b88154234a8487f79efac930729e",
    base_url="https://api.deepseek.com"
)

# ======================
# 1. 状态定义（核心升级）
# ======================

buyer_state = {
    "initial_budget": 85,
    "current_offer": 85,
    "hard_ceiling": 95,
    "target_price": 90,
    "history": []
}

seller_state = {
    "initial_price": 120,
    "current_price": 120,
    "min_price": 105,
    "history": []
}

topic = "服务报价谈判：初始价格120元"

# ======================
# 2. 状态驱动 Prompt
# ======================

def build_buyer_prompt(state):
    return f"""
你是买方A（谈判者）。

你的状态如下：
- 初始预算：{state['initial_budget']}
- 当前报价意愿：{state['current_offer']}
- 历史让步：{state['history']}

规则：
- 不允许超过硬预算
- 可以逐步让步，但不能回退
- 每一轮必须基于当前状态发言
"""

def build_seller_prompt(state):
    return f"""
你是卖方B（谈判者）。

你的状态如下：
- 初始价格：{state['initial_price']}
- 当前报价：{state['current_price']}
- 历史让步：{state['history']}

规则：
- 不允许低于底线价格
- 可以策略性让步
- 每轮必须基于状态，不得自相矛盾
"""

# ======================
# 3. 谈判循环
# ======================

for i in range(3):
    print(f"\n===== 第{i+1}轮谈判 =====")

    # --- 买方 ---
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

    # --- 卖方 ---
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

# ======================
# 4. 结束总结
# ======================

summary = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是谈判分析专家，请基于全过程进行结构化总结"},
        {"role": "user", "content": str({
            "buyer_state": buyer_state,
            "seller_state": seller_state
        })}
    ]
)

print("\n===== 谈判总结 =====")
print(summary.choices[0].message.content)