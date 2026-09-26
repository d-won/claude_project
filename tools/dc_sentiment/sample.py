"""분기별 층화 무작위 표본 추출 → 사람이(또는 LLM이) 읽고 라벨링할 텍스트 파일 생성.

라벨 파일(TSV) 형식:  no <TAB> label <TAB> aspects
  label  : P(긍정) N(부정) M(혼재) 0(중립/정보·질문)
  aspects: 쉼표 구분 — 디자인, 마감, 무브, 가격, 감가, 브랜드, 착용감, AS, 비교
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime

from run import quarter_of
from sentiment import MENTION_RE, target_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/posts.jsonl")
    ap.add_argument("--per-quarter", type=int, default=60)
    ap.add_argument("--since", default="2024-10-01")
    ap.add_argument("--until", default="2026-09-30")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/sample.txt")
    ap.add_argument("--chars", type=int, default=260)
    args = ap.parse_args()

    since = datetime.fromisoformat(args.since)
    until = datetime.fromisoformat(args.until).replace(hour=23, minute=59, second=59)
    by_q: dict[str, list[dict]] = {}
    with open(args.inp, encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            dt = datetime.strptime(p["date"], "%Y-%m-%d %H:%M:%S")
            if since <= dt <= until and MENTION_RE.search(p["title"] + "\n" + p.get("body", "")):
                by_q.setdefault(quarter_of(p["date"]), []).append(p)

    rng = random.Random(args.seed)
    with open(args.out, "w", encoding="utf-8") as out:
        for q in sorted(by_q):
            pool = sorted(by_q[q], key=lambda p: p["no"])
            for p in rng.sample(pool, min(args.per_quarter, len(pool))):
                text = target_text(p["title"], p.get("body", "")).replace("\n", " / ")
                out.write(f"{p['no']}\t{q}\t{text[: args.chars]}\n")
    print({q: min(args.per_quarter, len(v)) for q, v in sorted(by_q.items())})


if __name__ == "__main__":
    main()
