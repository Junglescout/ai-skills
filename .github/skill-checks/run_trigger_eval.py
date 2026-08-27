#!/usr/bin/env python3
"""Trigger-accuracy eval for the skills packaged in this repository.

The skills in this plugin overlap heavily on their description surface —
share-diagnosis, benchmark-brand, analyze-category-keywords and
innovation-whitespace all answer brand-versus-category questions. A description
edit that reads fine in a diff can quietly steal or lose traffic from a sibling
skill. This harness catches that: it shows a model nothing but the skill
descriptions plus a user prompt, and asserts which skill it routes to.

Fixtures live in .github/skill-checks/triggers/<skill-name>.yaml:

    should_trigger:
      - "why are we losing share in electrolytes?"
    should_not_trigger:
      - prompt: "rewrite our titles for the 75-char rule"
        expect: title-rewrite-and-item-highlights   # optional

`should_trigger` cases pass when the model picks this skill. `should_not_trigger`
cases pass when it picks anything else (or none) — unless `expect` names the
skill it must land on instead.

Usage:
    export ANTHROPIC_API_KEY=...
    python3 .github/skill-checks/run_trigger_eval.py [--skill NAME] [--min-accuracy 0.9]

Exits 1 if accuracy falls below the threshold, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
BATCH_SIZE = 10
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
NONE = "none"

SYSTEM_PROMPT = """You are the skill router for an AI assistant. You are given a \
catalogue of skills, each with a name and the description its author wrote to \
say when it should be used, and a numbered list of user prompts.

For each prompt, decide which single skill — if any — should be invoked. Judge \
only from the descriptions; do not invent skills. Answer "none" when no skill's \
description covers the prompt, and pick exactly one skill otherwise. Some \
descriptions overlap; choose the one whose stated triggers fit best.

Reply with JSON only, no prose: {"choices": [{"n": 1, "skill": "<name or none>"}, ...]} \
with one entry per prompt, in order."""


@dataclass
class Case:
    skill: str
    prompt: str
    should_trigger: bool
    expect: str | None = None

    def passed(self, chosen: str) -> bool:
        if self.should_trigger:
            return chosen == self.skill
        if self.expect:
            return chosen == self.expect
        return chosen != self.skill

    def wanted(self) -> str:
        if self.should_trigger:
            return self.skill
        return self.expect or f"anything but {self.skill}"


def load_catalogue(root: Path) -> dict[str, str]:
    """skill name -> description, read straight from the packaged SKILL.md files."""
    catalogue: dict[str, str] = {}
    for skill_md in sorted((root / "plugins").glob("*/skills/*/SKILL.md")):
        match = FRONTMATTER_RE.match(skill_md.read_text(encoding="utf-8"))
        if not match:
            continue
        frontmatter = yaml.safe_load(match.group(1)) or {}
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        if name and description:
            catalogue[name] = " ".join(str(description).split())
    return catalogue


def load_cases(fixtures_dir: Path, only: str | None) -> list[Case]:
    cases: list[Case] = []
    for fixture in sorted(fixtures_dir.glob("*.yaml")):
        skill = fixture.stem
        if only and skill != only:
            continue
        data = yaml.safe_load(fixture.read_text(encoding="utf-8")) or {}
        for entry in data.get("should_trigger", []) or []:
            prompt = entry["prompt"] if isinstance(entry, dict) else entry
            cases.append(Case(skill=skill, prompt=prompt, should_trigger=True))
        for entry in data.get("should_not_trigger", []) or []:
            if isinstance(entry, dict):
                cases.append(
                    Case(
                        skill=skill,
                        prompt=entry["prompt"],
                        should_trigger=False,
                        expect=entry.get("expect"),
                    )
                )
            else:
                cases.append(Case(skill=skill, prompt=entry, should_trigger=False))
    return cases


def route(client, model: str, catalogue: dict[str, str], prompts: list[str]) -> list[str]:
    listing = "\n\n".join(f"{name}: {desc}" for name, desc in sorted(catalogue.items()))
    numbered = "\n".join(f"{i}. {prompt}" for i, prompt in enumerate(prompts, start=1))
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"<skills>\n{listing}\n</skills>\n\n<prompts>\n{numbered}\n</prompts>",
            },
            {"role": "assistant", "content": '{"choices":'},
        ],
    )
    raw = '{"choices":' + message.content[0].text
    try:
        payload = json.loads(raw[: raw.rindex("}") + 1])
    except (ValueError, IndexError):
        raise SystemExit(f"router returned unparseable JSON:\n{raw}")

    chosen = [NONE] * len(prompts)
    for choice in payload.get("choices", []):
        index = int(choice.get("n", 0)) - 1
        if 0 <= index < len(prompts):
            skill = str(choice.get("skill", NONE)).strip()
            chosen[index] = skill if skill in catalogue else NONE
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", help="run only this skill's fixture")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--min-accuracy", type=float, default=0.9)
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()

    checks_dir = Path(__file__).resolve().parent
    root = Path(args.repo_root).resolve() if args.repo_root else checks_dir.parents[1]

    catalogue = load_catalogue(root)
    if not catalogue:
        sys.exit("no skills found under plugins/*/skills/")

    cases = load_cases(checks_dir / "triggers", args.skill)
    if not cases:
        sys.exit("no trigger fixtures found")

    missing = {case.skill for case in cases} - set(catalogue)
    if missing:
        sys.exit(f"fixtures reference unknown skills: {', '.join(sorted(missing))}")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set")

    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("the anthropic SDK is required: pip install anthropic")

    client = Anthropic()

    results: list[tuple[Case, str]] = []
    for start in range(0, len(cases), BATCH_SIZE):
        batch = cases[start : start + BATCH_SIZE]
        chosen = route(client, args.model, catalogue, [case.prompt for case in batch])
        results.extend(zip(batch, chosen))

    by_skill: dict[str, list[bool]] = {}
    failures: list[tuple[Case, str]] = []
    for case, chosen in results:
        ok = case.passed(chosen)
        by_skill.setdefault(case.skill, []).append(ok)
        if not ok:
            failures.append((case, chosen))

    print(f"model: {args.model}    cases: {len(results)}\n")
    print(f"{'skill':<38} {'pass':>5} {'total':>6} {'accuracy':>9}")
    for skill in sorted(by_skill):
        outcomes = by_skill[skill]
        passed = sum(outcomes)
        print(
            f"{skill:<38} {passed:>5} {len(outcomes):>6} "
            f"{passed / len(outcomes):>8.0%}"
        )

    if failures:
        print("\nfailures:")
        for case, chosen in failures:
            print(f"  [{case.skill}] {case.prompt}")
            print(f"      wanted {case.wanted()}, got {chosen}")

    accuracy = sum(sum(v) for v in by_skill.values()) / len(results)
    print(f"\noverall accuracy: {accuracy:.0%} (threshold {args.min_accuracy:.0%})")
    return 0 if accuracy >= args.min_accuracy else 1


if __name__ == "__main__":
    sys.exit(main())
