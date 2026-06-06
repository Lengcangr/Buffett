#!/usr/bin/env python3
"""Run saved Buffett skill review prompts through `codex exec`.

This helper keeps prompt encoding stable on Windows by feeding UTF-8 text to
Codex through stdin. It only produces raw scenario outputs; use
`run_review_suite.py --scenario-output-dir ...` to score them.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run_scenario(
    codex_bin: str,
    prompt_path: Path,
    output_path: Path,
    cwd: Path,
    sandbox: str,
    timeout_seconds: int,
) -> int:
    prompt = prompt_path.read_text(encoding="utf-8")
    wrapped = (
        "You must use the buffett-investing-coach skill. "
        "Answer the investment prompt only. Do not edit files. "
        "If current facts are needed, verify them and cite sources.\n\n"
        + prompt
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        codex_bin,
        "exec",
        "-",
        "--skip-git-repo-check",
        "-s",
        sandbox,
        "-C",
        str(cwd),
        "-o",
        str(output_path),
    ]
    completed = subprocess.run(
        cmd,
        input=wrapped,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_seconds,
        check=False,
    )
    log_path = output_path.with_suffix(".log")
    log_path.write_text(completed.stdout, encoding="utf-8", errors="replace")
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--scenario-id", action="append", help="Run only this scenario id. Repeatable.")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--sandbox", default="read-only")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    prompt_dir = args.prompt_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    wanted = set(args.scenario_id or [])
    prompt_paths = sorted(prompt_dir.glob("*.md"))
    if wanted:
        prompt_paths = [path for path in prompt_paths if path.stem in wanted]
    if not prompt_paths:
        raise SystemExit("No matching scenario prompts found.")

    failures: list[str] = []
    for prompt_path in prompt_paths:
        output_path = output_dir / f"{prompt_path.stem}.txt"
        print(f"running {prompt_path.stem} -> {output_path}")
        try:
            code = run_scenario(
                args.codex_bin,
                prompt_path,
                output_path,
                args.cwd.expanduser().resolve(),
                args.sandbox,
                args.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{prompt_path.stem}: timeout")
            continue
        if code != 0:
            failures.append(f"{prompt_path.stem}: codex exit {code}")

    if failures:
        print("failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
