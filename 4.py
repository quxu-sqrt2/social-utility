# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time
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
# 任务2：Role-Conditioned Utility
# ============================================================

TASK2 = """你在一家餐厅工作。餐厅突然来了很多客人，需要快速服务。

你的角色是：{role_desc}

你要决定先做什么。请根据你的角色，制定你的行动优先级。"""

TASK2_ROLES = {
    "chef": "厨师：负责做菜，不能离开厨房",
    "waiter": "服务员：负责点菜、上菜、收桌",
    "manager": "经理：负责协调、分配任务",
    "cashier": "收银员：负责收钱、不能出错"
}

TASK2_MEMORY = """【成功经验】
不同角色应该有不同的优先级：

厨师：优先做最快的菜，让服务员先上已有的菜。
服务员：优先安抚等待的客人，然后点菜，最后收桌。
经理：优先分配任务，然后处理投诉，最后自己也帮忙。
收银员：优先保证收钱准确，然后加快速度，最后帮忙指路。"""

TASK2_BAD_MEMORY = """【错误经验】
所有角色都做同一件事：去厨房帮忙做菜。
结果：厨师觉得被打扰，服务员没点菜，经理没人协调，收银台排队没人管。"""


def analyze_task2(response, role):
    response_lower = response.lower()
    keywords = {
        "chef": ["做菜", "厨房", "出菜", "烹饪", "快菜"],
        "waiter": ["点菜", "上菜", "客人", "安抚", "服务"],
        "manager": ["协调", "分配", "处理", "安排", "调度"],
        "cashier": ["收钱", "准确", "收银", "排队", "找零"]
    }
    matched = [kw for kw in keywords.get(role, []) if kw in response_lower]
    return len(matched) >= 1, matched


def run_task2(trials=3):
    print("\n" + "="*60)
    print("任务2: Role-Conditioned Utility")
    print("="*60)
    
    results = {}
    
    for role, role_desc in TASK2_ROLES.items():
        print(f"\n  测试角色: {role}")
        
        results[role] = {"with_good": 0, "with_bad": 0, "total": trials}
        
        for trial in range(trials):
            prompt = TASK2.format(role_desc=role_desc)
            
            # 好记忆
            full_prompt = f"{prompt}\n\n【参考经验】\n{TASK2_MEMORY}\n\n请根据你的角色制定行动策略。输出要具体。"
            response = call_llm([{"role": "user", "content": full_prompt}], temperature=0.5)
            if response:
                success, matched = analyze_task2(response, role)
                if success:
                    results[role]["with_good"] += 1
                print(f"    Trial {trial+1}: 好记忆={'✓' if success else '✗'} ({matched[:2] if matched else '无匹配'})")
            
            time.sleep(0.5)
            
            # 坏记忆
            full_prompt = f"{prompt}\n\n【参考经验】\n{TASK2_BAD_MEMORY}\n\n请根据你的角色制定行动策略。输出要具体。"
            response = call_llm([{"role": "user", "content": full_prompt}], temperature=0.5)
            if response:
                success, matched = analyze_task2(response, role)
                if success:
                    results[role]["with_bad"] += 1
                print(f"    Trial {trial+1}: 坏记忆={'✓' if success else '✗'} ({matched[:2] if matched else '无匹配'})")
            
            time.sleep(0.5)
        
        good_rate = results[role]["with_good"] / trials
        bad_rate = results[role]["with_bad"] / trials
        print(f"    结果: 好记忆={good_rate:.0%}, 坏记忆={bad_rate:.0%}, 效应={good_rate - bad_rate:+.0%}")
    
    return results


# ============================================================
# 任务3：Team-Conditioned Utility
# ============================================================

TASK3 = """你参与一个软件开发项目，需要做一个紧急修复。

团队规模：{team_desc}

你要决定如何组织工作。请根据团队规模，制定你的沟通和分工策略。"""

TASK3_TEAMS = {
    "solo": "只有你一个人，没有队友",
    "pair": "你和1个搭档，共2人",
    "small": "你和4个队友，共5人",
    "large": "你和9个队友，共10人"
}

TASK3_MEMORY = """【成功经验】
不同团队规模要用不同方式：

一个人：自己全做，不需要沟通，按自己节奏。
2人：直接沟通，一人做前端一人做后端，随时同步。
5人：开短会分工，用群聊同步，每天站会。
10人：分小组，组长汇报，用项目管理工具，定期会议。"""

