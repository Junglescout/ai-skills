# Skill checks

Two automated checks run against the skills in this repository before a pull
request merges. They exist because a skill is markdown: nothing about it is
compiled, so the things that break it — a renamed reference file, a description
that grew past the limit, a tool the MCP server renamed, a description edit that
quietly steals traffic from a sibling skill — are invisible in a diff and only
show up in a customer session.

| Check | Workflow | Runs on | Needs secrets | Cost |
|---|---|---|---|---|
| Structural lint | `skill-lint.yml` | every PR | no | free, ~10s |
| Trigger accuracy | `trigger-eval.yml` | PRs touching a `SKILL.md` or a fixture | `ANTHROPIC_API_KEY` | ~9 Haiku calls |

## 1. Structural lint

```bash
pip install pyyaml
python3 .github/skill-checks/lint_skills.py
```

Errors (fail the build):

- a skill directory with no `SKILL.md`, or unparseable YAML frontmatter
- `name` missing, not lowercase-kebab-case, or not matching its directory
- `description` missing or over 1024 characters — past that it gets truncated,
  which silently degrades triggering
- two skills declaring the same name
- a cited `references/*.md` that exists nowhere in the repo
- `` `some-skill` skill `` pointing at a skill that doesn't exist here
- a backticked `analyze_* / query_* / search_* / get_* / list_* / describe_*`
  identifier that isn't a known Jungle Scout MCP tool
- `marketplace.json` / `plugin.json` / `.mcp.json` invalid, mismatched, or
  pointing at a directory that isn't there

Warnings (reported, don't fail): a description within 10% of the length limit, a
reference file nothing points at, and a citation that resolves to a *different*
skill's reference file — legitimate when a skill defers styling to
`jungle-scout-visualizer`, worth a look otherwise.

Two lists back the tool-name check, both plain text with `#` comments:

- `mcp-tools.txt` — the Jungle Scout MCP tool names. Refresh it when the server
  gains or renames a tool.
- `not-tools.txt` — identifiers that look like tools but are request parameters
  or response fields (`search_volume`, `search_time_min`, …). Add to it when the
  linter flags a legitimate field name.

## 2. Trigger accuracy

```bash
pip install pyyaml anthropic
export ANTHROPIC_API_KEY=...
python3 .github/skill-checks/run_trigger_eval.py            # all skills
python3 .github/skill-checks/run_trigger_eval.py --skill share-diagnosis
```

Several skills here overlap on their description surface — `share-diagnosis`,
`benchmark-brand`, `analyze-category-keywords` and `innovation-whitespace` all
answer brand-versus-category questions. This check measures whether the
descriptions still separate cleanly: it shows a model nothing but the skill
names and descriptions plus a user prompt, and asserts where it routes.

Fixtures live in `triggers/<skill-name>.yaml`:

```yaml
should_trigger:
  - "why are we losing ground in electrolytes?"

should_not_trigger:
  - prompt: "rewrite our titles for the 75-character rule"
    expect: title-rewrite-and-item-highlights     # optional
  - "how big is the collagen market?"             # any other skill, or none
```

A `should_trigger` case passes when the router picks that skill. A
`should_not_trigger` case passes when it picks anything else — unless `expect`
names the sibling it must land on instead. Use `expect` only where the right
owner is unambiguous; without it the case stays robust.

The run prints a per-skill accuracy table and every failing case with what it
wanted and what it got, and exits 1 below `--min-accuracy` (default 0.9). Add a
fixture case whenever you change a description or add a skill — that is the
regression test for the change.

**One simplification to know about:** the router picks a single skill, while the
real assistant can activate several at once. That makes the check a good proxy
for "which description dominates" and a poor one for composition skills like
`jungle-scout-visualizer`, whose fixture is deliberately narrow.

**Setup:** add `ANTHROPIC_API_KEY` as a repository secret (Settings → Secrets and
variables → Actions). Without it the workflow logs a notice and passes, so pull
requests from forks don't fail on a secret their author can't provide.

## Not covered here

Behavioural evals — does the skill actually run the right steps and produce the
right report — belong in `claude plugin eval` suites with recorded MCP mocks, run
on a label or a nightly schedule rather than on every PR. That is the natural
next tier on top of these two.
