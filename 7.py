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

PROJECT_SCORE = 75


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
# Population 实验任务（群体经验水平）
# ============================================================

TASK = """【项目争取任务】
你所在的公司有一个重要项目需要上级政府批准。
你的团队组成：{population}

【团队背景】
{population_description}

{memory_section}

【任务目标】
你需要制定一份行动计划，争取让项目获得批准。
请输出你的行动计划（3-5条具体行动），并说明你预计的成功概率（0-100%）。

输出格式：
行动计划：
1. ...
2. ...
预计成功率：XX%"""

POPULATION_INFO = {
    "专家团队": """专家团队特点：
- 团队成员都有10年以上行业经验
- 经历过多个类似项目，政治敏感度高
- 对政府态度有自己的判断，不会轻易被单一信息影响
- 能够独立分析风险，制定应对策略
- 团队决策理性，不易受情绪影响""",

    "新手团队": """新手团队特点：
- 团队成员经验不足，入职不到2年
- 没有经历过类似项目，政治敏感度低
- 容易被外部信息影响，对负面消息更敏感
- 需要明确指导，独立判断能力弱
- 团队容易产生焦虑，需要领导安抚""",

    "混合团队": """混合团队特点：
- 团队中有2-3名专家，其余是新手
- 专家有经验，新手需要指导
- 信息会在团队内传播，专家会影响新手
- 专家可以帮助新手理解信息、稳定情绪
- 团队整体判断介于专家和新手之间"""
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


def analyze_population_consistency(response, population):
    """检查回答是否体现了团队经验水平的特点"""
    response_lower = response.lower()
    
    if population == "专家团队":
        keywords = ["经验", "判断", "独立", "理性", "分析", "经历过", "敏感度"]
        # 专家不应该表现出焦虑或过度依赖信息
        negative = ["焦虑", "害怕", "担心", "不知所措"]
    elif population == "新手团队":
        keywords = ["指导", "安抚", "明确", "焦虑", "敏感", "担心", "经验不足"]
        negative = []
    elif population == "混合团队":
        keywords = ["专家", "新手", "传播", "影响", "平衡", "指导", "安抚"]
        negative = []
    else:
        keywords = []
        negative = []
    
    matched = sum(1 for kw in keywords if kw in response_lower)
    has_negative = any(nw in response_lower for nw in negative) if negative else False
    
    # 专家团队如果表现出焦虑，扣分
    if population == "专家团队" and has_negative:
        return False, matched
    
    return matched >= 2, matched


def calculate_comprehensive_score(rate, consistent):
    """综合评分 = 成功率 × 一致性修正"""
    score = rate
    if not consistent:
        score = score * 0.7
    return score


def run_trials(population, memory_type, trials=5):
    """测试某种群体在某种记忆条件下的表现"""
    memory_content = MEMORIES[memory_type]
    memory_section = memory_content
    
    rates = []
    consistencies = []
    
    for trial in range(trials):
        prompt = TASK.format(
            population=population,
            population_description=POPULATION_INFO[population],
            memory_section=memory_section
        )
        response = call_llm([{"role": "user", "content": prompt}], temperature=0.6)
        
        if response:
            rate = extract_success_rate(response)
            consistent, matched = analyze_population_consistency(response, population)
            rates.append(rate)
            consistencies.append(consistent)
            print(f"      Trial {trial+1}: 成功率={rate}%, 群体一致性={consistent}, 匹配词={matched}")
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
    print("Population-Conditioned Utility 验证")
    print("测试：同一记忆对不同经验水平团队的影响")
    print(f"项目客观评分: {PROJECT_SCORE} 分")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 测试 API
    print("\n测试 API...")
    if not call_llm([{"role": "user", "content": "Say OK"}]):
        print("API 连接失败")
        return
    
    results = {}
    
    for population in ["专家团队", "新手团队", "混合团队"]:
        print(f"\n{'='*50}")
        print(f"群体类型: {population}")
        print(f"{'='*50}")
        
        baseline = run_trials(population, "无记忆", trials=5)
        positive = run_trials(population, "正面记忆", trials=5)
        negative = run_trials(population, "负面记忆", trials=5)
        
        results[population] = {
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
    
    print("\n| 群体类型 | 基线(综合) | +正面记忆 | 变化 | +负面记忆 | 变化 |")
    print("|----------|-----------|----------|------|----------|------|")
    for population, data in results.items():
        print(f"| {population} | {data['baseline_comprehensive']:.0f} | {data['positive_comprehensive']:.0f} | {data['positive_effect_comprehensive']:+.0f} | {data['negative_comprehensive']:.0f} | {data['negative_effect_comprehensive']:+.0f} |")
    
    # 分析负面记忆对不同群体的影响
    negative_effects = [data['negative_effect_comprehensive'] for data in results.values()]
    print(f"\n负面记忆的边际效用范围: {min(negative_effects):+.0f} ~ {max(negative_effects):+.0f}")
    print(f"群体间最大差距: {max(negative_effects) - min(negative_effects):.0f}")
    
    if max(negative_effects) - min(negative_effects) > 20:
        print("\n✅ Population-Conditioned Utility 显著存在")
        print("   同一条负面记忆，对不同经验水平团队的影响不同")
        # 找出受影响最大的群体
        min_idx = negative_effects.index(min(negative_effects))
        populations = list(results.keys())
        print(f"   受影响最大: {populations[min_idx]} (变化{min(negative_effects):+.0f})")
    else:
        print("\n❌ Population-Conditioned Utility 不明显")
    
    # 保存报告
    filename = f"population_conditioned_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Population-Conditioned Utility 验证报告\n\n")
        f.write(f"项目客观评分: {PROJECT_SCORE} 分\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 结果\n\n")
        f.write("| 群体类型 | 基线(综合) | +正面记忆 | 变化 | +负面记忆 | 变化 |\n")
        f.write("|----------|-----------|----------|------|----------|------|\n")
        for population, data in results.items():
            f.write(f"| {population} | {data['baseline_comprehensive']:.0f} | {data['positive_comprehensive']:.0f} | {data['positive_effect_comprehensive']:+.0f} | {data['negative_comprehensive']:.0f} | {data['negative_effect_comprehensive']:+.0f} |\n")
    
    print(f"\n报告保存: {filename}")


if __name__ == "__main__":
    main()