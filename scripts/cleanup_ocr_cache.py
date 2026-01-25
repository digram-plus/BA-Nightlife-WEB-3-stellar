#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

CACHE_DIR = Path("storage/ocr_cache")
DEFAULT_TTL_DAYS = 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove OCR.Space cache files older than the TTL"
    )
    parser.add_argument(
        "--ttl-days",
        type=int,
        default=DEFAULT_TTL_DAYS,
        help="How many days to keep cache entries (default: 60)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be removed without deleting",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ttl = timedelta(days=args.ttl_days)
    now = datetime.utcnow()

    if not CACHE_DIR.exists():
        print("Cache directory does not exist; nothing to do")
        return 0

    removed = 0
    for path in CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            created_str = data.get("created_at")
            created = datetime.fromisoformat(created_str) if created_str else None
        except Exception:
            created = None

        if not created:
            created = datetime.utcfromtimestamp(path.stat().st_mtime)

        if now - created >= ttl:
            removed += 1
            if args.dry_run:
                print(f"Would remove {path}")
            else:
                path.unlink(missing_ok=True)

    if args.dry_run:
        print(f"Dry run complete, {removed} files would be removed")
    else:
        print(f"Removed {removed} cache entries older than {args.ttl_days} days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
