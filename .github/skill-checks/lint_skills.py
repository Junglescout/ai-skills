#!/usr/bin/env python3
"""Structural lint for the skills packaged in this repository.

Checks the things that break a skill silently — bad frontmatter, an
over-length description, a reference file that was renamed but still cited, a
cross-skill pointer to a skill that no longer exists, an MCP tool that was
renamed server-side — none of which are visible when reading a diff.

Usage:
    python3 .github/skill-checks/lint_skills.py [--repo-root PATH]

Exits 1 if any error is found. Warnings do not fail the run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - surfaced to the operator, not tested
    sys.exit("PyYAML is required: pip install pyyaml")

# Claude truncates skill descriptions past this; a longer one degrades triggering.
MAX_DESCRIPTION_CHARS = 1024
MAX_NAME_CHARS = 64
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
BACKTICKED_RE = re.compile(r"`([a-z][a-z0-9_]*)`")
TOOL_PREFIXES = ("analyze_", "query_", "search_", "get_", "list_", "describe_")
# "`jungle-scout-visualizer` skill" — a pointer from one skill to another.
SKILL_POINTER_RE = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`\s+skill")
# "references/worked-example.md", with or without backticks.
REFERENCE_RE = re.compile(r"(references/[A-Za-z0-9._-]+\.md)")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: Path | str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: Path | str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


def load_list(path: Path) -> set[str]:
    if not path.exists():
        return set()
    entries = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.add(line)
    return entries


def parse_frontmatter(text: str) -> dict | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    parsed = yaml.safe_load(match.group(1))
    return parsed if isinstance(parsed, dict) else None


def check_skill(
    skill_dir: Path, root: Path, all_skill_dirs: list[Path], report: Report
) -> str | None:
    """Lint one skill directory. Returns the declared skill name, if any."""
    rel = skill_dir.relative_to(root)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        report.error(rel, "no SKILL.md")
        return None

    text = skill_md.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    if frontmatter is None:
        report.error(rel / "SKILL.md", "missing or unparseable YAML frontmatter")
        return None

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        report.error(rel / "SKILL.md", "frontmatter has no 'name'")
        name = None
    else:
        name = name.strip()
        if name != skill_dir.name:
            report.error(
                rel / "SKILL.md",
                f"name '{name}' does not match directory '{skill_dir.name}'",
            )
        if not NAME_RE.match(name):
            report.error(rel / "SKILL.md", f"name '{name}' is not lowercase-kebab-case")
        if len(name) > MAX_NAME_CHARS:
            report.error(
                rel / "SKILL.md",
                f"name is {len(name)} chars, over the {MAX_NAME_CHARS} limit",
            )

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        report.error(rel / "SKILL.md", "frontmatter has no 'description'")
    else:
        collapsed = " ".join(description.split())
        if len(collapsed) > MAX_DESCRIPTION_CHARS:
            report.error(
                rel / "SKILL.md",
                f"description is {len(collapsed)} chars, over the "
                f"{MAX_DESCRIPTION_CHARS} limit",
            )
        elif len(collapsed) > MAX_DESCRIPTION_CHARS * 0.9:
            report.warn(
                rel / "SKILL.md",
                f"description is {len(collapsed)} chars, close to the "
                f"{MAX_DESCRIPTION_CHARS} limit",
            )

    check_references(skill_dir, root, all_skill_dirs, report)
    return name


def markdown_files(skill_dir: Path) -> list[Path]:
    return sorted(skill_dir.rglob("*.md"))


def check_references(
    skill_dir: Path, root: Path, all_skill_dirs: list[Path], report: Report
) -> None:
    """Every cited references/*.md must exist, and every one that exists must be cited."""
    cited: set[str] = set()
    for md in markdown_files(skill_dir):
        for path in sorted(set(REFERENCE_RE.findall(md.read_text(encoding="utf-8")))):
            cited.add(path)
            if (skill_dir / path).exists():
                continue
            # Skills legitimately point at a sibling skill's reference file
            # ("read jungle-scout-visualizer's references/visuals.md").
            owners = [
                other.name
                for other in all_skill_dirs
                if other != skill_dir and (other / path).exists()
            ]
            if owners:
                report.warn(
                    md.relative_to(root),
                    f"cites '{path}', which lives in {', '.join(owners)} rather than "
                    "this skill — fine if that cross-skill pointer is intended",
                )
            else:
                report.error(
                    md.relative_to(root), f"cites '{path}', which does not exist"
                )

    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        for reference in sorted(references_dir.glob("*.md")):
            key = f"references/{reference.name}"
            if key not in cited:
                report.warn(
                    reference.relative_to(root),
                    "exists but no SKILL.md or reference file points at it",
                )


def check_cross_references(
    skill_dir: Path, root: Path, known_skills: set[str], report: Report
) -> None:
    for md in markdown_files(skill_dir):
        for pointer in set(SKILL_POINTER_RE.findall(md.read_text(encoding="utf-8"))):
            if pointer not in known_skills:
                report.error(
                    md.relative_to(root),
                    f"points at skill '{pointer}', which does not exist in this repo",
                )


def check_tool_names(
    skill_dir: Path, root: Path, tools: set[str], not_tools: set[str], report: Report
) -> None:
    if not tools:
        return
    for md in markdown_files(skill_dir):
        for token in set(BACKTICKED_RE.findall(md.read_text(encoding="utf-8"))):
            if not token.startswith(TOOL_PREFIXES):
                continue
            if token in tools or token in not_tools:
                continue
            report.error(
                md.relative_to(root),
                f"'{token}' looks like an MCP tool but is not in "
                "mcp-tools.txt (add it there if the server gained a tool, or to "
                "not-tools.txt if it is a field name)",
            )


def check_manifests(root: Path, plugin_dirs: list[Path], report: Report) -> None:
    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.exists():
        report.error(".claude-plugin/marketplace.json", "missing")
        return

    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(".claude-plugin/marketplace.json", f"invalid JSON: {exc}")
        return

    listed: set[str] = set()
    for entry in marketplace.get("plugins", []):
        name = entry.get("name")
        source = entry.get("source")
        listed.add(name)
        if not name or not source:
            report.error(
                ".claude-plugin/marketplace.json",
                f"plugin entry missing name or source: {entry!r}",
            )
            continue
        source_dir = (root / source).resolve()
        if not source_dir.is_dir():
            report.error(
                ".claude-plugin/marketplace.json",
                f"plugin '{name}' points at '{source}', which is not a directory",
            )

    for plugin_dir in plugin_dirs:
        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        rel = manifest_path.relative_to(root)
        if not manifest_path.exists():
            report.error(plugin_dir.relative_to(root), "no .claude-plugin/plugin.json")
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.error(rel, f"invalid JSON: {exc}")
            continue
        name = manifest.get("name")
        if name != plugin_dir.name:
            report.error(rel, f"name '{name}' does not match directory '{plugin_dir.name}'")
        if not manifest.get("description"):
            report.error(rel, "no description")
        if name and name not in listed:
            report.error(
                ".claude-plugin/marketplace.json",
                f"plugin '{name}' exists on disk but is not listed",
            )

    mcp_path = root / "plugins" / "jungle-scout-cobalt" / ".mcp.json"
    if mcp_path.exists():
        try:
            json.loads(mcp_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.error(mcp_path.relative_to(root), f"invalid JSON: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None, help="defaults to the repo root")
    args = parser.parse_args()

    checks_dir = Path(__file__).resolve().parent
    root = Path(args.repo_root).resolve() if args.repo_root else checks_dir.parents[1]

    report = Report()
    tools = load_list(checks_dir / "mcp-tools.txt")
    not_tools = load_list(checks_dir / "not-tools.txt")

    plugin_dirs = sorted(p for p in (root / "plugins").iterdir() if p.is_dir())
    if not plugin_dirs:
        report.error("plugins/", "no plugins found")

    skill_dirs: list[Path] = []
    for plugin_dir in plugin_dirs:
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            report.error(plugin_dir.relative_to(root), "no skills/ directory")
            continue
        skill_dirs.extend(sorted(p for p in skills_dir.iterdir() if p.is_dir()))

    names: dict[str, Path] = {}
    for skill_dir in skill_dirs:
        name = check_skill(skill_dir, root, skill_dirs, report)
        if name:
            if name in names:
                report.error(
                    skill_dir.relative_to(root),
                    f"duplicate skill name '{name}', also declared by "
                    f"{names[name].relative_to(root)}",
                )
            else:
                names[name] = skill_dir

    known_skills = set(names)
    for skill_dir in skill_dirs:
        check_cross_references(skill_dir, root, known_skills, report)
        check_tool_names(skill_dir, root, tools, not_tools, report)

    check_manifests(root, plugin_dirs, report)

    for warning in report.warnings:
        print(f"warning: {warning}")
    for error in report.errors:
        print(f"error: {error}")

    print(
        f"\nchecked {len(skill_dirs)} skills across {len(plugin_dirs)} plugins: "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)"
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
