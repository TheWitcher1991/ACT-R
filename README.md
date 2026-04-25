# ACT-R Cognitive Architecture

Minimal Python implementation of [ACT-R](https://act-r.psy.cmu.edu/) cognitive architecture principles with LLM integration.

## About

Это экспериментальная реализация когнитивной архитектуры ACT-R (Adaptive Control of Thought — Rational) на Python. Система объединяет классические механизмы ACT-R с возможностями больших языковых моделей для создания интеллектуального агента с памятью, обучением и адаптивным поведением.

## Features

- **Declarative Memory** — декларативная память с активацией, затуханием и вероятностным извлечением
- **Semantic Memory** — семантическая память на основе эмбеддингов с косинусной相似度
- **Goal Stack** — управление целями с приоритетами
- **Production System** — система продукций для сопоставления с контекстом
- **Intent Analysis** — анализ намерений пользователя через LLM
- **Action Planning** — планирование действий
- **Reinforcement Learning** — обучение на основе вознаграждений
- **Tools** — встроенные инструменты (калькулятор, поиск)

## Architecture

```
┌─────────────────────────────────────┐
│           User Input                │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────────────────┐
│        Cognitive Router             │
│  ┌─────────┬────────┬────────┐      │
│  │ memory  │  tool  │  llm   │      │
│  └────┬────┴───┬────┴───┬────┘      │
└───────┼────────┼────────┼───────────┘
        ▼        ▼        ▼
     Memory    Tools    Reasoning
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from main import actr_step

actr_step("france")           # → "Paris"
actr_step("calc 2+2")         # → 4
actr_step("explain AI")       # → LLM reasoning
```

## Memory Model

Activation formula:
```
A = (B + ln(U + 1)) × e^(-age/τ) + noise
```
Where:
- `B` — base activation
- `U` — usage count
- `τ` — decay time constant
- `noise` — random noise for probabilistic retrieval

## License

Apache 2.0