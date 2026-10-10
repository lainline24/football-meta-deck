"""EDA 결과를 덱용 data.json으로 내보내기 (eda_league.py의 분석 함수 재사용)"""
import json
import os
import sys
from datetime import datetime

DECK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(DECK))
import eda_league as eda  # noqa: E402


def main():
    df = eda.load()
    dom = df[~df["리그"].isin(eda.EURO)].copy()
    meta = eda.league_meta(dom)
    mom = eda.momentum(dom)
    eu_tbl, eu = eda.europe_by_league(df, dom)
    corr = dom[["ppg", "gf", "ga"]].corr()

    data = {
        "collected": datetime.fromtimestamp(os.path.getmtime(eda.SRC)).strftime("%Y-%m-%d"),
        "counts": {"domestic": len(dom), "europe": len(eu), "leagues": int(dom["리그"].nunique())},
        "meta": [{"league": k, "teams": int(r["팀 수"]), "games": round(float(r["평균 경기"]), 1),
                  "gpg": round(float(r["경기당 골"]), 3), "draw": round(float(r["무승부율"]), 3),
                  "spread": round(float(r["승점/경기 편차"]), 3), "unbeaten": int(r["무패 팀"]), "leader": r["선두"]}
                 for k, r in meta.iterrows()],
        "europe": [{"league": k, "w": int(r["승"]), "d": int(r["무"]), "l": int(r["패"]),
                    "gf": int(r["득점"]), "ga": int(r["실점"]), "n": int(r["팀 수"])} for k, r in eu_tbl.iterrows()],
        "momentum": [{"league": r["리그"], "team": r["구단"], "rank": int(r["순위"]), "ppg": round(r["ppg"], 2),
                      "form": round(r["form_ppg"], 2), "mom": round(r["mom"], 2), "recent": r["최근 5경기"]}
                     for _, r in mom.iterrows()],
        "bigs": [{"league": b["리그"], "a": b["홈"], "b": b["상대"], "gap": b["승점차"]} for b in eda.big_matches(dom)],
        "corr": {"gf": round(float(corr.loc["ppg", "gf"]), 2), "ga": round(float(corr.loc["ppg", "ga"]), 2)},
        "teams": dom[["리그", "구단", "순위", "그룹", "경기", "승점", "gf", "ga", "ppg"]]
                 .rename(columns={"리그": "league", "구단": "team", "순위": "rank", "그룹": "group", "경기": "games", "승점": "pts"})
                 .round(3).to_dict("records"),
    }
    out = os.path.join(DECK, "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("data.json 저장:", out, "| 국내", len(dom), "팀 / 유럽", len(eu), "팀")


if __name__ == "__main__":
    main()
