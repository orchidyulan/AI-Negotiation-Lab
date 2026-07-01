from openai import OpenAI

client = OpenAI(
    api_key="sk-2a48b88154234a8487f79efac930729e",
    base_url="https://api.deepseek.com"
)

# ===== 角色设定 =====
buyer_prompt = """
你是买方A（强硬型谈判者）。
目标：
- 尽可能压低价格
- 强调预算限制
- 每轮都要尝试获得更大让步
"""

seller_prompt = """
你是卖方B（理性价值型谈判者）。
目标：
- 保持价格底线
- 适度让步但控制幅度
- 强调产品/服务价值
"""

# 初始议题
topic = "一项服务报价120元，买方希望降价"

buyer_messages = [
    {"role": "system", "content": buyer_prompt},
    {"role": "user", "content": topic}
]

seller_messages = [
    {"role": "system", "content": seller_prompt}
]

# ===== 双AI博弈 =====
for i in range(3):
    print(f"\n===== 第{i+1}轮谈判 =====")

    # A（买方）发言
    buyer_resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=buyer_messages
    ).choices[0].message.content

    print("A(买方):", buyer_resp)

    seller_messages.append({"role": "user", "content": buyer_resp})

    # B（卖方）回应
    seller_resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=seller_messages
    ).choices[0].message.content

    print("B(卖方):", seller_resp)

    buyer_messages.append({"role": "assistant", "content": seller_resp})
    seller_messages.append({"role": "assistant", "content": buyer_resp})

# ===== 结束总结 =====
summary = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是谈判分析专家，请总结这场谈判的策略与结果"},
        {"role": "user", "content": f"对话记录：{buyer_messages + seller_messages}"}
    ]
)

print("\n===== 谈判总结 =====")
print(summary.choices[0].message.content)