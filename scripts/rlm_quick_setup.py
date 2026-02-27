from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from rlm import RLM
from rlm.logger import RLMLogger


DEFAULT_BASE_URL = "https://api.us-west-2.modal.direct/v1"
DEFAULT_MODEL = "zai-org/GLM-5-FP8"


def _read_api_key() -> str:
    key = os.getenv("RLM_OPENAI_API_KEY", "").strip()
    key_file = os.getenv("RLM_OPENAI_API_KEY_FILE", "").strip()

    if key:
        return key

    if key_file:
        token = Path(key_file).expanduser().read_text(encoding="utf-8").strip()
        if token:
            return token

    raise RuntimeError(
        "Missing API key. Set RLM_OPENAI_API_KEY or RLM_OPENAI_API_KEY_FILE in your environment."
    )


def _build_client() -> tuple[OpenAI, str]:
    base_url = os.getenv("RLM_OPENAI_BASE_URL", DEFAULT_BASE_URL).strip()
    model = os.getenv("RLM_MODEL_NAME", DEFAULT_MODEL).strip()
    api_key = _read_api_key()
    return OpenAI(api_key=api_key, base_url=base_url), model


def raw_chat_completion(prompt: str) -> str:
    client, model = _build_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    return response.choices[0].message.content or ""


def bash(cmd: str) -> dict[str, Any]:
    proc = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def rg(pattern: str, path: str = ".") -> dict[str, Any]:
    return bash(f"rg --line-number --hidden --glob '!.git' {json.dumps(pattern)} {json.dumps(path)}")


def cat(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def run_rlm(prompt: str, use_monty: bool = False) -> str:
    _, model = _build_client()
    logger = RLMLogger(log_dir=".rlm_logs", file_name="trajectory")

    setup_note = (
        "Monty runtime is requested. This setup exposes a run_monty(code) tool for experimentation; "
        "native LocalREPL execution remains the default in rlms 0.1.1."
        if use_monty
        else ""
    )

    custom_tools: dict[str, Any] = {
        "bash": (bash, "Run shell commands and inspect stdout/stderr."),
        "rg": (rg, "Search files quickly with ripgrep."),
        "cat": (cat, "Read UTF-8 files from disk."),
    }

    if use_monty:
        custom_tools["run_monty"] = (
            lambda code: "Install pydantic-monty and wire a custom runtime adapter for full Monty execution.",
            "Placeholder for Monty runtime execution.",
        )

    rlm = RLM(
        backend="openai",
        backend_kwargs={
            "api_key": _read_api_key(),
            "base_url": os.getenv("RLM_OPENAI_BASE_URL", DEFAULT_BASE_URL),
            "model_name": model,
        },
        environment="local",
        max_depth=2,
        max_iterations=8,
        logger=logger,
        verbose=True,
        custom_tools=custom_tools,
        custom_sub_tools=custom_tools,
    )

    completion = rlm.completion(
        {
            "context": prompt,
            "setup": setup_note,
        },
        root_prompt="Use the REPL and tools when useful, then call FINAL_VAR with the answer.",
    )
    return completion.response


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Quick setup + smoke test for RLM with Modal GLM-5")
    parser.add_argument("--prompt", default="How many r's are in strawberry?")
    parser.add_argument("--rlm", action="store_true", help="Run an RLM completion after raw API smoke test.")
    parser.add_argument("--use-monty", action="store_true", help="Enable Monty exploration tool in REPL.")
    args = parser.parse_args()

    text = raw_chat_completion(args.prompt)
    print("[raw completion]", text)

    if args.rlm:
        answer = run_rlm(args.prompt, use_monty=args.use_monty)
        print("[rlm completion]", answer)
        print("[visualizer] Trajectory logs were written to .rlm_logs/*.jsonl")


if __name__ == "__main__":
    main()
