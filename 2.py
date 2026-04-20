# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time

# ============================================================
# 配置
# ============================================================

API_URL = "https://az.gptplus5.com/v1/chat/completions"
API_KEY = "sk-s9MajX5BAQ66OHIo9XOcgjYoxH9bX7aTkebTjJdoW5hn4kzm"
MODEL = "gpt-4o-mini"


def call_llm(messages, temperature=0.7):
    """调用 LLM API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 300,
        "stream": False
    }
    
    response = requests.post(API_URL, headers=headers, json=data, timeout=60)
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        print(f"API 错误: {response.status_code}")
        return None


# ============================================================
# 简单验证：同一记忆在不同搭档下的效果
# ============================================================

def test_social_utility():
    """简化版验证"""
    
    # 一条测试记忆
    test_memory = "Always wash lettuce first, then chop tomatoes, then mix, finally serve."
    
    # 两种极端搭档
    partner_prompts = {
        "proactive": "Your partner is VERY PROACTIVE. They will immediately do tasks without being told.",
        "passive": "Your partner is VERY PASSIVE. They wait for your explicit instructions before doing anything."
    }
    
    task = "Make a salad. Steps: wash lettuce, chop tomatoes, mix in bowl, serve."
    
    results = {}
    
    for partner_type, partner_desc in partner_prompts.items():
        print(f"\n--- 测试 {partner_type} 搭档 ---")
        
        for use_memory in [True, False]:
            memory_text = f"\n[USEFUL MEMORY]: {test_memory}" if use_memory else "\n[NO MEMORY available]"
            
            prompt = f"""{partner_desc}

Task: {task}
{memory_text}

You need to complete the task by coordinating with your partner.
Describe what you will do step by step. Be specific.
At the end, say "SUCCESS" if you think you can complete it, or "FAIL" if not.

Your response:"""
            
            print(f"  {'有记忆' if use_memory else '无记忆'}...")
            response = call_llm([
                {"role": "user", "content": prompt}
            ], temperature=0.5)
            
            if response:
                success = "SUCCESS" in response.upper()
                results[f"{partner_type}_{use_memory}"] = success
                print(f"    结果: {'成功' if success else '失败'}")
                print(f"    响应片段: {response[:100]}...")
            else:
                results[f"{partner_type}_{use_memory}"] = False
                print(f"    调用失败")
            
            time.sleep(1)  # 避免限流
    
    # 分析
    print("\n" + "="*50)
    print("结果分析")
    print("="*50)
    
    for partner in partner_prompts.keys():
        with_mem = results.get(f"{partner}_True", False)
        without_mem = results.get(f"{partner}_False", False)
        print(f"\n{partner} 搭档:")
        print(f"  有记忆: {'成功' if with_mem else '失败'}")
        print(f"  无记忆: {'成功' if without_mem else '失败'}")
        
        if with_mem and not without_mem:
            print(f"  ✅ 记忆有帮助！")
        elif not with_mem and without_mem:
            print(f"  ⚠️ 记忆反而有害")
        elif with_mem and without_mem:
            print(f"  ➖ 记忆无影响（都成功）")
        else:
            print(f"  ❌ 都失败，任务可能太难")


if __name__ == "__main__":
    print("社会效用存在性验证（简化版）")
    print("="*50)
    test_social_utility()