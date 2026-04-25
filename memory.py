import math
import random
import time
from typing import Any, Optional

B_BASE = 1.0
TAU_DECAY = 1000
NOISE_MEAN = 0
NOISE_STD = 0.1


def activation(key: str) -> float:
    mem = memory.get(key)
    if not mem:
        return -float("inf")

    B = mem.get("base_activation", B_BASE)
    U = mem.get("uses", 0)
    created = mem.get("created", time.time())

    age = time.time() - created

    # A = (B + ln(U + 1)) × e^(-age/τ) + noise
    base = B + math.log(U + 1)
    decay = math.exp(-age / TAU_DECAY)
    noise = random.gauss(NOISE_MEAN, NOISE_STD)

    A = base * decay + noise
    return A


memory = {
    "capital_france": {
        "value": "Paris",
        "uses": 5,
        "created": time.time() - 100,
        "base_activation": B_BASE,
        "embedding": None,  # будет заполнено при векторизации
    },
    "capital_germany": {
        "value": "Berlin",
        "uses": 3,
        "created": time.time() - 200,
        "base_activation": B_BASE,
        "embedding": None,
    },
}

vector_memory: dict[str, list[float]] = {}


def compute_embedding(text: str) -> list[float]:
    from llm_client import chat

    messages = [
        {
            "role": "system",
            "content": "Верни 3-мерный вектор (список чисел) для семантического представления этого текста. Будь краток.",
        },
        {"role": "user", "content": text},
    ]

    result = chat(messages, temperature=0.3)

    try:
        import ast

        vec = ast.literal_eval(result)
        if isinstance(vec, list):
            return vec[:3]
    except:
        pass

    return [0.0, 0.0, 0.0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def store(key: str, value: Any, text_for_embedding: Optional[str] = None):
    memory[key] = {
        "value": value,
        "uses": 0,
        "created": time.time(),
        "base_activation": B_BASE,
        "embedding": None,
    }

    if text_for_embedding:
        vec = compute_embedding(text_for_embedding)
        vector_memory[key] = vec
        memory[key]["embedding"] = vec


def retrieve(key: str) -> Optional[dict]:
    mem = memory.get(key)
    if mem:
        mem["uses"] += 1
    return mem


def retrieve_by_activation(threshold: float = 0.5) -> Optional[tuple[str, dict]]:
    best_key = None
    best_A = -float("inf")

    for key in memory:
        A = activation(key)
        if A > best_A and A >= threshold:
            best_A = A
            best_key = key

    if best_key:
        return best_key, memory[best_key]

    return None


def retrieve_semantic(query: str, top_k: int = 3) -> list[tuple[str, float]]:
    query_vec = compute_embedding(query)

    results = []
    for key, vec in vector_memory.items():
        sim = cosine_similarity(query_vec, vec)
        A = activation(key)
        combined = sim * 0.7 + A * 0.3
        results.append((key, combined))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


goal_stack: list[dict] = []


def push_goal(goal: str, priority: int = 0):
    goal_stack.append(
        {
            "goal": goal,
            "priority": priority,
            "created": time.time(),
        }
    )
    goal_stack.sort(key=lambda x: x["priority"], reverse=True)


def pop_goal() -> Optional[dict]:
    if goal_stack:
        return goal_stack.pop(0)
    return None


def current_goal() -> Optional[dict]:
    return goal_stack[0] if goal_stack else None


productions: list[dict] = []


def add_production(name: str, condition: str, action: str):
    productions.append(
        {
            "name": name,
            "condition": condition,
            "action": action,
            "uses": 0,
        }
    )


def match_production(context: dict) -> Optional[dict]:
    for prod in productions:
        cond = prod["condition"]

        for key, value in context.items():
            if key in cond and value in cond:
                prod["uses"] += 1
                return prod

    return None


history: list[dict] = []


def learn_from_interaction(input_text: str, action: str, result: Any, reward: float):
    history.append(
        {
            "input": input_text,
            "action": action,
            "result": result,
            "reward": reward,
            "timestamp": time.time(),
        }
    )

    if reward > 0.7:
        store(f"learned_{input_text}", result)

    update_productions(input_text, action, result, reward)


def update_productions(input_text: str, action: str, result: Any, reward: float):
    if reward < 0.3:
        for prod in productions:
            if prod["action"] == action:
                prod["uses"] -= 1

    if reward > 0.8 and action not in [p["action"] for p in productions]:
        add_production(
            name=f"learned_{len(productions)}", condition=input_text, action=action
        )


def get_best_action(input_text: str) -> Optional[str]:
    similar = retrieve_semantic(input_text)

    for key, score in similar:
        mem = memory.get(key)
        if mem and mem.get("uses", 0) > 0:
            for h in reversed(history):
                if h["input"] == key:
                    return h["action"]

    return None
