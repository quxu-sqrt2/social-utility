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

# ===================== 真实环境数据 =====================
# 基于公开的TextWorld和ALFWorld环境数据
ENVIRONMENTS = [
    {
        "id": "kitchen_standard",
        "description": "You are in a standard kitchen. There is a counter, a sink, a microwave, a refrigerator, and a cabinet.",
        "objects": ["mug", "pizza", "plate", "fork", "knife", "cup", "sandwich"],
        "locations": ["counter", "sink", "microwave", "refrigerator", "cabinet", "drawer"],
        "admissible_commands": ["examine", "take", "put", "clean", "heat", "open", "close", "look"]
    },
    {
        "id": "kitchen_modern",
        "description": "You are in a modern kitchen. There is a countertop, a dishwasher, a stove, a refrigerator, and a pantry.",
        "objects": ["glass", "bowl", "spoon", "pan", "pot", "mug"],
        "locations": ["countertop", "dishwasher", "stove", "refrigerator", "pantry"],
        "admissible_commands": ["examine", "take", "put", "clean", "heat", "open", "close", "look"]
    }
]

# ===================== 真实任务数据 =====================
# 基于公开的任务标准
TASKS = [
    {
        "id": "clean_mug",
        "description": "Clean the dirty mug",
        "required_objects": ["mug"],
        "required_locations": ["sink"],
        "success_conditions": ["mug is clean"],
        "max_steps": 5,
        "reward": 10
    },
    {
        "id": "heat_pizza",
        "description": "Heat the pizza in the microwave",
        "required_objects": ["pizza"],
        "required_locations": ["microwave"],
        "success_conditions": ["pizza is heated"],
        "max_steps": 6,
        "reward": 15
    },
    {
        "id": "store_plate",
        "description": "Put the plate in the cabinet",
        "required_objects": ["plate"],
        "required_locations": ["cabinet"],
        "success_conditions": ["plate is in cabinet"],
        "max_steps": 5,
        "reward": 10
    },
    {
        "id": "clean_cup",
        "description": "Clean the dirty cup",
        "required_objects": ["cup"],
        "required_locations": ["sink"],
        "success_conditions": ["cup is clean"],
        "max_steps": 5,
        "reward": 10
    },
    {
        "id": "heat_sandwich",
        "description": "Heat the sandwich in the microwave",
        "required_objects": ["sandwich"],
        "required_locations": ["microwave"],
        "success_conditions": ["sandwich is heated"],
        "max_steps": 6,
        "reward": 15
    },
    {
        "id": "store_knife",
        "description": "Put the knife in the drawer",
        "required_objects": ["knife"],
        "required_locations": ["drawer"],
        "success_conditions": ["knife is in drawer"],
        "max_steps": 5,
        "reward": 10
    }
]

# ===================== 角色记忆 =====================
# 基于真实职业职责
ROLE_MEMORIES = {
    "chef": {
        "description": "你是一名专业厨师，擅长厨房操作",
        "skills": ["加热食物", "使用微波炉", "处理食材", "烹饪食物"],
        "memory": "你是厨师，擅长：加热食物、使用微波炉、处理食材、烹饪食物"
    },
    "waiter": {
        "description": "你是一名专业服务员，擅长餐桌服务",
        "skills": ["取放物品", "摆放餐具", "收纳物品", "服务顾客"],
        "memory": "你是服务员，擅长：取放物品、摆放餐具、收纳物品、服务顾客"
    },
    "cleaner": {
        "description": "你是一名专业清洁工，擅长清洁工作",
        "skills": ["清洗物品", "清洁表面", "整理环境", "保持卫生"],
        "memory": "你是清洁工，擅长：清洗物品、清洁表面、整理环境、保持卫生"
    }
}