TASK3_BAD_MEMORY = """【错误经验】
不管多少人，都开全员大会讨论每一个细节。
结果：一个人时浪费时间，2人时还行，5人时效率低，10人时完全混乱。"""


def analyze_task3(response, team_type):
    response_lower = response.lower()
    keywords = {
        "solo": ["自己", "个人", "单独", "独立", "一个人"],
        "pair": ["搭档", "两人", "直接", "同步", "一对一"],
        "small": ["分工", "群聊", "站会", "小会", "5人"],
        "large": ["分组", "小组", "汇报", "工具", "10人", "组长"]
    }
    matched = [kw for kw in keywords.get(team_type, []) if kw in response_lower]
    return len(matched) >= 1, matched


def run_task3(trials=3):
    print("\n" + "="*60)
    print("任务3: Team-Conditioned Utility")
    print("="*60)
    
    results = {}
    
    for team, team_desc in TASK3_TEAMS.items():
        print(f"\n  测试团队: {team}")
        
        results[team] = {"with_good": 0, "with_bad": 0, "total": trials}
        
        for trial in range(trials):
            prompt = TASK3.format(team_desc=team_desc)
            
            # 好记忆
            full_prompt = f"{prompt}\n\n【参考经验】\n{TASK3_MEMORY}\n\n请根据团队规模制定策略。输出要具体。"
            response = call_llm([{"role": "user", "content": full_prompt}], temperature=0.5)
            if response:
                success, matched = analyze_task3(response, team)
                if success:
                    results[team]["with_good"] += 1
                print(f"    Trial {trial+1}: 好记忆={'✓' if success else '✗'} ({matched[:2] if matched else '无匹配'})")
            
            time.sleep(0.5)
            
            # 坏记忆
            full_prompt = f"{prompt}\n\n【参考经验】\n{TASK3_BAD_MEMORY}\n\n请根据团队规模制定策略。输出要具体。"
            response = call_llm([{"role": "user", "content": full_prompt}], temperature=0.5)
            if response:
                success, matched = analyze_task3(response, team)
                if success:
                    results[team]["with_bad"] += 1
                print(f"    Trial {trial+1}: 坏记忆={'✓' if success else '✗'} ({matched[:2] if matched else '无匹配'})")
            
            time.sleep(0.5)
        
        good_rate = results[team]["with_good"] / trials
        bad_rate = results[team]["with_bad"] / trials
        print(f"    结果: 好记忆={good_rate:.0%}, 坏记忆={bad_rate:.0%}, 效应={good_rate - bad_rate:+.0%}")
    
    return results


# ============================================================
# 任务4：Population-Conditioned Utility
# ============================================================

TASK4 = """你要给一个团队做培训，教他们使用新软件。

团队的背景：{population_desc}

请根据团队的经验水平，设计你的培训方法。"""

TASK4_POPULATIONS = {
    "expert": "全是技术专家：经验丰富，学习快，但容易不耐烦",
    "beginner": "全是新手：完全没接触过，需要详细讲解",
    "mixed": "混合水平：有专家也有新手，水平差距大",
    "resistant": "抗拒型：不想学新东西，觉得旧软件够用"
}

TASK4_MEMORY = """【成功经验】
不同经验水平要用不同培训方法：

专家：讲核心功能和高级技巧，快速过基础，给挑战性任务。
新手：从零开始，一步步演示，给练习机会，耐心解答。
混合：分开培训或分组，专家带新手，各自有收获。
抗拒型：先讲好处和价值，用小成果说服，给简单上手任务。"""

TASK4_BAD_MEMORY = """【错误经验】
不管什么水平，都从头讲基础，一视同仁。
结果：专家觉得无聊，新手跟不上，混合时专家嫌弃新手，抗拒型直接不听。"""


def analyze_task4(response, pop_type):
    response_lower = response.lower()
    keywords = {
        "expert": ["高级", "核心", "快速", "挑战", "技巧"],
        "beginner": ["基础", "详细", "演示", "练习", "耐心", "零基础"],
        "mixed": ["分开", "分组", "混合", "各取所需", "水平差"],
        "resistant": ["好处", "价值", "说服", "小成果", "简单"]
    }
    matched = [kw for kw in keywords.get(pop_type, []) if kw in response_lower]
    return len(matched) >= 1, matched


