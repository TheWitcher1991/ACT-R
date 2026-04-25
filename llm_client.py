import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("AI_API_KEY")

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def chat(messages, model=DEFAULT_MODEL, temperature=0.7):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def analyze_intent(user_input):
    system_prompt = """Ты — когнитивный помощник. Проанализируй запрос пользователя и определи:
1. intent: question | task | search | calc | chat
2. needs_memory: yes | no | maybe
3. needs_tools: yes | no
4. complexity: low | high | medium

Ответь в формате JSON."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    import json
    import re

    response = chat(messages, temperature=0.3)

    try:
        json_match = re.search(r"\{[^}]+\}", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass

    return {
        "intent": "chat",
        "needs_memory": "maybe",
        "needs_tools": "no",
        "complexity": "medium",
    }


def plan_action(user_input, intent_info):
    system_prompt = """Ты — когнитивный планировщик. Создай план действий для выполнения запроса.
Верни список шагов (массив строк)."""

    context = f"Запрос: {user_input}\nИнтент: {intent_info.get('intent')}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context},
    ]

    response = chat(messages, temperature=0.5)

    try:
        import json

        return json.loads(response)
    except:
        return [response]


def reason(user_input, context=None):
    system_prompt = """Ты — когнитивный ассистент. Отвечай на вопросы пользователя.
Используй предоставленный контекст из памяти если релевантно.
Будь кратким и полезным."""

    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.append({"role": "system", "content": f"Контекст: {context}"})

    messages.append({"role": "user", "content": user_input})

    return chat(messages)
