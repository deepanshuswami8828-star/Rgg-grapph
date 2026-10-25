"""
Unattended CLI Data Refresh Runner for Multi-Stock RRG Application.
Zero Streamlit imports. Idempotent and safe for automated scheduling.
Exit code:
  0 = SUCCESS or NO_NEW_SESSION (ok)
  1 = FAILED (error)
"""
import argparse
import os
import sys

# Ensure root directory is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

import data_pipeline as dp


def main():
    parser = argparse.ArgumentParser(description="Refresh RRG price datasets from Yahoo Finance.")
    parser.add_argument("--force", action="store_true", help="Force refresh even if no new completed session is due.")
    parser.add_argument("--include-provisional", action="store_true", help="Include provisional candle during market hours.")
    args = parser.parse_args()

    print("=== Starting RRG Data Refresh ===")
    res = dp.refresh_data(force=args.force, include_provisional=args.include_provisional)
    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")

    print(f"Status:  {status}")
    print(f"Message: {message}")

    if status == "SUCCESS":
        # daily highs for the take-profit analysis; a failure here never fails the close refresh
        failed = {t: s for t, s in dp.refresh_highs().items() if not s.startswith("OK")}
        print("Highs:   " + ("all stocks updated" if not failed else f"not updated for {failed}"))

    if status in ("SUCCESS", "NO_NEW_SESSION", "SKIPPED"):
        print("Refresh completed cleanly (Exit 0).")
        sys.exit(0)
    else:
        print("Refresh encountered an error (Exit 1).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
