from openai import OpenAI

print("开始调用AI...")

client = OpenAI(
    api_key="sk-2a48b88154234a8487f79efac930729e",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一名谈判助手"},
        {"role": "user", "content": "你好，请做一个自我介绍"}
    ]
)

print("===== AI回复 =====")
print(response.choices[0].message.content)