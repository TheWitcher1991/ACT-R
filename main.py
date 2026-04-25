import os
import sys

from llm_client import analyze_intent, plan_action, reason
from memory import (
    activation,
    add_production,
    add_skill,
    attend,
    attentional_capture,
    calculate_salience,
    current_goal,
    get_all_skills_sorted,
    get_attention_load,
    get_best_action,
    get_focused,
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
    retrieve_skill,
    shift_attention,
    store,
    strengthen_skill,
    weaken_skill,
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
    input_text = state.get("input", "")

    skill = retrieve_skill(input_text)
    if skill:
        state["learned_skill"] = skill
        return skill["action"]

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


def reflect(input_text, result, action, state=None):
    reward = 1.0 if result not in [None, "error", "I don't know"] else 0.2

    learn_from_interaction(input_text, action, result, reward)

    if state and reward > 0.7:
        skill = state.get("learned_skill")
        if skill:
            strengthen_skill(skill["name"])
        elif action:
            add_skill(
                name=f"skill_{input_text[:20]}", condition=input_text, action=action
            )

    if state and reward < 0.3:
        skill = state.get("learned_skill")
        if skill:
            weaken_skill(skill["name"])

    return reward


emotional_state = {
    "arousal": 0.5,
    "valence": 0.5,
    "dominance": 0.5,
}

working_memory: list = []


def export_to_markdown():
    import json
    from datetime import datetime

    md = f"# ACT-R Session\n\n**{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**\n\n"

    md += "## Emotional State\n"
    md += f"- Valence: {emotional_state['valence']:.2f}\n"
    md += f"- Arousal: {emotional_state['arousal']:.2f}\n"
    md += f"- Dominance: {emotional_state['dominance']:.2f}\n\n"

    md += "## Memory Stats\n"
    md += f"- Declarative: {len([k for k in memory.keys() if k.startswith('learned_')])} facts\n"
    md += f"- Procedural: {len(get_all_skills_sorted())} skills\n"
    md += f"- Attention: {get_attention_load()}/7\n\n"

    md += "## Recent Inputs\n"
    for i, wm in enumerate(working_memory):
        md += f"{i + 1}. **{wm['input']}** → {wm['result']}\n"

    return md


def save_session(filename="session.md"):
    md = export_to_markdown()
    with open(filename, "w") as f:
        f.write(md)


def update_emotions(reward: float):
    emotional_state["valence"] = 0.3 + reward * 0.7
    emotional_state["arousal"] = min(1.0, emotional_state["arousal"] + 0.1)


def brain_step(input_text):
    print(f"\n🧠 INPUT: {input_text}")

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

    reward = reflect(input_text, result, action, state)

    attentional_capture(result)
    update_emotions(reward)

    working_memory.append({"input": input_text, "result": result})
    if len(working_memory) > 5:
        working_memory.pop(0)

    focused = get_focused()
    emo = emotional_state
    print(f"📊 RESULT: {result}")
    print(f"⭐ REWARD: {reward}")
    print(f"💭 EMOTIONS: valence={emo['valence']:.2f}, arousal={emo['arousal']:.2f}")
    skills = get_all_skills_sorted()
    load = get_attention_load()
    print(
        f"📚 MEMORY: {len([k for k in memory.keys() if k.startswith('learned_')])} facts, {len(skills)} skills, attention {load}/7"
    )

    return result


def init():
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
    save_session()
    print("\n📝 Session saved to session.md")
