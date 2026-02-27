# clockwork-1

Quick setup for using Alex Zhang's RLM library with a Modal-hosted GLM-5 endpoint.

## 1) Install deps

```bash
uv sync
```

## 2) Configure secrets safely (without pasting token into chat)

Copy the template:

```bash
cp .env.example .env
```

Recommended: store token in a file outside the repo and lock permissions.

```bash
mkdir -p ~/.config/clockwork
read -s -p "Modal token: " MODAL_TOKEN && echo
printf "%s" "$MODAL_TOKEN" > ~/.config/clockwork/modal_glm5.token
chmod 600 ~/.config/clockwork/modal_glm5.token
unset MODAL_TOKEN
```

Then in `.env`, set:

```bash
RLM_OPENAI_BASE_URL="https://api.us-west-2.modal.direct/v1"
RLM_MODEL_NAME="zai-org/GLM-5-FP8"
RLM_OPENAI_API_KEY_FILE="$HOME/.config/clockwork/modal_glm5.token"
```

## 3) Python equivalent of your curl smoke test

```bash
uv run python scripts/rlm_quick_setup.py
```

This performs an OpenAI-compatible `chat.completions.create(...)` call against your Modal endpoint.

## 4) Run an actual RLM pass + trajectory logging

```bash
uv run python scripts/rlm_quick_setup.py --rlm
```

This writes JSONL traces into `.rlm_logs/` via `RLMLogger`.

## 5) Visualize the trajectory

```bash
uv run python scripts/rlm_visualizer.py .rlm_logs/<your_log_file>.jsonl
```

## Monty runtime exploration

RLM `0.1.1` does not expose a first-class runtime plugin slot for replacing `LocalREPL` execution, so the quick setup includes a `--use-monty` exploration mode that exposes a placeholder `run_monty(...)` tool to the REPL while keeping RLM execution stable.

```bash
uv run python scripts/rlm_quick_setup.py --rlm --use-monty
```

To fully switch the REPL execution backend to Monty, the next step is a small custom environment adapter (similar to the `monty_runtime.py` pattern you shared) and wiring it into the `get_environment` router in your fork.
