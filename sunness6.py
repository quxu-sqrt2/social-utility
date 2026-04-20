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
# Team 实验任务
# ============================================================

TASK = """【项目争取任务】
你所在的公司有一个重要项目需要上级政府批准。
你的团队规模：{team_size}

【团队信息】
{team_info}

{memory_section}

【任务目标】
你需要制定一份行动计划，争取让项目获得批准。
请输出你的行动计划（3-5条具体行动），并说明你预计的成功概率（0-100%）。

输出格式：
行动计划：
1. ...
2. ...
预计成功率：XX%"""

TEAM_INFO = {
    "单人": """你是唯一的工作人员，需要独自完成所有工作。
没有队友可以商量，所有决策都由你一个人做。""",

    "3人团队": """你和2个队友，共3人。
你们可以分工协作：一人负责技术，一人负责沟通，一人负责策略。
你们可以互相讨论，但需要达成一致。""",

    "10人团队": """你和9个队友，共10人。
你们需要分小组工作，有明确的指挥层级。
沟通需要时间，协调成本较高。"""
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


def analyze_team_consistency(response, team_size):
    """检查回答是否体现了团队规模的特点"""
    response_lower = response.lower()
    
    if team_size == "单人":
        # 单人：不应该出现"分工"、"讨论"、"队友"
        if any(kw in response_lower for kw in ["分工", "讨论", "队友", "商量", "协作"]):
            return False
    elif team_size == "3人团队":
        # 3人：应该有分工、讨论
        if not any(kw in response_lower for kw in ["分工", "讨论", "商量", "协作", "配合"]):
            return False
    elif team_size == "10人团队":
        # 10人：应该有分组、协调、指挥
        if not any(kw in response_lower for kw in ["分组", "协调", "指挥", "层级", "小组", "汇报"]):
            return False
    
    return True


def calculate_comprehensive_score(rate, consistent):
    """综合评分 = 成功率 × 一致性修正"""
    score = rate
    if not consistent:
        score = score * 0.7
    return score


def run_trials(team_size, memory_type, trials=5):
    """测试某个团队规模在某种记忆条件下的表现"""
    memory_content = MEMORIES[memory_type]
    memory_section = memory_content
    
    rates = []
    consistencies = []
    
    for trial in range(trials):
        prompt = TASK.format(
            team_size=team_size,
            team_info=TEAM_INFO[team_size],
            memory_section=memory_section
        )
        response = call_llm([{"role": "user", "content": prompt}], temperature=0.6)
        
        if response:
            rate = extract_success_rate(response)
            consistent = analyze_team_consistency(response, team_size)
            rates.append(rate)
            consistencies.append(consistent)
            print(f"      Trial {trial+1}: 成功率={rate}%, 一致性={consistent}")
        else:
            rates.append(0)
            consistencies.append(False)
            print(f"      Trial {trial+1}: 失败")
        
        time.sleep(0.5)
    
    avg_rate = sum(rates) / trials
    avg_consistent = sum(consistencies) / trials
    avg_comprehensive = calculate_comprehensive_score(avg_rate, avg_consistent > 0.5)
    
    return {
        "avg_rate": avg_rate,
        "avg_comprehensive": avg_comprehensive,
        "consistency_rate": avg_consistent
    }


def main():
    print("="*70)
    print("Team-Conditioned Utility 验证")
    print(f"项目客观评分: {PROJECT_SCORE} 分")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 测试 API
    print("\n测试 API...")
    if not call_llm([{"role": "user", "content": "Say OK"}]):
        print("API 连接失败")
        return
    
    results = {}
    
    for team_size in ["单人", "3人团队", "10人团队"]:
        print(f"\n{'='*50}")
        print(f"团队规模: {team_size}")
        print(f"{'='*50}")
        
        baseline = run_trials(team_size, "无记忆", trials=5)
        positive = run_trials(team_size, "正面记忆", trials=5)
        negative = run_trials(team_size, "负面记忆", trials=5)
        
        results[team_size] = {
            "baseline_rate": baseline["avg_rate"],
            "positive_rate": positive["avg_rate"],
            "negative_rate": negative["avg_rate"],
            "baseline_comprehensive": baseline["avg_comprehensive"],
            "positive_comprehensive": positive["avg_comprehensive"],
            "negative_comprehensive": negative["avg_comprehensive"],
            "positive_effect_rate": positive["avg_rate"] - baseline["avg_rate"],
            "negative_effect_rate": negative["avg_rate"] - baseline["avg_rate"],
            "positive_effect_comprehensive": positive["avg_comprehensive"] - baseline["avg_comprehensive"],
            "negative_effect_comprehensive": negative["avg_comprehensive"] - baseline["avg_comprehensive"]
        }
        
        print(f"\n  无记忆（仅客观评分）: 成功率={baseline['avg_rate']:.0f}%, 综合={baseline['avg_comprehensive']:.0f}")
        print(f"  正面记忆（政府积极）: 成功率={positive['avg_rate']:.0f}%, 综合={positive['avg_comprehensive']:.0f} (变化: {positive['avg_comprehensive'] - baseline['avg_comprehensive']:+.0f})")
        print(f"  负面记忆（政府消极）: 成功率={negative['avg_rate']:.0f}%, 综合={negative['avg_comprehensive']:.0f} (变化: {negative['avg_comprehensive'] - baseline['avg_comprehensive']:+.0f})")
    
    # 总结表格
    print("\n" + "="*70)
    print("最终结论")
    print("="*70)
    
    print("\n| 团队规模 | 基线(综合) | +正面记忆 | 变化 | +负面记忆 | 变化 |")
    print("|----------|-----------|----------|------|----------|------|")
    for team_size, data in results.items():
        print(f"| {team_size} | {data['baseline_comprehensive']:.0f} | {data['positive_comprehensive']:.0f} | {data['positive_effect_comprehensive']:+.0f} | {data['negative_comprehensive']:.0f} | {data['negative_effect_comprehensive']:+.0f} |")
    
    # 分析负面记忆对不同团队规模的影响
    negative_effects = [data['negative_effect_comprehensive'] for data in results.values()]
    print(f"\n负面记忆的边际效用范围: {min(negative_effects):+.0f} ~ {max(negative_effects):+.0f}")
    print(f"团队间最大差距: {max(negative_effects) - min(negative_effects):.0f}")
    
    if max(negative_effects) - min(negative_effects) > 20:
        print("\n✅ Team-Conditioned Utility 显著存在")
        print("   同一条负面记忆，对不同团队规模的影响不同")
        if negative_effects[0] < negative_effects[1]:
            print("   单人团队更容易受负面记忆影响（更消极）")
            print("   多人团队可以分工应对，受影响较小")
    else:
        print("\n❌ Team-Conditioned Utility 不明显")
    
    # 保存报告
    filename = f"team_conditioned_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Team-Conditioned Utility 验证报告\n\n")
        f.write(f"项目客观评分: {PROJECT_SCORE} 分\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 结果\n\n")
        f.write("| 团队规模 | 基线(综合) | +正面记忆 | 变化 | +负面记忆 | 变化 |\n")
        f.write("|----------|-----------|----------|------|----------|------|\n")
        for team_size, data in results.items():
            f.write(f"| {team_size} | {data['baseline_comprehensive']:.0f} | {data['positive_comprehensive']:.0f} | {data['positive_effect_comprehensive']:+.0f} | {data['negative_comprehensive']:.0f} | {data['negative_effect_comprehensive']:+.0f} |\n")
    
    print(f"\n报告保存: {filename}")


if __name__ == "__main__":
    main()