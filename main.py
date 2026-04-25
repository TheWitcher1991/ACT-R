import math
import random
import time

memory = {
    "capital_france": {
        "value": "Paris",
        "base_activation": 0.9,
        "uses": 5,
        "last_used": time.time(),
    },
    "capital_germany": {
        "value": "Berlin",
        "base_activation": 0.7,
        "uses": 3,
        "last_used": time.time(),
    },
}


goal_stack = []


def push_goal(g):
    goal_stack.append(g)


def pop_goal():
    return goal_stack.pop() if goal_stack else None


def current_goal():
    return goal_stack[-1] if goal_stack else None


def tool_calc(expr):
    try:
        return eval(expr.replace("calc", "").strip())
    except:
        return "error"


def tool_search(q):
    return f"[search result] {q}"


TOOLS = {
    "calc": tool_calc,
    "search": tool_search,
}


def decay(chunk):
    age = time.time() - chunk["last_used"]
    return math.exp(-age / 40)


def activation(chunk):
    return (chunk["base_activation"] + math.log(chunk["uses"] + 1)) * decay(
        chunk
    ) + random.uniform(-0.1, 0.1)


def retrieve(key):
    if key in memory:
        chunk = memory[key]
        return {
            "value": chunk["value"],
            "score": activation(chunk),
        }
    return {"value": None, "score": 0}


def normalize(text):
    text = text.lower().strip()

    if text in ["france", "germany"]:
        return f"capital_{text}"

    return text


def cognitive_router(state):
    text = state["input"]

    if text in ["france", "germany"]:
        return "memory"

    if text.startswith("capital_"):
        return "memory"

    if "calc" in text or "search" in text:
        return "tool"

    if len(text) > 12:
        return "llm"

    return "fallback"


def llm_reasoning(prompt):
    return f"[LLM reasoning]: understood -> {prompt}"


def actr_step(user_input):
    print(f"\n🧠 INPUT: {user_input}")

    push_goal("answer_question")

    state = {"input": user_input, "goal": current_goal()}

    route = cognitive_router(state)

    result = None

    if route == "memory":
        key = normalize(user_input)
        mem = retrieve(key)

        if mem["value"]:
            result = mem["value"]

            memory[key]["uses"] += 1
            memory[key]["last_used"] = time.time()

            print("📚 MEMORY USED")
        else:
            result = "unknown"

    elif route == "tool":
        if "calc" in user_input:
            result = tool_calc(user_input)
            print("🛠 CALC TOOL")

        elif "search" in user_input:
            result = tool_search(user_input)
            print("🛠 SEARCH TOOL")

    elif route == "llm":
        result = llm_reasoning(user_input)
        print("🤖 LLM USED")

    else:
        result = "I don't know"
        print("❓ FALLBACK USED")

    pop_goal()

    print("➡ RESULT:", result)
    print("🎯 GOAL STACK:", goal_stack)

    return result


actr_step("france")
actr_step("france")
actr_step("germany")
actr_step("search ai models")
actr_step("calc 5+7")
actr_step("explain neural networks")
