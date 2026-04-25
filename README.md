# ACT-R Cognitive Architecture

Minimal Python implementation of [ACT-R](https://act-r.psy.cmu.edu/) cognitive architecture principles.

## Features

- **Declarative Memory** with activation-based retrieval and decay
- **Goal Stack** management
- **Cognitive Router** that selects execution paths

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