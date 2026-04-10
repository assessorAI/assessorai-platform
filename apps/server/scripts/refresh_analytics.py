#!/usr/bin/env python3
"""
Refresh analytics metrics for all mandatos and users.
Can be run manually or via cron job.

Usage:
    python scripts/refresh_analytics.py [--month YYYY-MM]
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from services.analytics import refresh_all_metrics


def main():
    parser = argparse.ArgumentParser(description="Refresh analytics metrics")
    parser.add_argument(
        "--month",
        help="Reference month in YYYY-MM format. Defaults to current month.",
    )
    args = parser.parse_args()
    
    ref_date = None
    if args.month:
        try:
            ref_date = datetime.strptime(args.month, "%Y-%m")
        except ValueError:
            print(f"Error: Invalid date format '{args.month}'. Use YYYY-MM")
            return 1
    
    session = SessionLocal()
    try:
        print("Refreshing analytics metrics...")
        mandatos_count, users_count = refresh_all_metrics(session, ref_date)
        print(f"✓ Updated {mandatos_count} mandatos")
        print(f"✓ Updated {users_count} users")
        print(f"✓ Reference date: {ref_date or datetime.now()}")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