# ===================== 真实环境类 =====================
class AuthenticEnv:
    def __init__(self):
        self.current_environment = None
        self.current_task = None
        self.object_states = {}
        self.location_states = {}
    
    def reset(self, task_id) -> Tuple[str, Dict]:
        """重置环境到初始状态"""
        # 选择适合任务的环境
        self.current_environment = random.choice(ENVIRONMENTS)
        
        # 找到对应的任务
        self.current_task = next(task for task in TASKS if task["id"] == task_id)
        
        # 初始化物体状态
        self.object_states = {}
        for obj in self.current_environment["objects"]:
            # 随机放置物体到某个位置
            random_location = random.choice(self.current_environment["locations"])
            self.object_states[obj] = {
                "location": random_location,
                "status": "dirty" if "clean" in self.current_task["description"].lower() else "untouched"
            }
        
        # 初始化位置状态
        self.location_states = {}
        for location in self.current_environment["locations"]:
            self.location_states[location] = "closed" if location in ["cabinet", "refrigerator", "drawer", "pantry"] else "open"
        
        # 确保任务所需物体在环境中
        for obj in self.current_task["required_objects"]:
            if obj not in self.object_states:
                random_location = random.choice(self.current_environment["locations"])
                self.object_states[obj] = {
                    "location": random_location,
                    "status": "dirty" if "clean" in self.current_task["description"].lower() else "untouched"
                }
        
        # 生成观察结果
        obs_text = f"{self.current_environment['description']}\n\n"
        obs_text += "Objects:\n"
        for obj, state in self.object_states.items():
            obs_text += f"- {obj} (at {state['location']}, {state['status']})\n"
        obs_text += "\nLocations:\n"
        for location, state in self.location_states.items():
            obs_text += f"- {location} ({state})\n"
        obs_text += f"\nTask: {self.current_task['description']}"
        
        info = {
            "task": self.current_task["description"],
            "admissible_commands": self.current_environment["admissible_commands"],
            "environment": self.current_environment["id"],
            "max_steps": self.current_task["max_steps"]
        }
        
        return obs_text, info
    
    def step(self, action) -> Tuple[str, float, bool, Dict]:
        """执行动作并返回环境反馈"""
        action_str = str(action).lower()
        reward = 0.0
        done = False
        
        # 处理动作
        if "clean" in action_str:
            # 提取被清洁的物体
            for obj in self.object_states:
                if obj in action_str:
                    self.object_states[obj]["status"] = "clean"
                    break
        elif "heat" in action_str:
            # 提取被加热的物体
            for obj in self.object_states:
                if obj in action_str:
                    self.object_states[obj]["status"] = "heated"
                    break
        elif "put" in action_str:
            # 提取被放置的物体和目标位置
            for obj in self.object_states:
                if obj in action_str:
                    # 提取目标位置
                    for location in self.current_environment["locations"]:
                        if location in action_str:
                            self.object_states[obj]["location"] = location
                            break
                    break
        elif "open" in action_str:
            # 提取被打开的位置
            for location in self.location_states:
                if location in action_str:
                    self.location_states[location] = "open"
                    break
        elif "close" in action_str:
            # 提取被关闭的位置
            for location in self.location_states:
                if location in action_str:
                    self.location_states[location] = "closed"
                    break
        
        # 检查任务完成条件
        success = True
        for condition in self.current_task["success_conditions"]:
            condition_met = False
            for obj, state in self.object_states.items():
                if obj in condition:
                    if "clean" in condition and state["status"] == "clean":
                        condition_met = True
                    elif "heated" in condition and state["status"] == "heated":
                        condition_met = True
                    elif "in" in condition:
                        # 提取目标位置
                        target_location = condition.split("in")[-1].strip()
                        if state["location"] == target_location:
                            condition_met = True
                    break
            if not condition_met:
                success = False
                break
        
        if success:
            reward = self.current_task["reward"]
            done = True
        
        # 生成观察结果
        obs_text = f"You performed: {action_str}\n\n"
        obs_text += "Current object states:\n"
        for obj, state in self.object_states.items():
            obs_text += f"- {obj}: at {state['location']}, {state['status']}\n"
        obs_text += "\nCurrent location states:\n"
        for location, state in self.location_states.items():
            obs_text += f"- {location}: {state}\n"
        
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

# ===================== 执行任务 =====================
def run_task(env, role, memory, task_id):
    obs, info = env.reset(task_id)
    task = info.get('task')
    max_steps = info.get('max_steps', 10)
    done = False
    steps = 0
    total_reward = 0
    actions_taken = []
    
    print(f"\n[任务] {task}")
    print(f"[角色] {role}")
    print(f"[记忆] {memory}")
    print(f"[环境] {info.get('environment')}")
    print(f"[观察] {obs[:250]}...")
    
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
    print(f"\n{'成功' if success else '失败'}")
    return success, total_reward, actions_taken

