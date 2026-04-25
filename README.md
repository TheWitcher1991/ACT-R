# ACT-R Cognitive Architecture

Minimal Python implementation of [ACT-R](https://act-r.psy.cmu.edu/) cognitive architecture principles with LLM integration.

## About

Экспериментальная реализация когнитивной архитектуры ACT-R (Adaptive Control of Thought — Rational) на Python. Система объединяет классические механизмы ACT-R с возможностями больших языковых моделей для создания интеллектуального агента с памятью, обучением и адаптивным поведением.

## Features

- **Declarative Memory** — декларативная память с активацией, затуханием и вероятностным извлечением
- **Semantic Memory** — семантическая память на основе эмбеддингов с косинусной相似度
- **Procedural Memory** — процедурная память с силой (strength), затуханием и обучением
- **Attention Module** — окно внимания (7±2), салиентность, захват внимания
- **Working Memory** — рабочая память последних 5 вводов
- **Emotional State** — валентность, возбуждение, доминирование (PAD модель)
- **Goal Stack** — управление целями с приоритетами
- **Production System** — система продукций для сопоставления с контекстом
- **Intent Analysis** — анализ намерений через LLM
- **Action Planning** — планирование действий
- **Reinforcement Learning** — обучение на основе вознаграждений
- **Session Export** — экспорт сессии в markdown
- **Tools** — встроенные инструменты (калькулятор, поиск)

## Architecture

```
┌─────────────────────────────────────┐
│           User Input                │
└─────────────┬───────────────────────┘
               ▼
┌─────────────────────────────────────┐
│        Cognitive Router             │
│  ┌─────────┬─────────┬────────┐      │
│  │ skill  │ memory  │ tool   │      │
│  └────┬────┴───┬────┴───┬────┘      │
└───────┼────────┼────────┼───────────┘
        ▼        ▼        ▼
      Skills   Memory    Tools ──► LLM Reasoning
```

## Installation

```bash
pip install -r requirements.txt
```

Создай `.env` с API ключом:
```
AI_API_KEY=твой_groq_ключ
```

## Usage

```python
from main import brain_step, init, save_session

init()
result = brain_step("France")           # → "Paris"
result = brain_step("calc 5+7")        # → 12
result = brain_step("Что такое AI?")    # → LLM reasoning

save_session("session.md")               # экспорт в markdown
```

## Input Types

- Факты: `"France"`, `"Париж"`
- Команды: `"calc 5+7"`, `"найди информацию"`
- Вопросы: `"Кто такой?"`, `"Что та��ое?"`
- Запросы: `"Объясни..."`, `"Расскажи..."`

## Memory Model

### Declarative Activation
```
A = (B + ln(U + 1)) × e^(-age/τ) + noise
```

### Procedural Strength
```
S = strength × e^(-time_since_use/τ) + noise
```

### Attention Salience
```
S = novelty × 0.3 + relevance × 0.4 + (1 - size) × 0.3
```

Where:
- `B` — base activation
- `U` — usage count
- `τ` — decay time constant (1000)
- `noise` — random noise for probabilistic retrieval

## License

Apache 2.0