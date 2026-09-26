"""디시 갤러리 브랜드 언급량·긍부정 분기별 분석.

사용 예:
    python run.py crawl  --gallery automata --since 2024-10-01 --out data/posts.jsonl
    python run.py report --in data/posts.jsonl --since 2024-10-01 --until 2026-09-30 --out report
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

from sentiment import MENTION_RE, analyze

DEFAULT_KEYWORDS = ["그세", "그랜드세이코", "그랜드 세이코", "grand seiko"]


def quarter_of(date: str) -> str:
    d = datetime.strptime(date[:10], "%Y-%m-%d")
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def all_quarters(since: datetime, until: datetime) -> list[str]:
    out, y, q = [], since.year, (since.month - 1) // 3 + 1
    while (y, q) <= (until.year, (until.month - 1) // 3 + 1):
        out.append(f"{y}Q{q}")
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)
    return out


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_report(posts: list[dict], since: datetime, until: datetime) -> tuple[list[dict], list[dict]]:
    quarters = all_quarters(since, until)
    agg: dict[str, dict] = {
        q: {"posts": 0, "mentions": 0, "positive": 0, "negative": 0, "neutral": 0, "score_sum": 0,
            "views": 0, "recommend": 0, "pos_terms": Counter(), "neg_terms": Counter(),
            "top_pos": [], "top_neg": []}
        for q in quarters
    }
    rows = []
    for p in posts:
        dt = datetime.strptime(p["date"], "%Y-%m-%d %H:%M:%S")
        if not (since <= dt <= until):
            continue
        # 검색은 부분문자열이라 오탐(그세끼 등)이 섞일 수 있어 다시 확인
        if not MENTION_RE.search(p["title"] + "\n" + p.get("body", "")):
            continue
        r = analyze(p["title"], p.get("body", ""))
        q = quarter_of(p["date"])
        a = agg[q]
        a["posts"] += 1
        a["mentions"] += r["mentions"]
        a[r["label"]] += 1
        a["score_sum"] += r["score"]
        a["views"] += p.get("views", 0)
        a["recommend"] += p.get("recommend", 0)
        a["pos_terms"].update(r["pos_terms"])
        a["neg_terms"].update(r["neg_terms"])
        item = (r["score"], p.get("views", 0), p["no"], p["title"])
        if r["label"] == "positive":
            a["top_pos"].append(item)
        elif r["label"] == "negative":
            a["top_neg"].append(item)
        rows.append({"no": p["no"], "date": p["date"], "quarter": q, "title": p["title"],
                     "views": p.get("views", 0), "recommend": p.get("recommend", 0),
                     "mentions": r["mentions"], "score": r["score"], "label": r["label"],
                     "pos_terms": " ".join(r["pos_terms"]), "neg_terms": " ".join(r["neg_terms"])})

    summary = []
    for q in quarters:
        a = agg[q]
        n = a["posts"]
        polar = a["positive"] + a["negative"]
        summary.append({
            "quarter": q,
            "posts": n,
            "mentions": a["mentions"],
            "positive": a["positive"],
            "neutral": a["neutral"],
            "negative": a["negative"],
            "pos_pct": round(100 * a["positive"] / n, 1) if n else 0.0,
            "neg_pct": round(100 * a["negative"] / n, 1) if n else 0.0,
            # 순감성지수: +100 = 전부 긍정, -100 = 전부 부정 (중립 제외)
            "net_sentiment": round(100 * (a["positive"] - a["negative"]) / polar, 1) if polar else 0.0,
            "avg_score": round(a["score_sum"] / n, 2) if n else 0.0,
            "avg_views": round(a["views"] / n) if n else 0,
            "avg_recommend": round(a["recommend"] / n, 1) if n else 0.0,
            "top_pos_terms": ", ".join(f"{t}({c})" for t, c in a["pos_terms"].most_common(5)),
            "top_neg_terms": ", ".join(f"{t}({c})" for t, c in a["neg_terms"].most_common(5)),
            "_top_pos": sorted(a["top_pos"], key=lambda x: (x[0], x[1]), reverse=True)[:3],
            "_top_neg": sorted(a["top_neg"], key=lambda x: (x[0], -x[1]))[:3],
        })
    return summary, rows


def bar(value: float, maximum: float, width: int = 20) -> str:
    return "█" * round(width * value / maximum) if maximum else ""


def write_outputs(summary, rows, out_dir, gallery, since, until, gallery_type="mgallery"):
    prefix = {"board": "board", "mgallery": "mgallery/board", "mini": "mini/board"}[gallery_type]
    os.makedirs(out_dir, exist_ok=True)
    cols = [k for k in summary[0] if not k.startswith("_")] if summary else []
    with open(os.path.join(out_dir, "quarterly_summary.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(summary)
    with open(os.path.join(out_dir, "posts_scored.csv"), "w", encoding="utf-8-sig", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    total = sum(s["posts"] for s in summary)
    max_posts = max((s["posts"] for s in summary), default=0)
    lines = [
        f"# 디시 {gallery} 갤러리 · 그랜드세이코 분기별 언급/감성 분석",
        "",
        f"- 기간: {since:%Y-%m-%d} ~ {until:%Y-%m-%d}",
        f"- 검색어: {', '.join(DEFAULT_KEYWORDS)} (제목+내용, 오탐 필터 적용)",
        f"- 분석 게시글: {total}건",
        "- 감성: 브랜드 언급 문장 ±1문장 대상 사전 기반 점수 (≥+2 긍정, ≤-2 부정)",
        "",
        "## 분기별 언급량",
        "",
        "| 분기 | 게시글 | 언급 횟수 | 추이 |",
        "|---|---:|---:|---|",
    ]
    for s in summary:
        lines.append(f"| {s['quarter']} | {s['posts']} | {s['mentions']} | {bar(s['posts'], max_posts)} |")
    lines += [
        "",
        "## 분기별 긍·부정",
        "",
        "| 분기 | 긍정 | 중립 | 부정 | 긍정% | 부정% | 순감성지수 | 평균조회 | 평균추천 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summary:
        lines.append(
            f"| {s['quarter']} | {s['positive']} | {s['neutral']} | {s['negative']} | {s['pos_pct']} | "
            f"{s['neg_pct']} | {s['net_sentiment']:+} | {s['avg_views']} | {s['avg_recommend']} |"
        )
    lines += ["", "## 분기별 주요 표현과 대표 글", ""]
    for s in summary:
        lines.append(f"### {s['quarter']}")
        lines.append(f"- 긍정 키워드: {s['top_pos_terms'] or '-'}")
        lines.append(f"- 부정 키워드: {s['top_neg_terms'] or '-'}")
        for sc, v, no, title in s["_top_pos"]:
            lines.append(f"- 👍 ({sc:+}) [{title}](https://gall.dcinside.com/{prefix}/view/?id={gallery}&no={no})")
        for sc, v, no, title in s["_top_neg"]:
            lines.append(f"- 👎 ({sc:+}) [{title}](https://gall.dcinside.com/{prefix}/view/?id={gallery}&no={no})")
        lines.append("")
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines[: 12 + len(summary) * 2 + 6]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crawl")
    c.add_argument("--gallery", default="automata")
    c.add_argument("--gallery-type", choices=["board", "mgallery", "mini"])
    c.add_argument("--keywords", nargs="+", default=DEFAULT_KEYWORDS)
    c.add_argument("--since", default="2024-10-01")
    c.add_argument("--out", default="data/posts.jsonl")
    c.add_argument("--no-body", action="store_true", help="본문 수집 생략(제목만 분석)")
    c.add_argument("--delay", type=float, default=1.0)
    r = sub.add_parser("report")
    r.add_argument("--in", dest="inp", default="data/posts.jsonl")
    r.add_argument("--gallery", default="automata")
    r.add_argument("--gallery-type", choices=["board", "mgallery", "mini"], default="mgallery")
    r.add_argument("--since", default="2024-10-01")
    r.add_argument("--until", default="2026-09-30")
    r.add_argument("--out", default="report")
    args = ap.parse_args()

    if args.cmd == "crawl":
        from crawler import crawl

        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        n = crawl(args.gallery, args.keywords, datetime.fromisoformat(args.since), args.out,
                  args.gallery_type, not args.no_body, args.delay)
        print(f"총 {n}건 저장 → {args.out}")
    else:
        since = datetime.fromisoformat(args.since)
        until = datetime.fromisoformat(args.until).replace(hour=23, minute=59, second=59)
        summary, rows = build_report(load(args.inp), since, until)
        write_outputs(summary, rows, args.out, args.gallery, since, until, args.gallery_type)


if __name__ == "__main__":
    main()
