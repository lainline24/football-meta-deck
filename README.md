# 2026-27 해외축구 메타 리포트 (HTML 슬라이드)

네이버 스포츠 순위·팀 기록을 Firecrawl로 수집해 분석한 10개 대회 메타·전술 슬라이드 덱입니다 (18장).

- 조작: `←` `→` / 스페이스 / 클릭 / 스와이프, `F` 전체화면, URL `#번호`로 특정 슬라이드 열기
- 시각화: **anime.js**(진입 애니메이션·인터랙티브 SVG 차트), **manim**(데이터 모션 영상), **matplotlib**(정적 차트)
- 이미지: Google Flow (Nano Banana 2.1)로 생성

## 다시 만들기
```bash
python ../crawl_league_rank.py          # 최신 순위 수집 → 해외축구_리그별_순위.xlsx
python ../crawl_team_records.py         # 팀 기록(xG·슈팅·점유율 등 9개 지표) → 해외축구_팀기록.xlsx
python scripts/build_data.py            # EDA + 전술 분석(scripts/tactics.py, K-means) → data.json
python scripts/charts.py                # matplotlib → assets/charts/
manim -qh --format mp4 scripts/scenes.py GoalsRace EPLParadox PossessionPoints   # Python 3.12 + manim → assets/video/
node scripts/verify.mjs http://localhost:8765/ shots            # 검증 루프 (puppeteer-core + Chrome)
```

## 검증 루프가 확인하는 것
모든 슬라이드를 애니메이션·영상 종료 후 캡처하고, 캔버스 밖 넘침 · 잘린 블록 · 텍스트 겹침 · 이미지/영상 로드 · 콘솔 에러 · 404를 자동 검사합니다.

## 전술 분석 방법
점유율·패스 정확도·경기당 슈팅·허용 슈팅·슈팅 품질(xG÷슈팅)을 표준화해 K-means(k=4)로 168개 구단을 군집화하고,
군집 중심값으로 유형 이름을 붙였습니다. 포메이션·압박 같은 직접 전술 데이터가 아니라 경기 기록에서 추론한 성향입니다.
