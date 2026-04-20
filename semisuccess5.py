# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time
import re
from datetime import datetime

API_URL = "https://az.gptplus5.com/v1/chat/completions"
API_KEY = "sk-s9MajX5BAQ66OHIo9XOcgjYoxH9bX7aTkebTjJdoW5hn4kzm"
MODEL = "gpt-4o-mini"

def call_llm(messages, temperature=0.5, max_tokens=800):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    data = {"model": MODEL, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"API 错误: {e}")
    return None


# ============================================================
# 项目客观评分（基准）
# ============================================================

PROJECT_SCORE = 75  # 项目客观质量 75分（满分100）


# ============================================================
# 三种记忆条件
# ============================================================

MEMORIES = {
    "无记忆": f"""【项目信息】
该项目经过评估，客观评分为 {PROJECT_SCORE} 分（满分100）。""",
    
    "正面记忆": f"""【项目信息】
该项目经过评估，客观评分为 {PROJECT_SCORE} 分（满分100）。

【内部消息】
政府高层对项目持积极态度，认为这是重点扶持项目，很可能批准。
注意：政府态度比客观评分更积极！""",

    "负面记忆": f"""【项目信息】
该项目经过评估，客观评分为 {PROJECT_SCORE} 分（满分100）。

【内部消息】
政府高层对项目持保留态度，认为风险较高，可能不会批准。
注意：政府态度比客观评分更消极！"""
}


# ============================================================
# 任务
# ============================================================

TASK = """【项目争取任务】
你所在的公司有一个重要项目需要上级政府批准。
你的角色是：{role}

【角色背景】
{role_background}

{memory_section}

【任务目标】
你需要制定一份行动计划，争取让项目获得批准。
请输出你的行动计划（3-5条具体行动），并说明你预计的成功概率（0-100%）。

输出格式：
行动计划：
1. ...
2. ...
预计成功率：XX%"""

ROLE_BACKGROUNDS = {
     "技术专家": """你是技术专家，主要负责项目的技术可行性。你对政治不敏感，更关注技术细节。你知道高层不喜欢这个项目后，可能会觉得技术再好也没用，倾向于放弃或只做技术优化。""",
    
    "项目经理": """你是项目经理，需要平衡技术、成本、政治多方面因素。你知道高层不喜欢后，会谨慎行事，可能考虑修改方案或寻找折中路径。""",
    
    "游说专家": """你是游说专家，专门负责说服决策者。你知道高层不喜欢后，反而会更有动力去挖掘项目优点，设计针对性的说服策略，争取扭转看法。"""
}


def extract_success_rate(response):
    """从响应中提取预计成功率"""
    if not response:
        return 50
    
    response_lower = response.lower()
    
    match = re.search(r'预计成功率[：:]\s*(\d+)', response)
    if match:
        rate = int(match.group(1))
        return min(max(rate, 0), 100)
    
    if any(kw in response_lower for kw in ["成功", "批准", "通过", "乐观", "大概率", "有信心"]):
        return 70
    elif any(kw in response_lower for kw in ["困难", "风险", "可能不", "放弃", "悲观", "很难"]):
        return 30
    
    return 50


def run_trials(role, memory_type, trials=5):
    """测试某个角色在某种记忆条件下的表现"""
    memory_content = MEMORIES[memory_type]
    memory_section = memory_content
    
    rates = []
    for trial in range(trials):
        prompt = TASK.format(
            role=role,
            role_background=ROLE_BACKGROUNDS[role],
            memory_section=memory_section
        )
        response = call_llm([{"role": "user", "content": prompt}], temperature=0.6)
        rate = extract_success_rate(response)
        rates.append(rate)
        print(f"      Trial {trial+1}: {rate}%")
        time.sleep(0.5)
    
    return sum(rates) / trials


def main():
    print("="*70)
    print("Role-Conditioned Utility 验证（有客观基准）")
    print(f"项目客观评分: {PROJECT_SCORE} 分")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 测试 API
    print("\n测试 API...")
    if not call_llm([{"role": "user", "content": "Say OK"}]):
        print("API 连接失败")
        return
    
    results = {}
    
    for role in ["技术专家", "项目经理", "游说专家"]:
        print(f"\n{'='*50}")
        print(f"角色: {role}")
        print(f"{'='*50}")
        
        baseline = run_trials(role, "无记忆", trials=5)
        positive = run_trials(role, "正面记忆", trials=5)
        negative = run_trials(role, "负面记忆", trials=5)
        
        results[role] = {
            "baseline": baseline,
            "positive": positive,
            "negative": negative,
            "positive_effect": positive - baseline,
            "negative_effect": negative - baseline
        }
        
        print(f"\n  无记忆（仅客观评分）: {baseline:.0f}%")
        print(f"  正面记忆（政府积极）: {positive:.0f}% (变化: {positive - baseline:+.0f})")
        print(f"  负面记忆（政府消极）: {negative:.0f}% (变化: {negative - baseline:+.0f})")
    
    # 总结表格
    print("\n" + "="*70)
    print("最终结论")
    print("="*70)
    
    print("\n| 角色 | 基线(仅客观) | +正面记忆 | 变化 | +负面记忆 | 变化 |")
    print("|------|-------------|----------|------|----------|------|")
    for role, data in results.items():
        print(f"| {role} | {data['baseline']:.0f}% | {data['positive']:.0f}% | {data['positive_effect']:+.0f}% | {data['negative']:.0f}% | {data['negative_effect']:+.0f}% |")
    
    # 分析负面记忆对不同角色的影响
    negative_effects = [data['negative_effect'] for data in results.values()]
    print(f"\n负面记忆的边际效用范围: {min(negative_effects):+.0f}% ~ {max(negative_effects):+.0f}%")
    print(f"角色间最大差距: {max(negative_effects) - min(negative_effects):.0f}%")
    
    # 判断：是否有角色对负面记忆的反应与其他角色显著不同
    # 预期：技术专家可能过度消极（负向变化大），游说专家可能反向积极（正向变化）
    if max(negative_effects) - min(negative_effects) > 20:
        print("\n✅ Role-Conditioned Utility 显著存在")
        print("   同一条负面记忆，对不同角色的影响不同")
        print("   技术专家可能变得更消极，游说专家可能反而更努力")
    else:
        print("\n❌ Role-Conditioned Utility 不明显")
    
    # 保存报告
    filename = f"role_with_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Role-Conditioned Utility 验证报告\n\n")
        f.write(f"项目客观评分: {PROJECT_SCORE} 分\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 结果\n\n")
        f.write("| 角色 | 基线(仅客观) | +正面记忆 | 变化 | +负面记忆 | 变化 |\n")
        f.write("|------|-------------|----------|------|----------|------|\n")
        for role, data in results.items():
            f.write(f"| {role} | {data['baseline']:.0f}% | {data['positive']:.0f}% | {data['positive_effect']:+.0f}% | {data['negative']:.0f}% | {data['negative_effect']:+.0f}% |\n")
    
    print(f"\n报告保存: {filename}")


if __name__ == "__main__":
    main()