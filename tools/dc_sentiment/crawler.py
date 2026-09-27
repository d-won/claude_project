"""디시인사이드 갤러리 키워드 검색 크롤러.

검색 결과 목록(제목+내용 검색)을 search_pos 블록 단위로 거슬러 올라가며 수집하고,
각 게시글 본문을 가져와 JSONL 로 저장한다.
"""
from __future__ import annotations

import json
import random
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://gall.dcinside.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


@dataclass
class Post:
    no: int
    title: str
    date: str  # "YYYY-MM-DD HH:MM:SS"
    views: int
    recommend: int
    keyword: str
    body: str = ""


class DCClient:
    def __init__(self, gallery_id: str, gallery_type: str | None = None, delay: float = 1.0):
        self.gallery_id = gallery_id
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.gallery_type = gallery_type or self._detect_type()

    # 일반 갤러리 = board, 마이너 = mgallery/board, 미니 = mini/board
    def _prefix(self, gtype: str | None = None) -> str:
        gtype = gtype or self.gallery_type
        return {"board": "/board", "mgallery": "/mgallery/board", "mini": "/mini/board"}[gtype]

    def _get(self, url: str, **params) -> str:
        for attempt in range(4):
            try:
                r = self.session.get(url, params=params, timeout=15)
                if r.status_code == 200:
                    time.sleep(self.delay + random.random() * self.delay)
                    return r.text
            except requests.RequestException:
                pass
            time.sleep(2 ** (attempt + 1))
        raise RuntimeError(f"요청 실패: {url} {params}")

    def _detect_type(self) -> str:
        for gtype in ("mgallery", "board", "mini"):
            try:
                r = self.session.get(
                    BASE + self._prefix(gtype) + "/lists/", params={"id": self.gallery_id}, timeout=15
                )
            except requests.RequestException:
                continue
            # 없는 갤러리는 리다이렉트/경고 스크립트를 돌려준다
            if r.status_code == 200 and "gall_list" in r.text:
                return gtype
        raise RuntimeError(f"갤러리 '{self.gallery_id}' 를 찾을 수 없습니다")

    def search(self, keyword: str, since: datetime, max_blocks: int = 500):
        """keyword 검색 결과를 최신순으로 since 이전 글이 나올 때까지 yield."""
        search_pos = None
        seen: set[int] = set()
        for _ in range(max_blocks):
            page = 1
            oldest_in_block = None
            next_pos = None
            while True:
                params = {
                    "id": self.gallery_id,
                    "s_type": "search_subject_memo",
                    "s_keyword": keyword,
                    "page": page,
                }
                if search_pos is not None:
                    params["search_pos"] = search_pos
                html = self._get(BASE + self._prefix() + "/lists/", **params)
                rows, next_pos_found, has_next_page = parse_list(html)
                next_pos = next_pos_found or next_pos
                for p in rows:
                    oldest_in_block = p.date
                    if p.no in seen:
                        continue
                    seen.add(p.no)
                    if datetime.strptime(p.date, "%Y-%m-%d %H:%M:%S") >= since:
                        p.keyword = keyword
                        yield p
                if not has_next_page or not rows:
                    break
                page += 1
            print(f"  [{keyword}] search_pos={search_pos} {page}페이지, 가장 오래된 글 {oldest_in_block}", flush=True)
            if oldest_in_block and datetime.strptime(oldest_in_block, "%Y-%m-%d %H:%M:%S") < since:
                return
            if next_pos is None:
                return
            search_pos = next_pos

    def fetch_body(self, no: int, retries: int = 3) -> str:
        # 과도한 요청 시 본문이 빈 페이지가 돌아온다. 이미지·투표도 없는 빈 본문이면 쉬었다가 재시도
        for attempt in range(retries + 1):
            html = self._get(BASE + self._prefix() + "/view/", id=self.gallery_id, no=no)
            body = parse_body(html)
            if body or has_media(html):
                return body
            time.sleep(5 * (attempt + 1))
        return ""


def _int(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text or "")
    return int(digits) if digits else 0


