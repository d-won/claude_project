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
            if oldest_in_block and datetime.strptime(oldest_in_block, "%Y-%m-%d %H:%M:%S") < since:
                return
            if next_pos is None:
                return
            search_pos = next_pos

    def fetch_body(self, no: int) -> str:
        html = self._get(BASE + self._prefix() + "/view/", id=self.gallery_id, no=no)
        return parse_body(html)


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

    has_next_page = False
    paging = soup.select_one("div.bottom_paging_box")
    if paging:
        current = paging.select_one("em")
        cur = _int(current.get_text()) if current else 1
        pages = [_int(a.get_text()) for a in paging.select("a") if a.get_text(strip=True).isdigit()]
        has_next_page = any(p > cur for p in pages)
    return posts, next_pos, has_next_page


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
