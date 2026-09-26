"""시계 커뮤니티(디시) 말투에 맞춘 사전 기반 한국어 감성 분석.

그랜드세이코가 언급된 문장과 그 앞뒤 문장만 대상으로 점수를 매겨,
글 전체 분위기가 아니라 '그세에 대한' 평가를 최대한 뽑아낸다.
"""
from __future__ import annotations

import re
from collections import Counter

# 브랜드 언급 패턴. '그세' 는 그세끼/그세상/그세계 등 오탐을 제외한다.
MENTION_RE = re.compile(
    r"그랜드\s*세이코|grand\s*seiko|그세(?!끼|상|계|대|팅|트|력|월|기|균|탁|션|종|련|금|무|번|개|명|포|컨|미|제|요일)",
    re.IGNORECASE,
)

POSITIVE = {
    # 외관/마감
    "예쁘": 2, "이쁘": 2, "이뻐": 2, "예뻐": 2, "예쁜": 2, "이쁜": 2, "예쁨": 2, "이쁨": 2, "이뽀": 2, "멋있": 2, "멋지": 2, "멋져": 2, "마음에 들": 2, "맘에 들": 2, "빠져": 1, "매력": 1, "말안되": 1, "ㅎㄷㄷ": 1, "영롱": 2, "아름답": 2, "미쳤": 1, "미친 다이얼": 2,
    "마감 좋": 2, "마감이 좋": 2, "마감 미쳤": 2, "마감 지리": 2, "자라츠": 1, "폴리싱": 1,
    "다이얼 좋": 2, "다이얼 예": 2, "스노우플레이크": 1, "시라카바": 1, "백화": 1,
    "고급": 1, "우아": 2, "세련": 2, "감성": 1, "간지": 2, "존예": 2, "갓": 1, "지린다": 2, "지리네": 2,
    # 가치/평가
    "최고": 2, "좋": 1, "만족": 2, "추천": 2, "강추": 2, "사랑": 2, "감동": 2, "인정": 1, "명품": 1,
    "가성비": 1, "가심비": 2, "혜자": 2, "끝판": 2, "엔드게임": 1, "정확": 1, "스드": 0,
    "스프링드라이브 좋": 2, "무브 좋": 2, "정교": 2, "장인": 1, "완벽": 2, "훌륭": 2, "레전드": 2,
    "꿀": 1, "찐": 1, "구매 완료": 1, "득템": 2, "입양": 1, "영입": 1, "기변 성공": 2, "행복": 2,
}

NEGATIVE = {
    # 가격/감가
    "비싸": 2, "비쌈": 2, "거품": 2, "감가": 2, "똥값": 3, "헐값": 2, "가격 인상": 1, "가격인상": 1,
    "리셀 안": 2, "중고가 낮": 2, "제값 못": 2, "돈값 못": 3,
    # 브랜드/이미지
    "아재": 1, "할배": 2, "할아버지 시계": 2, "틀딱": 2, "인지도": 1, "아무도 모름": 2, "아무도 몰라": 2,
    "브랜드력": 1, "브랜드 파워": 1, "세이코 주제": 3, "세이코 따리": 3, "세이코가 무슨": 2,
    "일본 시계": 1, "짭": 1,
    # 착용감/품질
    "두꺼": 2, "두껍": 2, "무겁": 1, "무거": 1, "러그 길": 1, "기스": 1, "스크래치": 1, "흠집": 1,
    "잔고장": 2, "고장": 2, "오차": 1, "as 별로": 2, "A/S": 0, "서비스 별로": 2,
    # 일반 부정
    "별로": 2, "별로더라": 1, "생각보다 덜": 1, "슬프": 1, "무리": 0, "일뽕": 1, "비추": 2, "실망": 2, "후회": 2, "구리": 2, "구림": 2, "촌스": 2, "애매": 1, "아쉽": 1, "아쉬": 1, "노잼": 2,
    "싫": 2, "최악": 3, "쓰레기": 3, "병신": 2, "븅신": 2, "허접": 2, "에바": 1, "오바": 1, "호구": 2,
    "매물 쌓": 1, "처분": 1, "방출": 1, "판매합니다": 0,
}

# 앞(최대 6자) 또는 바로 뒤에 붙으면 극성을 뒤집는 표현
NEG_PREFIX = re.compile(r"(안|못|전혀|별로\s*안)\s*$")
NEG_SUFFIX = re.compile(r"^[가-힣]{0,2}\s*(지는?\s*않|진\s*않|지도\s*않|지\s*못|진\s*못)")

SENT_SPLIT = re.compile(r"(?<=[.!?…~\n])\s+|[\n]+|(?<=[다요ㅋㅎ])\s+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT_SPLIT.split(text or "") if s and s.strip()]


def target_text(title: str, body: str, window: int = 1) -> str:
    """제목에 브랜드가 있으면 글 전체, 아니면 제목 + 본문 중 브랜드 언급 문장 ±window 문장."""
    sents = split_sentences(body)
    if MENTION_RE.search(title):
        return "\n".join([title] + sents)
    keep: set[int] = set()
    for i, s in enumerate(sents):
        if MENTION_RE.search(s):
            keep.update(range(max(0, i - window), min(len(sents), i + window + 1)))
    parts = [title] + [sents[i] for i in sorted(keep)]
    return "\n".join(parts)


def _score_lexicon(text: str, lexicon: dict[str, int], hits: Counter) -> int:
    total = 0
    low = text.lower()
    for term, w in lexicon.items():
        if w == 0:
            continue
        for m in re.finditer(re.escape(term.lower()), low):
            before = low[max(0, m.start() - 6): m.start()]
            after = low[m.end(): m.end() + 8]
            sign = -1 if (NEG_PREFIX.search(before) or NEG_SUFFIX.search(after)) else 1
            total += sign * w
            hits[("+" if sign > 0 else "-") + term] += 1
    return total


def analyze(title: str, body: str) -> dict:
    text = target_text(title, body)
    pos_hits: Counter = Counter()
    neg_hits: Counter = Counter()
    pos = _score_lexicon(text, POSITIVE, pos_hits)
    neg = _score_lexicon(text, NEGATIVE, neg_hits)
    # 부정된 긍정어는 부정 점수로, 부정된 부정어는 긍정 점수로 넘긴다
    score = pos - neg
    if score >= 2:
        label = "positive"
    elif score <= -2:
        label = "negative"
    else:
        label = "neutral"
    return {
        "score": score,
        "label": label,
        "pos_terms": [t[1:] for t, c in pos_hits.items() if t[0] == "+" for _ in range(c)],
        "neg_terms": [t[1:] for t, c in neg_hits.items() if t[0] == "+" for _ in range(c)],
        "mentions": len(MENTION_RE.findall(title + "\n" + (body or ""))),
    }
