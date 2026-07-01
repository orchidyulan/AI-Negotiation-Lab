from openai import OpenAI

client = OpenAI(
    api_key="sk-2a48b88154234a8487f79efac930729e",
    base_url="https://api.deepseek.com"
)

# ====== 初始设定 ======
system_prompt = """
你是一个专业谈判对手（B角色）。
你的目标：
- 坚持自身利益
- 合理让步，但不要轻易妥协
- 每一轮回应都要带策略
"""

user_state = "我希望价格从120降到100，并且包含售后服务"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_state}
]

# ====== 多轮谈判 ======
for i in range(3):
    print(f"\n===== 第{i+1}轮谈判 =====")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )

    ai_reply = response.choices[0].message.content
    print("B:", ai_reply)

    # 把AI回复加入对话（形成博弈闭环）
    messages.append({"role": "assistant", "content": ai_reply})

    # 模拟A的回应（先用简单规则，后面会升级成AI）
    user_reply = "我可以稍微让步，但需要更多服务保障"
    print("A:", user_reply)

    messages.append({"role": "user", "content": user_reply})

# ====== 结束总结 ======
summary = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是谈判总结专家"},
        {"role": "user", "content": str(messages)}
    ]
)

print("\n===== 谈判总结 =====")
print(summary.choices[0].message.content)