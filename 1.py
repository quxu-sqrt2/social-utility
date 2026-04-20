# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time

# ============================================================
# 你的配置
# ============================================================

API_URL = "https://az.gptplus5.com/v1/chat/completions"
API_KEY = "sk-s9MajX5BAQ66OHIo9XOcgjYoxH9bX7aTkebTjJdoW5hn4kzm"
MODEL = "gpt-4o-mini"


def call_llm(messages, temperature=0.7, max_tokens=500):
    """调用 LLM API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"API 错误: {response.status_code}")
            print(f"响应: {response.text}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None


# ============================================================
# 测试
# ============================================================

def test_api():
    print("测试 API 连接...")
    result = call_llm([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say OK"}
    ])
    if result:
        print(f"✅ API 连接成功！响应: {result}")
        return True
    else:
        print("❌ API 连接失败")
        return False


# ============================================================
# 任务定义
# ============================================================

TASK = "Make a salad. Steps: wash lettuce, chop tomatoes, mix in bowl, serve."

PARTNER_STYLES = {
    "proactive": "Your partner is PROACTIVE: they start tasks immediately without waiting.",
    "passive": "Your partner is PASSIVE: they wait for your instructions before acting.",
    "random": "Your partner acts RANDOMLY: sometimes helpful, sometimes not.",
    "collaborative": "Your partner is COLLABORATIVE: they coordinate naturally with you."
}


# ============================================================
# 单次执行
# ============================================================

def run_once(partner_style: str, memory: str = "") -> bool:
    """执行一次任务，返回是否成功"""
    
    style_desc = PARTNER_STYLES.get(partner_style, "")
    
    memory_text = f"\n[MEMORY from past success]: {memory}" if memory else ""
    
    system_prompt = f"""You are completing a kitchen task.

{style_desc}

Task: {TASK}
{memory_text}

Complete all 4 steps. Reply with ONLY a JSON: 
{{"step": number, "action": "what you do", "done": false/true}}

When all steps done, set "done": true.
"""
    
    actions = []
    
    for step in range(1, 7):
        response = call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Step {step}. Previous actions: {actions}. What now?"}
        ], temperature=0.7)
        
        if response is None:
            return False
        
        try:
            # 提取 JSON
            if "{" in response:
                json_str = response[response.find("{"):response.rfind("}")+1]
                result = json.loads(json_str)
                actions.append(result.get("action", ""))
                if result.get("done", False):
                    return True
            else:
                actions.append(response[:50])
        except:
            actions.append(response[:50])
        
        time.sleep(0.5)  # 避免限流
    
    return False


# ============================================================
# 生成记忆
# ============================================================

def generate_memory() -> str:
    """通过一次成功执行，生成记忆"""
    
    print("正在生成基准记忆...")
    
    success = False
    for attempt in range(3):
        success = run_once("proactive", memory="")
        if success:
            break
        print(f"  第 {attempt+1} 次尝试失败，重试...")
    
    if not success:
        print("无法生成成功轨迹，使用默认记忆")
        return "Work efficiently with your partner. Start with washing lettuce, then chop tomatoes, mix, then serve."
    
    print("成功执行！正在总结记忆...")
    
    prompt = """Based on a successful salad-making task, write ONE sentence of reusable advice (max 20 words) that would help complete similar kitchen tasks efficiently.

Advice:"""
    
    memory = call_llm([
        {"role": "user", "content": prompt}
    ], temperature=0.5, max_tokens=50)
    
    if memory is None:
        memory = "Work step by step and coordinate with your partner."
    
    print(f"生成的记忆: {memory}")
    return memory


# ============================================================
# 主实验
# ============================================================

def run_experiment(trials_per_condition: int = 3):
    """运行实验"""
    
    print("\n" + "="*60)
    print("社会效用验证实验")
    print("="*60)
    
    # 测试 API
    if not test_api():
        print("请先解决 API 连接问题")
        return
    
    # 1. 生成基准记忆
    memory = generate_memory()
    print(f"\n使用记忆: {memory}\n")
    
    # 2. 存储结果
    results = {}
    for style in PARTNER_STYLES.keys():
        for has_memory in [True, False]:
            results[(style, has_memory)] = {"success": 0, "total": 0}
    
    # 3. 运行实验
    for style in PARTNER_STYLES.keys():
        print(f"\n--- 测试搭档: {style} ---")
        
        for trial in range(trials_per_condition):
            # 有记忆
            success = run_once(style, memory)
            results[(style, True)]["success"] += 1 if success else 0
            results[(style, True)]["total"] += 1
            
            # 无记忆
            success = run_once(style, "")
            results[(style, False)]["success"] += 1 if success else 0
            results[(style, False)]["total"] += 1
            
            print(f"  Trial {trial+1}: with_mem={results[(style, True)]['success']}/{results[(style, True)]['total']}, without_mem={results[(style, False)]['success']}/{results[(style, False)]['total']}")
    
    # 4. 分析结果
    print("\n" + "="*60)
    print("实验结果")
    print("="*60)
    
    print(f"\n{'搭档风格':<15} {'有记忆成功率':<15} {'无记忆成功率':<15} {'差异':<10}")
    print("-"*55)
    
    style_rates = {}
    for style in PARTNER_STYLES.keys():
        with_success = results[(style, True)]["success"]
        with_total = results[(style, True)]["total"]
        without_success = results[(style, False)]["success"]
        without_total = results[(style, False)]["total"]
        
        rate_with = with_success / with_total if with_total > 0 else 0
        rate_without = without_success / without_total if without_total > 0 else 0
        diff = rate_with - rate_without
        
        style_rates[style] = rate_with
        
        print(f"{style:<15} {rate_with:<15.3f} {rate_without:<15.3f} {diff:+.3f}")
    
    max_rate = max(style_rates.values())
    min_rate = min(style_rates.values())
    gap = max_rate - min_rate
    
    print(f"\n同一记忆在不同搭档下的成功率范围: {min_rate:.3f} ~ {max_rate:.3f}")
    print(f"最大差距: {gap:.3f}")
    
    print("\n" + "="*60)
    if gap > 0.2:
        print("✅ 结论: 社会效用存在显著差异")
        print("   同一记忆在不同社会条件下的效果明显不同")
    elif gap > 0.1:
        print("⚠️ 结论: 存在一定差异，建议增加实验次数确认")
    else:
        print("❌ 结论: 差异不明显，当前任务/记忆下社会效用不显著")


# ============================================================
# 运行
# ============================================================

if __name__ == "__main__":
    run_experiment(trials_per_condition=3)  # 先跑3次测试