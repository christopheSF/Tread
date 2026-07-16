#!/usr/bin/env python3
"""
Western States Contracting — CSV → CRLF file processing.

Replaces the manual Notepad++ steps (Edit → EOL Conversion → Windows CRLF → Save)
from the SOP. Takes the downloaded Western billing file, normalizes every line
ending to Windows CRLF, and writes a copy named for the billing period — ready
to send to the requestor.

USAGE
  # Convert a specific file, name it for a period:
  python3 western-crlf.py ~/Downloads/western-billing.csv --period 2026-07-15

  # No file given → picks the newest CSV in ~/Downloads (handy right after download):
  python3 western-crlf.py --period 2026-07-15

  # No period given → keeps the original name with a _CRLF suffix:
  python3 western-crlf.py ~/Downloads/western-billing.csv

OUTPUT
  Writes <name>_Western_Billing_<period>.csv next to the input (or --out PATH),
  verifies the result is 100% CRLF, and prints the path to send.
"""

import argparse
import glob
import os
import sys


def newest_csv(folder):
    csvs = glob.glob(os.path.join(os.path.expanduser(folder), "*.csv"))
    return max(csvs, key=os.path.getmtime) if csvs else None


def to_crlf(raw: bytes) -> bytes:
    # Normalize any mix of CRLF / lone CR / lone LF to a single clean CRLF.
    # 1) collapse existing CRLF to LF, 2) collapse lone CR to LF, 3) LF -> CRLF.
    text = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return text.replace(b"\n", b"\r\n")


def main():
    p = argparse.ArgumentParser(description="Convert the Western billing file to Windows CRLF.")
    p.add_argument("infile", nargs="?", help="Input CSV. Omit to use the newest CSV in --from.")
    p.add_argument("--period", help="Billing period label for the output filename, e.g. 2026-07-15.")
    p.add_argument("--from", dest="from_dir", default="~/Downloads",
                   help="Folder to auto-pick the newest CSV from (default: ~/Downloads).")
    p.add_argument("--out", help="Explicit output path (overrides the generated name).")
    args = p.parse_args()

    infile = args.infile or newest_csv(args.from_dir)
    if not infile:
        sys.exit(f"No input file given and no .csv found in {args.from_dir}.")
    infile = os.path.expanduser(infile)
    if not os.path.isfile(infile):
        sys.exit(f"File not found: {infile}")

    with open(infile, "rb") as f:
        raw = f.read()

    converted = to_crlf(raw)

    if args.out:
        outfile = os.path.expanduser(args.out)
    else:
        base = os.path.dirname(infile)
        suffix = f"Western_Billing_{args.period}" if args.period else "Western_Billing_CRLF"
        outfile = os.path.join(base, f"{suffix}.csv")

    with open(outfile, "wb") as f:
        f.write(converted)

    # Verify: every LF must be preceded by CR, and no lone CR remains.
    check = open(outfile, "rb").read()
    lone_lf = check.count(b"\n") - check.count(b"\r\n")
    lone_cr = check.count(b"\r") - check.count(b"\r\n")
    lines = check.count(b"\r\n")
    ok = lone_lf == 0 and lone_cr == 0

    print(f"In:   {infile}")
    print(f"Out:  {outfile}")
    print(f"Lines (CRLF-terminated): {lines}")
    if ok:
        print("✓ Clean Windows CRLF — ready to send.")
    else:
        print(f"⚠ Check failed: {lone_lf} lone LF, {lone_cr} lone CR remain.")
        sys.exit(1)


if __name__ == "__main__":
    main()
