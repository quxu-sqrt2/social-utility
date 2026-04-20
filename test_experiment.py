import os
import re
import random
import requests
import json
from typing import Tuple, Dict, List

# ===================== 配置项 =====================
API_URL = "https://az.gptplus5.com/v1/chat/completions"
API_KEY = "sk-s9MajX5BAQ66OHIo9XOcgjYoxH9bX7aTkebTjJdoW5hn4kzm"
MODEL = "gpt-4o-mini"

# ===================== 调试模式 =====================
DEBUG = True

# ===================== 辅助函数 =====================
def debug_print(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

# ===================== 模拟环境：不依赖textworld =====================
class TextWorldEnv:
    def __init__(self):
        self.current_task = None
        
    def reset(self, task=None) -> Tuple[str, Dict]:
        """重置环境：返回模拟的观察结果"""
        self.current_task = task
        obs_text = f"你在一个厨房里，你的任务是：{task}"
        info = {"task": task, "admissible_commands": ["examine", "take", "put", "clean", "heat", "open", "close", "look"]}
        return obs_text, info
    
    def step(self, action) -> Tuple[str, float, bool, Dict]:
        """执行动作：模拟环境反馈"""
        action_str = str(action)
        task = self.current_task
        reward = 0.0
        done = False
        
        if any(keyword in action_str.lower() for keyword in task.split()):
            reward = 1.0
            if sum(1 for keyword in task.split() if keyword in action_str.lower()) >= 2:
                done = True
        
        obs_text = f"你执行了动作：{action_str}"
        return obs_text, reward, done, {}
    
    def close(self):
        pass

# ===================== LLM 调用 =====================
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
        return "look"

def parse_action(out):
    patterns = [r"(take|put|go|clean|heat|open|close|look|examine)\s+.*"]
    for p in patterns:
        match = re.search(p, out, re.I)
        if match:
            return match.group(0).strip()
    return "look"

# ===================== 角色记忆 =====================
ROLE_SPECIFIC_MEM = {
    "chef":     "你是厨师，只做：加热食物、使用微波炉、处理食材",
    "waiter":   "你是服务员，只做：取放物品、摆放、收纳",
    "cleaner":  "你是清洁工，只做：清洗物品、清洁"
}

# ===================== 执行任务 =====================
def run_task(env, role, memory, task, max_steps=5):
    obs, info = env.reset(task)
    done = False
    steps = 0
    total_reward = 0
    actions_taken = []
    
    print(f"\n[任务] {task}")
    print(f"[角色] {role}")
    print(f"[记忆] {memory}")
    
    while not done and steps < max_steps:
        prompt = f"""任务：{task}\n当前观察：{obs}\n身份：{role}\n规则：{memory}\n\n只输出动作，不要解释！\n动作："""
        
        action = parse_action(call_llm(prompt))
        actions_taken.append(action)
        print(f"  步骤{steps+1}: {action}")
        
        try:
            obs, reward, done, info = env.step(action)
            total_reward += reward
            print(f"    奖励: {reward:.2f}, 总分: {total_reward:.2f}")
        except Exception as e:
            print(f"    执行失败: {e}")
            break
        
        steps += 1
    
    success = done or total_reward > 0
    print(f"\n{success}")
    return success, total_reward, actions_taken

# ===================== 主函数 =====================
if __name__ == "__main__":
    debug_print("开始测试...")
    print("开始测试...")
    
    # 测试LLM连接
    debug_print("测试LLM连接...")
    print("测试LLM连接...")
    test_prompt = "你好"
    try:
        debug_print(f"发送测试请求到: {API_URL}")
        response = call_llm(test_prompt)
        debug_print(f"LLM响应: {response}")
        print(f"LLM响应: {response}")
    except Exception as e:
        debug_print(f"LLM连接失败: {e}")
        print(f"LLM连接失败: {e}")
    
    # 创建环境
    debug_print("创建环境...")
    env = TextWorldEnv()
    debug_print("环境创建成功")
    print("环境创建成功")
    
    # 测试匹配记忆
    debug_print("测试匹配记忆...")
    print("\n=== 测试匹配记忆 ===")
    task1 = "clean the dirty mug"
    role1 = "cleaner"
    memory1 = ROLE_SPECIFIC_MEM[role1]
    print(f"任务: {task1}")
    print(f"角色: {role1}")
    print(f"记忆: {memory1}")
    success1, reward1, actions1 = run_task(env, role1, memory1, task1)
    debug_print(f"匹配记忆测试结果: 成功={success1}, 奖励={reward1}, 动作={actions1}")
    
    # 测试不匹配记忆
    debug_print("测试不匹配记忆...")
    print("\n=== 测试不匹配记忆 ===")
    task2 = "clean the dirty mug"
    role2 = "cleaner"
    memory2 = ROLE_SPECIFIC_MEM["chef"]  # 不匹配
    print(f"任务: {task2}")
    print(f"角色: {role2}")
    print(f"记忆: {memory2}")
    success2, reward2, actions2 = run_task(env, role2, memory2, task2)
    debug_print(f"不匹配记忆测试结果: 成功={success2}, 奖励={reward2}, 动作={actions2}")
    
    # 结果比较
    debug_print("比较结果...")
    print("\n=== 结果比较 ===")
    print(f"匹配记忆: 成功={success1}, 奖励={reward1}")
    print(f"不匹配记忆: 成功={success2}, 奖励={reward2}")
    
    if success1 and not success2 or reward1 > reward2:
        print("\n存在记忆社会效用：匹配记忆时表现更好")
    else:
        print("\n未发现明显的记忆社会效用")
    
    env.close()
    debug_print("测试完成！")
    print("\n测试完成！")
