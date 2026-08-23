"""Validate the register, classify every entry, render the published artefact.

Exit code 1 on any schema failure or stale review date, so CI blocks the merge.
That failure is the control. A register that cannot go stale silently is the
whole point of keeping it in version control.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
REVIEW_INTERVAL_DAYS = 180

sys.path.insert(0, str(ROOT / "src"))
from classify import classify  # noqa: E402


def load_entries() -> list[dict]:
    entries = []
    for path in sorted((ROOT / "register" / "systems").glob("*.yaml")):
        with path.open() as fh:
            data = yaml.safe_load(fh)
        data["_source"] = path.name
        entries.append(data)
    return entries


def validate(entries: list[dict]) -> list[str]:
    schema = json.loads((ROOT / "schema" / "system.schema.json").read_text())
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    seen_ids: set[str] = set()

    for entry in entries:
        payload = {k: v for k, v in entry.items() if not k.startswith("_")}
        for err in sorted(validator.iter_errors(payload), key=lambda e: e.path):
            loc = ".".join(str(p) for p in err.path) or "(root)"
            errors.append(f"{entry['_source']}: {loc}: {err.message}")

        sid = entry.get("id")
        if sid in seen_ids:
            errors.append(f"{entry['_source']}: duplicate id {sid}")
        seen_ids.add(sid)

        reviewed = entry.get("last_reviewed")
        if reviewed:
            age = date.today() - date.fromisoformat(str(reviewed))
            if age > timedelta(days=REVIEW_INTERVAL_DAYS):
                errors.append(
                    f"{entry['_source']}: review overdue by {age.days - REVIEW_INTERVAL_DAYS} days"
                )
    return errors


def main() -> int:
    entries = load_entries()
    errors = validate(entries)
    if errors:
        print("REGISTER VALIDATION FAILED\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    results = [classify(e) for e in entries]

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), trim_blocks=True, lstrip_blocks=True)
    rendered = env.get_template("register.md.j2").render(
        entries=entries,
        results={r.system_id: r for r in results},
        generated=date.today().isoformat(),
        counts={
            t: sum(1 for r in results if r.tier == t)
            for t in sorted({r.tier for r in results})
        },
    )
    out = ROOT / "docs" / "register.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(rendered)

    (ROOT / "docs" / "classifications.json").write_text(
        json.dumps([r.to_dict() for r in results], indent=2)
    )

    print(f"OK: {len(entries)} entries validated and classified -> {out.relative_to(ROOT)}")
    for r in results:
        print(f"  {r.system_id}  {r.tier:<32} role={r.effective_role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
