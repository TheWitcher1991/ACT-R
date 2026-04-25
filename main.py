import os
import sys

from llm_client import analyze_intent, plan_action, reason
from memory import (
    activation,
    add_production,
    current_goal,
    get_best_action,
    goal_stack,
    learn_from_interaction,
    match_production,
    memory,
    pop_goal,
    productions,
    push_goal,
    retrieve,
    retrieve_by_activation,
    retrieve_semantic,
    store,
)


def tool_calc(expr):
    try:
        return eval(expr.replace("calc", "").replace("вычисли", ""))
    except:
        return "error"


def tool_search(q):
    from llm_client import chat

    messages = [
        {"role": "system", "content": "Ты — поисковая система. Дай краткий ответ."},
        {"role": "user", "content": q},
    ]
    return chat(messages)


def router(state):
    llm = state["llm"]
    ctx = state.get("context", {})

    prod = match_production(ctx)
    if prod:
        return prod["action"]

    if llm.get("needs_memory") == "yes":
        return "memory"

    if llm.get("needs_tools") == "yes":
        return "tool"

    if llm.get("complexity") in ["high", "medium"]:
        return "llm"

    return "llm"


def execute(action, input_text, context=None):
    result = None

    if action == "memory":
        results = retrieve_semantic(input_text)
        if results:
            key, score = results[0]
            mem = retrieve(key)
            if mem:
                result = mem.get("value")

    elif action == "tool":
        if "calc" in input_text.lower() or "вычисли" in input_text.lower():
            result = tool_calc(input_text)
        elif "search" in input_text.lower() or "найди" in input_text.lower():
            result = tool_search(input_text)

    elif action == "llm":
        result = reason(input_text)

    return result or "I don't know"


def reflect(input_text, result, action):
    reward = 1.0 if result not in [None, "error", "I don't know"] else 0.2

    learn_from_interaction(input_text, action, result, reward)

    return reward


def brain_step(input_text):
    print(f"\n🧠 INPUT: {input_text}")

    # Цель из стека?
    goal = current_goal()
    if goal:
        print(f"🎯 GOAL: {goal['goal']}")

    llm_state = analyze_intent(input_text)
    print(f"📊 INTENT: {llm_state}")

    best_action = get_best_action(input_text)
    if best_action:
        print(f"💡 LEARNED ACTION: {best_action}")
        llm_state["learned_action"] = best_action

    state = {"input": input_text, "llm": llm_state, "context": {"input": input_text}}

    action = router(state)
    print(f"🎯 ROUTE: {action}")

    plan = plan_action(input_text, llm_state)
    print(f"🧩 PLAN: {plan}")

    result = execute(action, input_text, state.get("context"))

    reward = reflect(input_text, result, action)

    print(f"📊 RESULT: {result}")
    print(f"⭐ REWARD: {reward}")
    print(
        f"📚 MEMORY KEYS: {len([k for k in memory.keys() if k.startswith('learned_')])} productions"
    )

    return result


def init():
    """Инициализация системы"""
    store("capital_france", "Paris", "Франция столица Париж")
    store("capital_germany", "Berlin", "Германия столица Берлин")

    add_production("calc", "вычисли", "tool")
    add_production("calc", "calc", "tool")
    add_production(" capitals ", "столица", "memory")
    add_production("find", "найди", "search")

    push_goal("answer_user", priority=10)

    print("🧠 ACT-R инициализирован")


if __name__ == "__main__":
    init()
    brain_step("Кто такой?")
    brain_step("France")
    brain_step("calc 5+7")
    brain_step("Объясни нейросети")
