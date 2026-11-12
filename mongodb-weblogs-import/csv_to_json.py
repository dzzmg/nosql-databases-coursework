#!/usr/bin/env python3
"""
csv_to_json.py - converts web server logs from CSV to JSON for MongoDB.

Practical Work #3, Task 2.

Every log entry must have four fields:
    URL        - the requested resource, e.g. /courses/databases
    IP         - IPv4 address of the visitor, e.g. 192.168.1.5
    timeStamp  - date and time of the visit, e.g. 2026-10-01 14:30:00
    timeSpent  - time spent on the page, in whole seconds, e.g. 35

Usage:
    python3 csv_to_json.py INPUT.csv OUTPUT.json [--errors ERRORS.csv]

Valid rows are written to OUTPUT.json as a JSON array. The timeStamp is written
in MongoDB Extended JSON ({"$date": "..."}), so it is stored in MongoDB as a real
date and can be used in date range queries.
Invalid rows are skipped; a message is printed for each of them, and with
--errors they are also saved to a separate CSV file.

Exit codes: 0 = done (some rows may be skipped), 1 = fatal error (nothing written).
"""

import argparse
import csv
import ipaddress
import json
import re
import sys
from datetime import datetime, timezone

REQUIRED_FIELDS = ["URL", "IP", "timeStamp", "timeSpent"]

# URL: a path that starts with "/" (e.g. /courses?id=5) or a full http(s) address; no spaces
URL_PATTERN = re.compile(r"^(https?://[^\s/]+)?/[^\s]*$")

# accepted timestamp formats
TIME_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]


class RowError(Exception):
    """Raised when one row of the CSV file is invalid."""


def parse_args():
    parser = argparse.ArgumentParser(description="Convert web server logs from CSV to JSON.")
    parser.add_argument("input", help="path to the input CSV file")
    parser.add_argument("output", help="path to the output JSON file")
    parser.add_argument("--errors", help="optional CSV file for the rejected rows")
    return parser.parse_args()


def fail(message):
    """Print a fatal error and stop the program."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def check_url(value):
    if not value:
        raise RowError("URL is missing")
    if not URL_PATTERN.match(value):
        raise RowError(f"invalid URL '{value}' (must start with '/' or http(s):// and contain no spaces)")
    return value


def check_ip(value):
    if not value:
        raise RowError("IP is missing")
    try:
        # ip_address() checks every number is 0-255 and rejects letters
        return str(ipaddress.IPv4Address(value))
    except ValueError:
        raise RowError(f"invalid IP address '{value}'")


def check_timestamp(value):
    if not value:
        raise RowError("timeStamp is missing")
    for fmt in TIME_FORMATS:
        try:
            # strptime also rejects impossible dates such as 2026-02-30
            moment = datetime.strptime(value, fmt)
            return moment.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    raise RowError(f"invalid timeStamp '{value}' (expected YYYY-MM-DD HH:MM:SS and a real date)")


def check_time_spent(value):
    if not value:
        raise RowError("timeSpent is missing")
    if not re.fullmatch(r"-?\d+", value):
        raise RowError(f"timeSpent '{value}' is not a whole number of seconds")
    seconds = int(value)
    if seconds < 0:
        raise RowError(f"timeSpent cannot be negative ({seconds})")
    return seconds


def convert_row(row, header):
    """Check one CSV row and return a dictionary for JSON, or raise RowError."""
    if len(row) < len(header):
        raise RowError(f"too few columns ({len(row)} instead of {len(header)})")
    if len(row) > len(header):
        raise RowError(f"too many columns ({len(row)} instead of {len(header)})")

    values = {name: cell.strip() for name, cell in zip(header, row)}   # remove extra spaces
    return {
        "URL": check_url(values["URL"]),
        "IP": check_ip(values["IP"]),
        "timeStamp": {"$date": check_timestamp(values["timeStamp"])},
        "timeSpent": check_time_spent(values["timeSpent"]),
    }


def read_header(reader, path):
    """Read the first line and make sure all four required columns exist."""
    try:
        header = [name.strip() for name in next(reader)]
    except StopIteration:
        fail(f"the file '{path}' is empty")
    # allow any letter case and any column order: map e.g. "url" -> "URL"
    known = {name.lower(): name for name in REQUIRED_FIELDS}
    normalised = [known.get(name.lower(), name) for name in header]
    missing = [name for name in REQUIRED_FIELDS if name not in normalised]
    if missing:
        fail(f"required column(s) missing in the header: {', '.join(missing)}. "
             f"The first line must contain: {','.join(REQUIRED_FIELDS)}")
    return normalised


def main():
    args = parse_args()

    # 1. open the input file
    try:
        source = open(args.input, newline="", encoding="utf-8-sig")
    except FileNotFoundError:
        fail(f"input file '{args.input}' not found")
    except PermissionError:
        fail(f"no permission to read '{args.input}'")
    except IsADirectoryError:
        fail(f"'{args.input}' is a folder, not a file")

    documents, rejected = [], []
    empty_lines = 0

    # 2. read and check the rows one by one
    with source:
        reader = csv.reader(source)
        try:
            header = read_header(reader, args.input)
            for row in reader:
                line = reader.line_num
                if not row or all(not cell.strip() for cell in row):
                    empty_lines += 1
                    print(f"Line {line}: empty line - skipped", file=sys.stderr)
                    continue
                try:
                    documents.append(convert_row(row, header))
                except RowError as error:
                    rejected.append((line, row, str(error)))
                    print(f"Line {line}: {error} - row skipped", file=sys.stderr)
        except UnicodeDecodeError:
            fail(f"'{args.input}' is not a UTF-8 text file")
        except csv.Error as error:
            fail(f"CSV format error on line {reader.line_num}: {error}")

    if not documents:
        fail("no valid rows found - the output file was not created")

    # 3. write the valid rows as JSON
    try:
        with open(args.output, "w", encoding="utf-8") as target:
            json.dump(documents, target, indent=2, ensure_ascii=False)
    except OSError as error:
        fail(f"cannot write '{args.output}': {error.strerror}")

    # 4. optionally save the rejected rows, with the reason, for checking
    if args.errors and rejected:
        try:
            with open(args.errors, "w", newline="", encoding="utf-8") as bad:
                writer = csv.writer(bad)
                writer.writerow(["line", "reason", "original_row"])
                for line, row, reason in rejected:
                    writer.writerow([line, reason, ",".join(row)])
        except OSError as error:
            print(f"WARNING: cannot write the errors file: {error.strerror}", file=sys.stderr)

    # 5. summary for the user
    total = len(documents) + len(rejected) + empty_lines
    print("-" * 50)
    print(f"Rows read:       {total}")
    print(f"Converted:       {len(documents)}")
    print(f"Skipped (error): {len(rejected)}")
    print(f"Empty lines:     {empty_lines}")
    print(f"Output file:     {args.output}")
    if args.errors and rejected:
        print(f"Rejected rows:   {args.errors}")


if __name__ == "__main__":
    main()
