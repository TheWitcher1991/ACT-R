import math
import random
import time
from llm_client import analyze_intent, plan_action, reason

# =========================
# 🧠 MEMORY
# =========================

memory = {
    "capital_france": {"value": "Paris", "uses": 5},
    "capital_germany": {"value": "Berlin", "uses": 3},
}

working_memory = []


# =========================
# ⚙️ TOOLS
# =========================


def tool_calc(expr):
    try:
        return eval(expr.replace("calc", "").replace("вычисли", ""))
    except:
        return "error"


def tool_search(q):
    from llm_client import chat, client
    
    system_prompt = """Ты - поисковая система. Дай краткий ответ на вопрос пользователя."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": q}
    ]
    
    return chat(messages)


# =========================
# 🧠 MEMORY CORE
# =========================


def retrieve(key):
    return memory.get(key, {"value": None})


def update_memory(key, value):
    memory[key] = {"value": value, "uses": memory.get(key, {}).get("uses", 0) + 1}


# =========================
# 🧠 ACT-R ROUTER (intelligent)
# =========================


def router(state):
    llm = state["llm"]

    if llm.get("needs_memory") == "yes":
        return "memory"

    if llm.get("needs_tools") == "yes":
        return "tool"

    if llm.get("complexity") in ["high", "medium"]:
        return "llm"

    return "llm"


# =========================
# 🧠 EXECUTION ENGINE
# =========================


def execute(action, input_text):

    if action == "memory":
        key = f"capital_{input_text}"
        mem = retrieve(key)
        return mem["value"]

    if action == "tool":
        if "calc" in input_text.lower() or "вычисли" in input_text.lower():
            return tool_calc(input_text)
        if "search" in input_text.lower() or "найди" in input_text.lower() or "поиск" in input_text.lower():
            return tool_search(input_text)

    if action == "llm":
        return reason(input_text)

    return "I don't know"


# =========================
# 🧠 REFLECTION (CRITICAL PART)
# =========================


def reflect(input_text, result, action):

    reward = 1.0 if result not in [None, "error", "I don't know"] else 0.2

    if reward > 0.5:
        update_memory(f"last_success_{input_text}", result)

    return reward


# =========================
# 🧠 MAIN BRAIN LOOP
# =========================


def brain_step(input_text):

    print(f"\n🧠 INPUT: {input_text}")

    llm_state = analyze_intent(input_text)
    print(f"📊 INTENT: {llm_state}")

    state = {"input": input_text, "llm": llm_state}

    action = router(state)

    print(f"🎯 ROUTE: {action}")

    plan = plan_action(input_text, llm_state)
    print(f"🧩 PLAN: {plan}")

    result = execute(action, input_text)

    reward = reflect(input_text, result, action)

    print(f"📊 RESULT: {result}")
    print(f"⭐ REWARD: {reward}")

    working_memory.append(
        {"input": input_text, "action": action, "result": result, "reward": reward}
    )

    return result


# =========================
# 🚀 RUN LOOP
# =========================

if __name__ == "__main__":
    brain_step("Кто такой?")
    brain_step("France")
    brain_step("Germany")
    brain_step("search ai models")
    brain_step("calc 5+7")
    brain_step("Объясни нейросети")