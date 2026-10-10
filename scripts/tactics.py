"""팀 기록(xG·슈팅·점유율 등) + 순위표로 전술 성향 분석 → build_data.py가 data.json의 "tactics"로 넣는다

전술 데이터(포메이션·압박 등)가 아니라 경기 기록에서 '추론한' 성향이다.
"""
import os

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "해외축구_팀기록.xlsx")
FEATURES = ["poss", "pass", "shots", "shots_ag", "xg_per_shot"]
FEATURE_KO = {"poss": "점유율", "pass": "패스 정확도", "shots": "경기당 슈팅", "shots_ag": "허용 슈팅", "xg_per_shot": "슈팅 품질"}


def load_records() -> pd.DataFrame:
    xl = pd.ExcelFile(SRC)
    frames = []
    for sheet in xl.sheet_names:
        d = pd.read_excel(xl, sheet, header=4).dropna(subset=["구단"])
        d["리그"] = sheet
        frames.append(d)
    r = pd.concat(frames, ignore_index=True)
    return r.rename(columns={"구단": "team", "리그": "league", "점유율": "poss", "패스 정확도": "pass", "경기당 슈팅": "shots",
                             "경기당 유효슈팅": "sot", "경기당 슈팅 허용": "shots_ag", "클린시트": "cs"})