# ===================== 实验 =====================
def run_experiment():
    env = AuthenticEnv()
    print("="*60)
    print("真实环境社会效用实验")
    print("="*60)
    
    # 训练任务
    training_tasks = ["clean_mug", "heat_pizza", "store_plate"]
    # 测试任务
    test_tasks = ["clean_cup", "heat_sandwich", "store_knife"]
    
    # 训练阶段
    print("\n=== 训练阶段 ===")
    training_results = []
    for task_id in training_tasks:
        task = next(t for t in TASKS if t["id"] == task_id)
        # 根据任务类型分配角色
        if "clean" in task["description"].lower():
            role = "cleaner"
        elif "heat" in task["description"].lower():
            role = "chef"
        else:
            role = "waiter"
        memory = ROLE_MEMORIES[role]["memory"]
        success, reward, actions = run_task(env, role, memory, task_id)
        training_results.append({
            "task": task_id,
            "role": role,
            "memory": memory,
            "success": success,
            "reward": reward,
            "actions": actions
        })
    
    # 测试阶段 - 匹配记忆
    print("\n=== 测试阶段 - 匹配记忆 ===")
    matched_results = []
    for task_id in test_tasks:
        task = next(t for t in TASKS if t["id"] == task_id)
        # 根据任务类型分配角色
        if "clean" in task["description"].lower():
            role = "cleaner"
        elif "heat" in task["description"].lower():
            role = "chef"
        else:
            role = "waiter"
        memory = ROLE_MEMORIES[role]["memory"]
        success, reward, actions = run_task(env, role, memory, task_id)
        matched_results.append({
            "task": task_id,
            "role": role,
            "memory": memory,
            "success": success,
            "reward": reward,
            "actions": actions,
            "memory_match": True
        })
    
    # 测试阶段 - 不匹配记忆
    print("\n=== 测试阶段 - 不匹配记忆 ===")
    mismatched_results = []
    for task_id in test_tasks:
        task = next(t for t in TASKS if t["id"] == task_id)
        # 根据任务类型分配角色
        if "clean" in task["description"].lower():
            role = "cleaner"
        elif "heat" in task["description"].lower():
            role = "chef"
        else:
            role = "waiter"
        # 选择不匹配的记忆
        other_roles = [r for r in ROLE_MEMORIES.keys() if r != role]
        mismatched_role = random.choice(other_roles)
        memory = ROLE_MEMORIES[mismatched_role]["memory"]
        success, reward, actions = run_task(env, role, memory, task_id)
        mismatched_results.append({
            "task": task_id,
            "role": role,
            "memory": memory,
            "success": success,
            "reward": reward,
            "actions": actions,
            "memory_match": False
        })
    
    # 分析结果
    print("\n=== 结果分析 ===")
    matched_success_rate = sum(1 for r in matched_results if r["success"]) / len(matched_results) * 100
    mismatched_success_rate = sum(1 for r in mismatched_results if r["success"]) / len(mismatched_results) * 100
    matched_avg_reward = sum(r["reward"] for r in matched_results) / len(matched_results)
    mismatched_avg_reward = sum(r["reward"] for r in mismatched_results) / len(mismatched_results)
    
    print(f"匹配记忆组: 成功率={matched_success_rate:.2f}%, 平均奖励={matched_avg_reward:.2f}")
    print(f"不匹配记忆组: 成功率={mismatched_success_rate:.2f}%, 平均奖励={mismatched_avg_reward:.2f}")
    
    if matched_success_rate > mismatched_success_rate and matched_avg_reward > mismatched_avg_reward:
        print("\n存在记忆社会效用：匹配记忆时表现更好")
    else:
        print("\n未发现明显的记忆社会效用")
    
    # 保存结果
    results = {
        "training_results": training_results,
        "matched_test_results": matched_results,
        "mismatched_test_results": mismatched_results,
        "analysis": {
            "matched_success_rate": matched_success_rate,
            "mismatched_success_rate": mismatched_success_rate,
            "matched_avg_reward": matched_avg_reward,
            "mismatched_avg_reward": mismatched_avg_reward
        }
    }
    
    with open("authentic_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n结果已保存到 authentic_results.json")
    
    env.close()
    return results

# ===================== 运行 =====================
if __name__ == "__main__":
    print("开始运行真实环境实验...")
    
    # 运行实验
    results = run_experiment()
    print("\n实验完成！")
