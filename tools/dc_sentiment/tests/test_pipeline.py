import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime
from crawler import parse_list, parse_body
from sentiment import analyze, MENTION_RE
from run import build_report, quarter_of

LIST_HTML = """
<table><tbody>
<tr class="ub-content us-post" data-no="100"><td class="gall_num">공지</td>
 <td class="gall_tit"><a>공지사항</a></td><td class="gall_date" title="2025-01-01 00:00:00">25.01.01</td>
 <td class="gall_count">1</td><td class="gall_recommend">0</td></tr>
<tr class="ub-content us-post" data-no="2001"><td class="gall_num">2001</td>
 <td class="gall_tit"><a>그세 스노우플레이크 영입</a></td><td class="gall_date" title="2025-02-03 12:00:00">02.03</td>
 <td class="gall_count">1,234</td><td class="gall_recommend">15</td></tr>
</tbody></table>
<div class="bottom_paging_box"><em>1</em><a href="#">2</a><a class="search_next" href="/mgallery/board/lists/?id=automata&search_pos=-120000&s_keyword=x">다음검색</a></div>
"""

def test_parse_list():
    posts, pos, more = parse_list(LIST_HTML)
    assert [p.no for p in posts] == [2001]
    assert posts[0].views == 1234 and posts[0].recommend == 15
    assert pos == -120000 and more

def test_parse_body():
    assert parse_body('<div class="write_div"><p>본문</p></div>') == "본문"

def test_mention_filter():
    assert MENTION_RE.search("그세 샀다")
    assert MENTION_RE.search("그랜드 세이코 SBGA211")
    assert not MENTION_RE.search("그세끼 뭐냐")
    assert not MENTION_RE.search("그세상 참")

def test_sentiment():
    assert analyze("그세 다이얼 진짜 영롱하다", "")["label"] == "positive"
    assert analyze("그세 감가 너무 심하고 비싸", "")["label"] == "negative"
    assert analyze("그세 별로 안 비싸던데 예쁘다", "")["label"] == "positive"
    # 무관한 문장(브랜드 언급 없는 먼 문장)은 제외
    body = "그세 샀다.\n날씨 좋다.\n점심 맛있다.\n롤렉스는 최악이다."
    assert analyze("구매기", body)["neg_terms"] == []

def test_report_quarters():
    posts = [
        {"no": 1, "title": "그세 예쁘다", "date": "2024-10-05 10:00:00", "views": 10, "recommend": 1, "body": ""},
        {"no": 2, "title": "그세 거품 비싸", "date": "2026-08-01 10:00:00", "views": 20, "recommend": 0, "body": ""},
        {"no": 3, "title": "그세끼", "date": "2025-05-01 10:00:00", "views": 5, "recommend": 0, "body": ""},
    ]
    s, rows = build_report(posts, datetime(2024, 10, 1), datetime(2026, 9, 30, 23, 59, 59))
    assert [x["quarter"] for x in s][0] == "2024Q4" and len(s) == 8
    d = {x["quarter"]: x for x in s}
    assert d["2024Q4"]["positive"] == 1 and d["2026Q3"]["negative"] == 1
    assert d["2025Q2"]["posts"] == 0
    assert quarter_of("2025-12-31 23:00:00") == "2025Q4"

def test_title_mention_uses_whole_body():
    assert analyze("그세 영입했습니다", "다이얼 진짜 영롱하다. 만족")["label"] == "positive"