def run_task4(trials=3):
    print("\n" + "="*60)
    print("任务4: Population-Conditioned Utility")
    print("="*60)
    
    results = {}
    
    for pop, pop_desc in TASK4_POPULATIONS.items():
        print(f"\n  测试群体: {pop}")
        
        results[pop] = {"with_good": 0, "with_bad": 0, "total": trials}
        
        for trial in range(trials):
            prompt = TASK4.format(population_desc=pop_desc)
            
            # 好记忆
            full_prompt = f"{prompt}\n\n【参考经验】\n{TASK4_MEMORY}\n\n请根据团队背景制定培训方法。输出要具体。"
            response = call_llm([{"role": "user", "content": full_prompt}], temperature=0.5)
            if response:
                success, matched = analyze_task4(response, pop)
                if success:
                    results[pop]["with_good"] += 1
                print(f"    Trial {trial+1}: 好记忆={'✓' if success else '✗'} ({matched[:2] if matched else '无匹配'})")
            
            time.sleep(0.5)
            
            # 坏记忆
            full_prompt = f"{prompt}\n\n【参考经验】\n{TASK4_BAD_MEMORY}\n\n请根据团队背景制定培训方法。输出要具体。"
            response = call_llm([{"role": "user", "content": full_prompt}], temperature=0.5)
            if response:
                success, matched = analyze_task4(response, pop)
                if success:
                    results[pop]["with_bad"] += 1
                print(f"    Trial {trial+1}: 坏记忆={'✓' if success else '✗'} ({matched[:2] if matched else '无匹配'})")
            
            time.sleep(0.5)
        
        good_rate = results[pop]["with_good"] / trials
        bad_rate = results[pop]["with_bad"] / trials
        print(f"    结果: 好记忆={good_rate:.0%}, 坏记忆={bad_rate:.0%}, 效应={good_rate - bad_rate:+.0%}")
    
    return results


# ============================================================
# 主程序
# ============================================================

def main():
    print("="*70)
    print("剩余三个维度社会效用验证实验")
    print("Role-Conditioned + Team-Conditioned + Population-Conditioned")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 测试 API
    print("\n测试 API...")
    if not call_llm([{"role": "user", "content": "Say OK"}]):
        print("API 连接失败")
        return
    
    all_results = {}
    
    # 任务2：Role-Conditioned
    all_results["role"] = run_task2(trials=3)
    
    # 任务3：Team-Conditioned
    all_results["team"] = run_task3(trials=3)
    
    # 任务4：Population-Conditioned
    all_results["population"] = run_task4(trials=3)
    
    # 生成总结报告
    print("\n" + "="*70)
    print("实验总结")
    print("="*70)
    
    for category, results in all_results.items():
        print(f"\n{category}:")
        gains = []
        for cond_name, data in results.items():
            gain = (data["with_good"] / data["total"]) - (data["with_bad"] / data["total"])
            gains.append(gain)
            print(f"  {cond_name}: 效应={gain:+.0%}")
        
        max_gain = max(gains)
        min_gain = min(gains)
        gap = max_gain - min_gain
        print(f"  效应范围: {min_gain:+.0%} ~ {max_gain:+.0%}")
        print(f"  最大差异: {gap:.0%}")
        
        if gap > 0.3:
            print(f"  ✅ {category} 社会效用显著存在")
        elif gap > 0.15:
            print(f"  ⚠️ {category} 社会效用存在但不显著")
        else:
            print(f"  ❌ {category} 社会效用不明显")
    
    # 保存报告
    filename = f"remaining_tasks_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 剩余三个维度社会效用验证报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for category, results in all_results.items():
            f.write(f"## {category}\n\n")
            f.write("| 条件 | 好记忆成功率 | 坏记忆成功率 | 效应 |\n")
            f.write("|------|-------------|-------------|------|\n")
            for cond_name, data in results.items():
                good_rate = data["with_good"] / data["total"]
                bad_rate = data["with_bad"] / data["total"]
                effect = good_rate - bad_rate
                f.write(f"| {cond_name} | {good_rate:.0%} | {bad_rate:.0%} | {effect:+.0%} |\n")
            f.write("\n")
    
    print(f"\n报告已保存到: {filename}")


if __name__ == "__main__":
    main()