def parse_list(html: str) -> tuple[list[Post], int | None, bool]:
    """목록 HTML → (게시글들, 다음 검색블록 search_pos, 다음 페이지 존재 여부)."""
    soup = BeautifulSoup(html, "html.parser")
    posts: list[Post] = []
    for tr in soup.select("tr.ub-content"):
        no = _int(tr.get("data-no", ""))
        if not no:
            continue
        # 공지/설문/AD 제외
        num_td = tr.select_one("td.gall_num")
        if num_td and not num_td.get_text(strip=True).isdigit():
            continue
        a = tr.select_one("td.gall_tit a")
        date_td = tr.select_one("td.gall_date")
        if not a or not date_td:
            continue
        date = date_td.get("title") or date_td.get_text(strip=True)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", date):
            continue
        posts.append(
            Post(
                no=no,
                title=a.get_text(" ", strip=True),
                date=date,
                views=_int(tr.select_one("td.gall_count").get_text() if tr.select_one("td.gall_count") else ""),
                recommend=_int(
                    tr.select_one("td.gall_recommend").get_text() if tr.select_one("td.gall_recommend") else ""
                ),
                keyword="",
            )
        )

    next_pos = None
    nxt = soup.select_one("a.search_next")
    if nxt and nxt.get("href"):
        qs = parse_qs(urlparse(urljoin(BASE, nxt["href"])).query)
        if "search_pos" in qs:
            next_pos = int(qs["search_pos"][0])

    # 페이징 박스가 여러 개일 수 있어 링크의 page 파라미터로 판단한다 (search_next 제외)
    has_next_page = False
    for box in soup.select("div.bottom_paging_box"):
        em = box.select_one("em")
        if not em:
            continue
        cur = _int(em.get_text())
        for a in box.select("a[href]"):
            if "search_next" in (a.get("class") or []):
                continue
            qs = parse_qs(urlparse(urljoin(BASE, a["href"])).query)
            if "page" in qs and _int(qs["page"][0]) > cur:
                has_next_page = True
    return posts, next_pos, has_next_page


def has_media(html: str) -> bool:
    div = BeautifulSoup(html, "html.parser").select_one("div.write_div")
    return bool(div and div.select("img, iframe, video, embed"))


def parse_body(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    div = soup.select_one("div.write_div")
    return div.get_text("\n", strip=True) if div else ""


def crawl(gallery_id, keywords, since, out_path, gallery_type=None, fetch_bodies=True, delay=1.0):
    client = DCClient(gallery_id, gallery_type, delay)
    posts: dict[int, Post] = {}
    for kw in keywords:
        n = 0
        for p in client.search(kw, since):
            if p.no not in posts:
                posts[p.no] = p
                n += 1
        print(f"[{kw}] 신규 {n}건 (누적 {len(posts)})")
    with open(out_path, "w", encoding="utf-8") as f:
        for i, p in enumerate(sorted(posts.values(), key=lambda x: x.no), 1):
            if fetch_bodies:
                try:
                    p.body = client.fetch_body(p.no)
                except RuntimeError as e:
                    print(f"본문 실패 {p.no}: {e}")
                if i % 50 == 0:
                    print(f"본문 {i}/{len(posts)}")
            f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
    return len(posts)


def fetch_bodies(gallery_id, in_path, out_path, gallery_type=None, workers=3, delay=0.5):
    """in_path(JSONL) 의 글마다 본문을 채워 out_path 에 추가 기록. 중단 후 재실행하면 이어서 받는다."""
    import os
    import threading
    from concurrent.futures import ThreadPoolExecutor

    done: set[int] = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            done = {json.loads(line)["no"] for line in f if line.strip()}
    with open(in_path, encoding="utf-8") as f:
        todo = [json.loads(line) for line in f if line.strip()]
    todo = [p for p in todo if p["no"] not in done]
    print(f"본문 수집 대상 {len(todo)}건 (완료 {len(done)}건)", flush=True)

    local = threading.local()
    lock = threading.Lock()
    count = [0]

    def work(p):
        if not hasattr(local, "client"):
            local.client = DCClient(gallery_id, gallery_type or "mgallery", delay)
        try:
            p["body"] = local.client.fetch_body(p["no"])
        except RuntimeError as e:
            p["body"] = ""
            p["error"] = str(e)
        with lock:
            out.write(json.dumps(p, ensure_ascii=False) + "\n")
            count[0] += 1
            if count[0] % 200 == 0:
                out.flush()
                print(f"본문 {count[0]}/{len(todo)}", flush=True)

    with open(out_path, "a", encoding="utf-8") as out, ThreadPoolExecutor(workers) as ex:
        list(ex.map(work, todo))
    print(f"본문 수집 완료 {count[0]}건", flush=True)


def refill_empty(gallery_id, path, gallery_type=None, workers=2, delay=1.0):
    """본문이 빈 글만 다시 받아 path 를 갱신한다."""
    from concurrent.futures import ThreadPoolExecutor
    import threading

    with open(path, encoding="utf-8") as f:
        posts = [json.loads(line) for line in f if line.strip()]
    todo = [p for p in posts if not p.get("body")]
    print(f"빈 본문 재수집 대상 {len(todo)}건", flush=True)
    local = threading.local()
    count = [0]
    lock = threading.Lock()

    def work(p):
        if not hasattr(local, "client"):
            local.client = DCClient(gallery_id, gallery_type or "mgallery", delay)
        try:
            p["body"] = local.client.fetch_body(p["no"])
        except RuntimeError:
            pass
        with lock:
            count[0] += 1
            if count[0] % 200 == 0:
                print(f"재수집 {count[0]}/{len(todo)}", flush=True)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(work, todo))
    with open(path, "w", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"재수집 완료, 남은 빈 본문 {sum(1 for p in posts if not p.get('body'))}건", flush=True)
