#!/usr/bin/env python3
"""Print quic-interop-runner results as Markdown, a row per test.

Usage: summary.py CLIENT=result.json ...
"""

import html
import json
import os
import re
import sys

MARKS = {"succeeded": "✓", "unsupported": "–", "failed": "✗"}
UNKNOWN = "?"
# Test order of https://interop.seemann.io/
ORDER = "H DC LR C20 M S R Z 3 B U A L1 L2 C1 C2 6 E V2 CM BP BA".split()


def entries(node):
    if isinstance(node, dict):
        if "abbr" in node and node.get("result") is not None:
            yield node
        for value in node.values():
            yield from entries(value)
    elif isinstance(node, list):
        for value in node:
            yield from entries(value)


def load(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def detail(text):
    match = re.fullmatch(r"(\S+) \(± (\S+)\) (\S+)", text)
    return (f"{match[1]} ±{match[2]}", match[3]) if match else (text, "")


def unit(abbr):
    units = {detail(m[abbr]["details"])[1] for _, _, m in clients
             if abbr in m and m[abbr].get("details")}
    return units.pop() if len(units) == 1 else ""


def escape(text):
    return html.escape(text).replace("|", "&#124;")


def test(abbr, suffix):
    text = escape(abbr) + suffix
    name = names.get(abbr, "")
    desc = descs.get(abbr)
    tip = f"{name}: {desc}" if name and desc else name or desc
    return f'<span title="{escape(tip)}">{text}</span>' if tip else text


def row(cells):
    return "| " + " | ".join(cells) + " |"


def links():
    urls = {}
    openssl_lts = os.environ.get("OPENSSL_LTS_BRANCH", "openssl-lts")
    for name, var in (("openssl-master", "OPENSSL_MASTER"),
                      (openssl_lts, "OPENSSL_LTS")):
        commit = os.environ.get(var)
        if commit:
            url = f"https://github.com/openssl/openssl/commit/{commit}"
            urls[name] = (url, "")
    for name in ("ngtcp2", "nginx"):
        url = os.environ.get(f"{name.upper()}_URL")
        image = os.environ.get(f"{name.upper()}_IMAGE", "")
        _, _, digest = image.partition("@")
        if url:
            urls[name] = (url, digest if url.endswith("/versions") else "")
    return urls


def run_page():
    server = os.environ.get("GITHUB_SERVER_URL")
    repo = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not (server and repo and run_id):
        return ""
    return f"{server}/{repo}/actions/runs/{run_id}"


def mark(result):
    text = MARKS.get(result, UNKNOWN)
    return f"[{text}]({run_url})" if result == "failed" and run_url else text


def blank(tests, measurements):
    return "" if tests or measurements else "N/A"


def link(name):
    if name not in urls:
        return name
    url, digest = urls[name]
    text = f"[{name}]({url})"
    return f"{text} ({digest})" if digest else text


urls = links()
run_url = run_page()
names = {}
descs = {}
clients = []
for arg in sys.argv[1:]:
    client, path = arg.split("=", 1)
    result = load(path)
    meta = result.get("tests")
    for abbr, entry in meta.items() if isinstance(meta, dict) else ():
        if isinstance(entry, dict) and entry.get("desc"):
            descs.setdefault(abbr, entry["desc"])
    tests = {}
    for entry in entries(result.get("results")):
        tests[entry["abbr"]] = entry
        names.setdefault(entry["abbr"], entry.get("name", ""))
    measurements = {}
    for entry in entries(result.get("measurements")):
        measurements[entry["abbr"]] = entry
        names.setdefault(entry["abbr"], entry.get("name", ""))
    clients.append((client, tests, measurements))

order = [a for a in names if any(a in tests for _, tests, _ in clients)]
order.sort(key=lambda a: ORDER.index(a) if a in ORDER else len(ORDER))
metrics = [a for a in names if a not in order]

number = os.environ.get("GITHUB_RUN_NUMBER")
if number and run_url:
    print(f"Run: [#{number}]({run_url})")
    print()
print(f"server: {link('nginx')}")
print()
print(row(["test"] + [link(c) for c, _, _ in clients]))
print("|---|" + ":--:|" * len(clients))
for abbr in order:
    cells = []
    for _, tests, measurements in clients:
        entry = tests.get(abbr)
        cells.append(mark(entry["result"]) if entry
                     else blank(tests, measurements))
    print(row([test(abbr, "")] + cells))
for abbr in metrics:
    found = unit(abbr)
    cells = []
    for _, tests, measurements in clients:
        entry = measurements.get(abbr)
        cell = blank(tests, measurements)
        if entry:
            cell = mark(entry["result"])
            if entry.get("details"):
                value, found_unit = detail(entry["details"])
                value = escape(value if found_unit == found
                               else entry["details"])
                cell = value if entry["result"] == "succeeded" \
                    else f"{cell} {value}"
        cells.append(cell)
    print(row([test(abbr, f" ({found})" if found else "")] + cells))
print()
print("<details><summary>Test names</summary>")
print()
for abbr in order + metrics:
    desc = descs.get(abbr)
    print(f"- **{abbr}** {names[abbr]}" + (f": {desc}" if desc else ""))
print()
print("</details>")
