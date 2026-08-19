from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.framework_loader import load_frameworks
from src.provenance import provenance_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit framework source provenance and verification states.")
    parser.add_argument("--strict", action="store_true", help="Fail when provenance errors are present.")
    parser.add_argument("--json", dest="json_path", help="Optional path for JSON output.")
    args = parser.parse_args()

    summary = provenance_summary(load_frameworks(ROOT / "frameworks"))
    print(f"frameworks={summary['frameworks']} controls={summary['controls']} errors={summary['errors']} warnings={summary['warnings']}")
    for finding in summary["findings"]:
        print(f"{finding['severity'].upper()}: {finding['framework_id']}: {finding['message']}")

    if args.json_path:
        path = Path(args.json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return 1 if args.strict and summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
