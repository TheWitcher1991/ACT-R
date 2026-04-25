import math
import random
import time
from typing import Any, Optional

B_BASE = 1.0
TAU_DECAY = 1000
NOISE_MEAN = 0
NOISE_STD = 0.1

# Procedural Memory Configuration
PROC_INITIAL_STRENGTH = 0.3
PROC_STRENGTH_INC = 0.2
PROC_STRENGTH_DEC = 0.05
PROC_PRACTICE_BONUS = 0.15


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

    if not result:
        return [0.0, 0.0, 0.0]

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


procedural_memory: dict[str, dict] = {}


def add_skill(name: str, condition: str, action: str):
    """Add a new skill to procedural memory."""
    procedural_memory[name] = {
        "name": name,
        "condition": condition,
        "action": action,
        "strength": PROC_INITIAL_STRENGTH,
        "created": time.time(),
        "last_used": time.time(),
        "uses": 0,
    }


def get_skill_strength(skill: dict) -> float:
    """Compute activation (strength) for a skill using ACT-R formula:
    S = strength * e^(-time_since_use/τ) + noise
    """
    S = skill.get("strength", PROC_INITIAL_STRENGTH)
    last_used = skill.get("last_used", time.time())
    time_since = time.time() - last_used
    decay = math.exp(-time_since / TAU_DECAY)
    noise = random.gauss(NOISE_MEAN, NOISE_STD)
    return S * decay + noise


def strengthen_skill(skill_name: str):
    """Strengthen a skill after successful use."""
    skill = procedural_memory.get(skill_name)
    if skill:
        skill["strength"] = min(1.0, skill["strength"] + PROC_STRENGTH_INC)
        skill["uses"] += 1
        skill["last_used"] = time.time()


def weaken_skill(skill_name: str):
    """Weaken a skill after failed use."""
    skill = procedural_memory.get(skill_name)
    if skill:
        skill["strength"] = max(0.0, skill["strength"] - PROC_STRENGTH_DEC)


def practice_skill(skill_name: str):
    """Practice a skill to strengthen it (practice bonus)."""
    skill = procedural_memory.get(skill_name)
    if skill:
        skill["strength"] = min(1.0, skill["strength"] + PROC_PRACTICE_BONUS)


def retrieve_skill(condition: str, threshold: float = 0.2) -> Optional[dict]:
    """Retrieve best matching skill by condition similarity."""
    best_skill = None
    best_activation = -float("inf")

    for skill in procedural_memory.values():
        if condition in skill.get("condition", ""):
            A = get_skill_strength(skill)
            if A > best_activation and A >= threshold:
                best_activation = A
                best_skill = skill

    if best_skill:
        best_skill["uses"] += 1
        best_skill["last_used"] = time.time()

    return best_skill


def retrieve_best_skill() -> Optional[dict]:
    """Retrieve skill with highest activation."""
    best_skill = None
    best_A = -float("inf")

    for skill in procedural_memory.values():
        A = get_skill_strength(skill)
        if A > best_A:
            best_A = A
            best_skill = skill

    return best_skill if best_skill else None


def get_all_skills_sorted() -> list[tuple[str, dict]]:
    """Get all skills sorted by strength (descending)."""
    results = []
    for name, skill in procedural_memory.items():
        A = get_skill_strength(skill)
        results.append((name, skill, A))

    results.sort(key=lambda x: x[2], reverse=True)
    return results


def clear_skill(skill_name: str):
    """Remove a skill from procedural memory."""
    if skill_name in procedural_memory:
        del procedural_memory[skill_name]


add_skill(name="calculate", condition="math expression", action="use_calculator")
add_skill(
    name="search_info", condition="what is, who is, where is", action="search_web"
)


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


ATTENTION_CAPACITY = 7

attention_window: list[dict] = []
focused_item: Optional[dict] = None


def attend(item: Any):
    global focused_item

    attention_window.insert(
        0, {"item": item, "salience": 1.0, "timestamp": time.time()}
    )

    if len(attention_window) > ATTENTION_CAPACITY:
        attention_window.pop()

    focused_item = attention_window[0]


def calculate_salience(
    item: Any, novelty: float = 0.5, relevance: float = 0.5, size: float = 0.5
) -> float:
    return novelty * 0.3 + relevance * 0.4 + (1 - size) * 0.3


def attentional_capture(stimulus: Any):
    salience = calculate_salience(stimulus)
    if salience > 0.7:
        attend(stimulus)
        return True
    return False


def shift_attention(to_index: int = 0):
    global focused_item
    if 0 <= to_index < len(attention_window):
        focused_item = attention_window[to_index]


def clear_attention():
    global attention_window, focused_item
    attention_window.clear()
    focused_item = None


def get_focused() -> Optional[dict]:
    return focused_item


def get_attention_capacity() -> int:
    return ATTENTION_CAPACITY


def get_attention_load() -> int:
    return len(attention_window)
