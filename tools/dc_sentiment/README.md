# 디시 갤러리 브랜드 언급량 · 긍부정 분기 분석

디시인사이드 갤러리(기본: 오토마타 갤러리 `automata`)에서 그랜드세이코(그세) 언급 글을 수집해
분기(Q1~Q4)별 언급량과 긍·부정 평가를 집계합니다.

## 실행

```bash
pip install -r requirements.txt

# 1) 목록 수집 (제목·날짜·조회수) — 빠름
python run.py crawl --gallery automata --since 2024-09-26 --no-body --out data/titles.jsonl
# 2) 본문 수집 (재실행하면 이어받음) + 차단으로 비어버린 본문 재수집
python run.py bodies --in data/titles.jsonl --out data/posts.jsonl --workers 4
python run.py bodies --refill --out data/posts.jsonl --workers 2 --delay 1.0
# 3) 분기별 층화 표본 추출 → 읽고 labels.tsv 작성 (형식은 sample.py 참고)
python sample.py --per-quarter 60 --out data/sample.txt
# 4) 리포트 (언급량 전수 + 사전 기반 감성 + 표본 라벨 감성)
python run.py report --in data/posts.jsonl --since 2024-10-01 --until 2026-09-30 \
    --labels results/labels_all.tsv --out results
```

Reddit 수집: `python reddit.py collect --only GrandSeikos --out data/reddit_gs.jsonl`, `python reddit.py windows --sub Watches` (대형 서브는 월 단위 병렬 전수).

2026-09-26 실행 결과 요약은 [`results/SUMMARY.md`](results/SUMMARY.md), Reddit 비교는 [`results/REDDIT_SUMMARY.md`](results/REDDIT_SUMMARY.md)에 있습니다.

갤러리 종류(일반/마이너/미니)는 자동 감지합니다. 강제하려면 `--gallery-type mgallery` 등을 지정하세요.

## 결과물 (`report/`)

| 파일 | 내용 |
|---|---|
| `report.md` | 분기별 언급량, 긍정/중립/부정 건수·비율, 순감성지수, 주요 긍·부정 표현, 대표 글 링크 |
| `quarterly_summary.csv` | 분기별 집계 (엑셀에서 바로 열림, UTF-8 BOM) |
| `posts_scored.csv` | 글 단위 점수·라벨·매칭 표현 (수작업 검수용) |

## 방법

- **검색어**: `그세`, `그랜드세이코`, `그랜드 세이코`, `grand seiko` → 글 번호로 중복 제거
- **오탐 제거**: `그세끼`, `그세상`, `그세계` 등 브랜드가 아닌 `그세`는 정규식으로 제외
- **감성 대상**: 제목에 브랜드가 있으면 글 전체, 아니면 제목 + 본문 중 브랜드 언급 문장 ±1문장
- **점수**: 시계 커뮤니티 말투에 맞춘 사전(`sentiment.py`)으로 긍정−부정 가중합.
  `안/못 ~`, `~지 않` 같은 부정 표현은 극성을 뒤집음. 점수 ≥ +2 긍정, ≤ −2 부정, 그 사이 중립
- **순감성지수** = (긍정 − 부정) / (긍정 + 부정) × 100 (−100 ~ +100)

## 한계

- 사전 기반이라 비꼼·반어("그세 참 싸다ㅋㅋ")는 잡지 못합니다. `posts_scored.csv`로 표본 검수를 권장합니다.
- 댓글은 수집하지 않습니다(게시글 제목+본문만).
- 삭제된 글은 집계되지 않습니다.
