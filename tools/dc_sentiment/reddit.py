"""Reddit 수집기 (Arctic Shift 아카이브 API).

reddit.com 은 클라우드 IP 를 403/429 로 막기 때문에 공개 아카이브인 Arctic Shift 를 쓴다.
  - r/GrandSeikos: 서브 전체가 그세 이야기 → 글 전수
  - r/Watches    : 글 전수 수집 후 'grand seiko' 언급 글만 사용 (댓글은 규모상 제외)

사용 예:
    python reddit.py collect --out data/reddit.jsonl --since 2024-10-01
    python reddit.py report --in data/reddit.jsonl --out results_reddit
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

import requests

API = "https://arctic-shift.photon-reddit.com/api"
MENTION_RE = re.compile(r"grand\s*seiko|\bGS\s?(?:SBG|SLG)|\bSBG[A-Z]\d{3}|\bSLG[A-Z]\d{3}", re.IGNORECASE)

# (종류, 서브레딧, 검색 파라미터) — 검색 파라미터가 없으면 서브 전수
TARGETS = [
    # r/GrandSeiko 는 글 52개짜리 제한 서브, 실제 커뮤니티는 r/GrandSeikos(구독 6만)
    ("post", "GrandSeikos", {}),
    # r/Watches 는 활동량이 많아 아카이브의 키워드 검색이 지원되지 않는다 → 글 전수 수집 후 로컬 필터
    ("post", "Watches", {}),
]
FIELDS = {
    "post": "id,created_utc,title,selftext,score,num_comments,subreddit,link_flair_text",
    "comment": "id,created_utc,body,score,subreddit,link_id",
}


def _get(path: str, params: dict, tries: int = 6) -> list[dict]:
    for attempt in range(tries):
        try:
            r = requests.get(f"{API}/{path}", params=params, timeout=60)
            if r.status_code == 200:
                return r.json().get("data") or []
            msg = r.text[:120]
        except requests.RequestException as e:
            msg = str(e)
        wait = 5 * 2 ** attempt
        print(f"  재시도 {attempt + 1}/{tries} ({msg}) {wait}s 후", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"Arctic Shift 요청 실패: {path} {params}")


def ping() -> bool:
    try:
        r = requests.get(f"{API}/posts/search", params={"subreddit": "GrandSeiko", "limit": 1}, timeout=60)
        return r.status_code == 200 and bool(r.json().get("data"))
    except requests.RequestException:
        return False


def collect(out_path: str, since: str, until: str | None = None, only: list[str] | None = None):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    seen = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            seen = {(json.loads(l)["kind"], json.loads(l)["id"]) for l in f if l.strip()}
    with open(out_path, "a", encoding="utf-8") as out:
        for kind, sub, extra in TARGETS:
            if only and sub not in only:
                continue
            after = int(datetime.fromisoformat(since).replace(tzinfo=timezone.utc).timestamp())
            before = until
            n = 0
            while True:
                params = {"subreddit": sub, "after": after, "limit": 100, "sort": "asc", "fields": FIELDS[kind], **extra}
                if before:
                    params["before"] = before
                rows = _get("posts/search" if kind == "post" else "comments/search", params)
                if not rows:
                    break
                for r in rows:
                    if (kind, r["id"]) in seen:
                        continue
                    seen.add((kind, r["id"]))
                    r["kind"] = kind
                    out.write(json.dumps(r, ensure_ascii=False) + "\n")
                    n += 1
                last = max(int(r["created_utc"]) for r in rows)
                if last <= after:
                    break
                after = last
                if n and n % 1000 < 100:
                    print(f"  [{kind} r/{sub}] {n}건, {datetime.fromtimestamp(last, timezone.utc):%Y-%m-%d}", flush=True)
                time.sleep(0.5)
            out.flush()
            print(f"[{kind} r/{sub}] {n}건", flush=True)


def collect_windows(sub: str, start: str, end: str, out_dir: str, workers: int = 4):
    """활동량 많은 서브용: 월 단위 구간을 병렬로 받는다. 구간별 파일이라 재실행 시 완료 구간은 건너뛴다."""
    from concurrent.futures import ThreadPoolExecutor

    os.makedirs(out_dir, exist_ok=True)
    s = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    e = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    windows = []
    while s < e:
        n = (s.replace(day=1) + __import__("datetime").timedelta(days=32)).replace(day=1)
        windows.append((s, min(n, e)))
        s = n

    def work(w):
        a, b = w
        path = os.path.join(out_dir, f"{sub}_{a:%Y%m%d}.jsonl")
        if os.path.exists(path + ".done"):
            return
        after, n = int(a.timestamp()), 0
        with open(path, "w", encoding="utf-8") as out:
            while True:
                rows = _get("posts/search", {"subreddit": sub, "after": after, "before": int(b.timestamp()),
                                             "limit": "auto", "sort": "asc", "fields": FIELDS["post"]})
                if not rows:
                    break
                for r in rows:
                    r["kind"] = "post"
                    out.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += len(rows)
                last = max(int(r["created_utc"]) for r in rows)
                if last <= after:
                    break
                after = last
                time.sleep(1)
        open(path + ".done", "w").write(str(n))
        print(f"[r/{sub}] {a:%Y-%m} {n}건", flush=True)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(work, windows))
    print(f"[r/{sub}] 전체 완료", flush=True)


def quarter(ts: int) -> str:
    d = datetime.fromtimestamp(int(ts), timezone.utc)
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def text_of(r: dict) -> str:
    return (r.get("title", "") + "\n" + (r.get("selftext") or r.get("body") or "")).strip()


def report(in_path: str, out_dir: str):
    rows = [json.loads(l) for l in open(in_path, encoding="utf-8") if l.strip()]
    os.makedirs(out_dir, exist_ok=True)
    table = defaultdict(Counter)
    for r in rows:
        if r.get("selftext") in ("[removed]", "[deleted]") and not r.get("title"):
            continue
        key = f"{r['kind']} r/{r['subreddit']}"
        if r["subreddit"].lower() == "watches" and not MENTION_RE.search(text_of(r)):
            continue
        table[key][quarter(r["created_utc"])] += 1
    qs = sorted({q for c in table.values() for q in c})
    with open(os.path.join(out_dir, "reddit_volume.csv"), "w", encoding="utf-8-sig") as f:
        f.write("source," + ",".join(qs) + "\n")
        for k, c in sorted(table.items()):
            f.write(k + "," + ",".join(str(c[q]) for q in qs) + "\n")
    for k, c in sorted(table.items()):
        print(k, [c[q] for q in qs])
    return table, qs


def sample(in_path: str, out_path: str, per_quarter: int, seed: int, sub: str, chars: int = 300):
    import random

    rows = [json.loads(l) for l in open(in_path, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r["subreddit"].lower() == sub.lower() and MENTION_RE.search(text_of(r))
            and (r.get("body") or r.get("title")) not in ("[removed]", "[deleted]")]
    by_q = defaultdict(list)
    for r in rows:
        by_q[quarter(r["created_utc"])].append(r)
    rng = random.Random(seed)
    with open(out_path, "w", encoding="utf-8") as out:
        for q in sorted(by_q):
            pool = sorted(by_q[q], key=lambda r: r["id"])
            for r in rng.sample(pool, min(per_quarter, len(pool))):
                t = text_of(r).replace("\n", " / ")
                # 댓글은 언급 주변만 잘라서 보여준다
                m = MENTION_RE.search(t)
                start = max(0, (m.start() if m else 0) - chars // 3)
                out.write(f"{r['kind'][0]}{r['id']}\t{q}\t{t[start:start + chars]}\n")
    print({q: min(per_quarter, len(v)) for q, v in sorted(by_q.items())})


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--out", default="data/reddit.jsonl")
    c.add_argument("--since", default="2024-10-01")
    c.add_argument("--only", nargs="+", help="수집할 서브레딧만 지정")
    w = sub.add_parser("windows")
    w.add_argument("--sub", default="Watches")
    w.add_argument("--start", default="2024-11-15")
    w.add_argument("--end", default="2026-09-28")
    w.add_argument("--out-dir", default="data/reddit_watches")
    w.add_argument("--workers", type=int, default=4)
    sub.add_parser("ping")
    r = sub.add_parser("report")
    r.add_argument("--in", dest="inp", default="data/reddit.jsonl")
    r.add_argument("--out", default="results_reddit")
    s = sub.add_parser("sample")
    s.add_argument("--in", dest="inp", default="data/reddit.jsonl")
    s.add_argument("--out", default="data/reddit_sample.txt")
    s.add_argument("--sub", default="Watches")
    s.add_argument("--per-quarter", type=int, default=50)
    s.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    if a.cmd == "collect":
        collect(a.out, a.since, only=a.only)
    elif a.cmd == "windows":
        collect_windows(a.sub, a.start, a.end, a.out_dir, a.workers)
    elif a.cmd == "ping":
        print("OK" if ping() else "DOWN")
    elif a.cmd == "report":
        report(a.inp, a.out)
    else:
        sample(a.inp, a.out, a.per_quarter, a.seed, a.sub)


if __name__ == "__main__":
    main()
