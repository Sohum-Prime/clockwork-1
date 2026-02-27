from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Lightweight visualizer for RLMLogger JSONL trajectories")
    parser.add_argument("log_file", type=Path, help="Path to an .rlm_logs/*.jsonl trajectory file")
    args = parser.parse_args()

    lines = [json.loads(line) for line in args.log_file.read_text(encoding="utf-8").splitlines() if line]
    metadata = next((x for x in lines if x.get("type") == "metadata"), None)
    iterations = [x for x in lines if x.get("type") == "iteration"]

    if metadata:
        print("=== Run Metadata ===")
        print(f"root_model: {metadata.get('root_model')}")
        print(f"backend: {metadata.get('backend')}")
        print(f"environment: {metadata.get('environment_type')}")
        print()

    print(f"=== Iterations ({len(iterations)}) ===")
    for item in iterations:
        idx = item.get("iteration")
        final_answer = item.get("final_answer")
        blocks = item.get("code_blocks", [])
        print(f"[{idx}] code_blocks={len(blocks)} final_answer={bool(final_answer)}")
        if final_answer:
            print(f"    {final_answer[:200]}")


if __name__ == "__main__":
    main()
