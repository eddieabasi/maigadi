"""Export JSON Schema files for non-Python consumers and contract review.

Run ``uv run maigadi-schemas`` to regenerate ``shared/schemas/json/``, or with
``--check`` to fail when the committed files are stale (CI runs the same check
as a test).
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from pydantic import TypeAdapter

from maigadi_schemas.captions import Caption
from maigadi_schemas.coverage import Coverage, SystemState
from maigadi_schemas.events import Event
from maigadi_schemas.messages import InboundEvent, InboxMessage, OutboundMessage
from maigadi_schemas.policy_pack import PolicyPack
from maigadi_schemas.rule_pack import RulePack
from maigadi_schemas.site import SiteConfig

JSON_SCHEMA_DIALECT: Final = "https://json-schema.org/draft/2020-12/schema"
DEFAULT_OUT_DIR: Final = Path(__file__).resolve().parents[2] / "json"

SCHEMAS: Final[dict[str, tuple[str, Any]]] = {
    "event": ("Event", Event),
    "caption": ("Caption", Caption),
    "coverage": ("Coverage", Coverage),
    "system-state": ("SystemState", SystemState),
    "outbound-message": ("OutboundMessage", OutboundMessage),
    "inbound-event": ("InboundEvent", InboundEvent),
    "inbox-message": ("InboxMessage", InboxMessage),
    "site-config": ("SiteConfig", SiteConfig),
    "rule-pack": ("RulePack", RulePack),
    "policy-pack": ("PolicyPack", PolicyPack),
}


def json_schemas() -> dict[str, dict[str, Any]]:
    """Validation-mode JSON Schema for every exported type, keyed by file stem."""
    result: dict[str, dict[str, Any]] = {}
    for stem, (title, schema_type) in SCHEMAS.items():
        schema = TypeAdapter(schema_type).json_schema(mode="validation")
        result[stem] = {"$schema": JSON_SCHEMA_DIALECT, "title": title, **schema}
    return result


def _render(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="maigadi-schemas", description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="output directory")
    parser.add_argument("--check", action="store_true", help="exit 1 if files are stale")
    args = parser.parse_args(argv)
    out: Path = args.out

    wanted = {f"{stem}.schema.json": _render(s) for stem, s in json_schemas().items()}
    existing = {p.name: p.read_text(encoding="utf-8") for p in out.glob("*.schema.json")}

    if args.check:
        names = wanted.keys() | existing.keys()
        stale = sorted(n for n in names if wanted.get(n) != existing.get(n))
        if stale:
            sys.stderr.write(f"stale schema files in {out}: {', '.join(stale)}\n")
            return 1
        return 0

    out.mkdir(parents=True, exist_ok=True)
    for name in existing.keys() - wanted.keys():
        (out / name).unlink()
    for name, text in wanted.items():
        (out / name).write_text(text, encoding="utf-8")
    sys.stdout.write(f"wrote {len(wanted)} schema files to {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
