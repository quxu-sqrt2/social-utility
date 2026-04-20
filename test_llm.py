import requests

API_URL = "https://az.gptplus5.com/v1/chat/completions"
API_KEY = "sk-s9MajX5BAQ66OHIo9XOcgjYoxH9bX7aTkebTjJdoW5hn4kzm"
MODEL = "gpt-4o-mini"

def call_llm(prompt, temperature=0.1):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"LLM调用失败: {e}")
        return "error"

if __name__ == "__main__":
    print("开始测试LLM连接...")
    test_prompt = "你好"
    response = call_llm(test_prompt)
    print(f"LLM响应: {response}")
    print("测试完成！")