def build(dom: pd.DataFrame) -> dict:
    """dom: eda_league.load()의 국내 리그 순위 데이터"""
    rec = load_records()
    st = dom.rename(columns={"리그": "league", "구단": "team", "순위": "rank", "그룹": "group", "경기": "games", "득점": "goals",
                             "실점": "conceded"})[["league", "team", "rank", "group", "games", "goals", "conceded", "ppg"]]
    df = rec.merge(st, on=["league", "team"], how="inner")
    unmatched = sorted(set(rec["team"]) - set(df["team"]))
    df["xg_pg"] = df["xG"] / df["games"]
    df["xga_pg"] = df["xGA"] / df["games"]
    df["xg_per_shot"] = df["xg_pg"] / df["shots"].replace(0, np.nan)
    df["finish_pg"] = (df["goals"] - df["xG"]) / df["games"]        # +: 기대보다 더 넣음
    df["defeff_pg"] = (df["xGA"] - df["conceded"]) / df["games"]    # +: 기대보다 덜 먹음
    df["shot_margin"] = df["shots"] - df["shots_ag"]
    df = df.dropna(subset=FEATURES)

    # --- 전술 유형: 표준화 후 K-means 4개 군집 ---
    X = StandardScaler().fit_transform(df[FEATURES])
    km = KMeans(n_clusters=4, n_init=50, random_state=0).fit(X)
    df["cluster"] = km.labels_
    z = pd.DataFrame(km.cluster_centers_, columns=FEATURES)
    names = name_clusters(z)
    df["style"] = df["cluster"].map(names)

    styles = []
    for c, name in names.items():
        g = df[df["cluster"] == c]
        leaders = g[g["rank"] == 1]["team"].tolist()
        examples = g.sort_values("ppg", ascending=False)["team"].head(4).tolist()
        styles.append({
            "name": name, "n": int(len(g)), "ppg": round(float(g["ppg"].mean()), 2),
            "poss": round(float(g["poss"].mean()), 1), "pass": round(float(g["pass"].mean()), 1),
            "shots": round(float(g["shots"].mean()), 1), "shots_ag": round(float(g["shots_ag"].mean()), 1),
            "xg_per_shot": round(float(g["xg_per_shot"].mean()), 3), "leaders": leaders, "examples": examples,
            "z": {f: round(float(z.loc[c, f]), 2) for f in FEATURES},
        })
    styles.sort(key=lambda s: -s["ppg"])

    # --- 리그 전술 지문 ---
    fp = df.groupby("league").agg(poss_sd=("poss", "std"), pass_=("pass", "mean"), shots=("shots", "mean"),
                                  xg_per_shot=("xg_per_shot", "mean"), finish=("finish_pg", "mean")).reset_index()
    fingerprint = [{"league": r.league, "poss_sd": round(r.poss_sd, 1), "pass": round(r.pass_, 1), "shots": round(r.shots, 1),
                    "xg_per_shot": round(r.xg_per_shot, 3), "finish": round(r.finish, 2)} for r in fp.itertuples()]
    style_mix = (df.groupby(["league", "style"]).size().unstack(fill_value=0)
                 .reindex(columns=[s["name"] for s in styles], fill_value=0))

    # --- 점유율과 승점 ---
    r_all = float(df[["poss", "ppg"]].corr().iloc[0, 1])
    r_by = {lg: round(float(g[["poss", "ppg"]].corr().iloc[0, 1]), 2) for lg, g in df.groupby("league")}
    r_shotm = float(df[["shot_margin", "ppg"]].corr().iloc[0, 1])
    r_xgd = float(pd.concat([df["xg_pg"] - df["xga_pg"], df["ppg"]], axis=1).corr().iloc[0, 1])

    # --- 선두들의 리그 내 백분위 (레이더) ---
    radar_metrics = [("poss", "점유율", 1), ("pass", "패스", 1), ("shots", "슈팅", 1), ("sot", "유효슈팅", 1),
                     ("xg_pg", "xG", 1), ("xg_per_shot", "슈팅 품질", 1), ("shots_ag", "슈팅 억제", -1), ("xga_pg", "xGA 억제", -1)]
    leaders = []
    for (lg, grp), g in df[df["rank"] == 1].groupby(["league", "group"]):
        for _, t in g.iterrows():
            pool = df[(df["league"] == lg) & (df["group"] == grp)] if grp else df[df["league"] == lg]
            pct = {}
            for col, label, sign in radar_metrics:
                v = pool[col] * sign
                pct[label] = round(float((v < t[col] * sign).mean() * 100 + (v == t[col] * sign).mean() * 50), 0)
            leaders.append({"league": lg, "group": grp, "team": t["team"], "style": t["style"], "pct": pct,
                            "poss": t["poss"], "shots": t["shots"], "xg_pg": round(t["xg_pg"], 2)})

    fin = df.sort_values("finish_pg")
    pick = pd.concat([fin.head(6), fin.tail(6)])
    finishing = [{"league": r.league, "team": r.team, "rank": int(r.rank), "finish": round(r.finish_pg, 2),
                  "goals": int(r.goals), "xg": round(r.xG, 1), "games": int(r.games)} for r in pick.itertuples()]

    teams = df[["league", "team", "rank", "group", "ppg", "poss", "pass", "shots", "shots_ag", "xg_per_shot", "style",
                "xg_pg", "xga_pg"]].round(3).to_dict("records")
    return {
        "n": int(len(df)), "unmatched": unmatched, "features": FEATURE_KO, "styles": styles,
        "fingerprint": fingerprint, "style_mix": {lg: row.to_dict() for lg, row in style_mix.iterrows()},
        "corr": {"poss": round(r_all, 2), "poss_by_league": r_by, "shot_margin": round(r_shotm, 2), "xgd": round(r_xgd, 2)},
        "leaders": leaders, "finishing": finishing, "teams": teams,
    }


def name_clusters(z: pd.DataFrame) -> dict:
    """군집 중심(z점수)으로 이름 붙이기 — 가장 두드러진 특징 순서로 하나씩 배정"""
    names, left = {}, set(z.index)
    def take(score, name):
        c = max(left, key=lambda i: score(z.loc[i]))
        names[c] = name; left.discard(c)
    take(lambda r: r["poss"] + r["pass"] + r["shots"] - r["shots_ag"], "점유 지배형")  # 쥐고, 많이 쏘고, 덜 허용
    take(lambda r: -r["poss"] - r["pass"] + r["xg_per_shot"], "역습형")            # 공을 내주고 적은 패스로 좋은 기회
    take(lambda r: -r["xg_per_shot"], "원거리 슈팅형")                             # 슈팅 1회당 기대값이 낮음 = 먼 거리
    for c in left:
        names[c] = "효율 빌드업형"                                                 # 나머지: 평균 이상 소유 + 높은 슈팅 품질
    return names
