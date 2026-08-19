from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.authority_verify import SPECS, verify_authority_pdf


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Structurally verify a privately supplied CBN authority PDF and record its SHA-256 hash."
    )
    parser.add_argument("framework", choices=sorted(SPECS))
    parser.add_argument("pdf")
    parser.add_argument("--json", dest="json_path")
    args = parser.parse_args()

    result = verify_authority_pdf(args.framework, args.pdf)
    print(json.dumps(result, indent=2))
    if args.json_path:
        out = Path(args.json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
