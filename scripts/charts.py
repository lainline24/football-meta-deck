"""matplotlib 정적 차트 → assets/charts/*.png (index.html 테마 v2와 같은 색·배경)"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

DECK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DECK, "assets", "charts")
D = json.load(open(os.path.join(DECK, "data.json"), encoding="utf-8"))

# 테마 v2 (index.html :root 와 동일) — 강조색은 dataviz validator 다크 모드 통과 값
INK, INK2, MUTED, GRID = "#ffffff", "#cbd5e1", "#8b97ab", "#1d2940"
BLUE, RED, MINT, AMBER, DIM = "#4090ff", "#f05252", "#0fae7e", "#ffc94d", "#3a4558"
CARD = "#121b2b"

for f in ("malgun.ttf", "malgunbd.ttf"):
    p = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", f)
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams.update({
    "font.family": "Malgun Gothic", "axes.unicode_minus": False, "font.size": 19,
    "text.color": INK2, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 17, "ytick.labelsize": 17, "axes.labelsize": 19,
    "axes.edgecolor": GRID, "axes.facecolor": CARD, "figure.facecolor": CARD, "savefig.facecolor": CARD,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 1, "axes.spines.top": False, "axes.spines.right": False,
})


def callout(ax, x, y, text, dx=20, dy=20, color=AMBER, ha="left"):
    """강조 대상에 붙이는 주석 박스"""
    ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=18, fontweight="bold", color="#0b1220",
                ha=ha, zorder=6, bbox=dict(boxstyle="round,pad=0.35", facecolor=color, edgecolor="none"),
                arrowprops=dict(arrowstyle="-", color=color, lw=2))


def attack_defense():
    T = D["teams"]
    fig, ax = plt.subplots(figsize=(12, 6.9), dpi=140)
    gf = np.array([t["gf"] for t in T]); ga = np.array([t["ga"] for t in T])
    ax.axvline(np.median(gf), color="#2c3a55", lw=1.5, zorder=1)
    ax.axhline(np.median(ga), color="#2c3a55", lw=1.5, zorder=1)
    others = [t for t in T if t["rank"] != 1]
    ax.scatter([t["gf"] for t in others], [t["ga"] for t in others], s=50, color=DIM, edgecolor=CARD, lw=1.2, zorder=2,
               label="그 외 구단")
    leads = [t for t in T if t["rank"] == 1]
    ax.scatter([t["gf"] for t in leads], [t["ga"] for t in leads], s=170, color=BLUE, edgecolor=CARD, lw=2.5, zorder=3,
               label="리그 선두")
    from adjustText import adjust_text
    labels = [ax.text(t["gf"] + (-0.08 if t["gf"] > 4 else 0.06), t["ga"] - 0.14,
                      t["team"] + (f' ({t["group"][:2]})' if t["group"] else ""), color=INK, fontsize=18,
                      fontweight="bold", zorder=4, ha="right" if t["gf"] > 4 else "left") for t in leads]
    ax.invert_yaxis()
    ax.set_xlabel("경기당 득점 →", loc="right")
    ax.set_ylabel("← 경기당 실점 (위로 갈수록 적게 먹음)", loc="top")
    xmax, ymax = gf.max() + .3, ga.max() + .3
    ax.set_xlim(0, xmax); ax.set_ylim(ymax, 0)
    adjust_text(labels, ax=ax, x=list(gf), y=list(ga), expand=(1.25, 1.6), force_text=(0.6, 0.9),
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
    for txt, x, y, ha, va in [("화력 + 철벽", xmax - .05, .08, "right", "top"), ("철벽형", .05, .08, "left", "top"),
                              ("화력형", xmax - .05, ymax - .1, "right", "bottom"), ("고전", .05, ymax - .1, "left", "bottom")]:
        ax.text(x, y, txt, ha=ha, va=va, color=MUTED, fontsize=17)
    leg = ax.legend(loc="upper center", bbox_to_anchor=(.5, 1.09), ncol=2, frameon=False, fontsize=17)
    for t in leg.get_texts():
        t.set_color(INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "attack_defense.png"))
    plt.close(fig)


def league_dna():
    """리그 × 지표 히트맵: 각 지표를 리그 간 0~1로 정규화, 셀에는 원래 값"""
    M = D["meta"]
    cols = [("gpg", "경기당 골", "{:.2f}"), ("draw", "무승부율", "{:.0%}"), ("spread", "격차\n(승점/경기 편차)", "{:.2f}"),
            ("unbeaten", "무패 팀", "{:d}"), ("games", "평균 경기 수", "{:.0f}")]
    leagues = [m["league"] for m in M]
    raw = np.array([[m[c] for c, _, _ in cols] for m in M], dtype=float)
    norm = (raw - raw.min(0)) / np.where(np.ptp(raw, 0) == 0, 1, np.ptp(raw, 0))
    cmap = LinearSegmentedColormap.from_list("blue", ["#17223a", "#1c4f9c", "#4090ff", "#b9d7ff"])
    fig, ax = plt.subplots(figsize=(14, 6.6), dpi=120)
    ax.imshow(norm, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    ax.grid(False)
    ax.set_xticks(range(len(cols)), [c[1] for c in cols], fontsize=18, color=INK2)
    ax.set_yticks(range(len(leagues)), leagues, fontsize=19, color=INK)
    ax.tick_params(length=0); ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(len(leagues)):
        for j, (_, _, fmt) in enumerate(cols):
            v = raw[i, j]
            txt = fmt.format(int(v)) if fmt == "{:d}" else fmt.format(v)
            ax.text(j, i, txt, ha="center", va="center", fontsize=20, fontweight="bold",
                    color="#0b1220" if norm[i, j] > .7 else INK)
    for x in np.arange(-.5, len(cols), 1):
        ax.axvline(x, color=CARD, lw=5)
    for y in np.arange(-.5, len(leagues), 1):
        ax.axhline(y, color=CARD, lw=5)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "league_dna.png"))
    plt.close(fig)


def style_map():
    """전술 유형 small multiples: 유형마다 패널 하나, 해당 유형만 블루로 강조 (4색 범주 팔레트는 색약 검증 불가 → 분할)"""
    T, S = D["tactics"]["teams"], D["tactics"]["styles"]
    x = np.array([t["poss"] for t in T]); y = np.array([t["shots"] - t["shots_ag"] for t in T])
    fig, axes = plt.subplots(2, 2, figsize=(14, 7.4), dpi=120, sharex=True, sharey=True)
    pending = []
    for ax, s in zip(axes.flat, S):
        on = np.array([t["style"] == s["name"] for t in T])
        ax.axvline(50, color="#2c3a55", lw=1.5); ax.axhline(0, color="#2c3a55", lw=1.5)
        ax.scatter(x[~on], y[~on], s=26, color=DIM, edgecolor="none", zorder=2)
        ax.scatter(x[on], y[on], s=70, color=BLUE, edgecolor=CARD, lw=1.5, zorder=3)
        from adjustText import adjust_text
        labs = [ax.text(t["poss"], t["shots"] - t["shots_ag"], t["team"], fontsize=15, fontweight="bold", color=INK, zorder=4)
                for t in T if t["style"] == s["name"] and t["rank"] == 1]
        pending.append((ax, labs, on))
        ax.set_title(f'{s["name"]}  ·  {s["n"]}팀  ·  경기당 승점 {s["ppg"]:.2f}', loc="left", fontsize=19, color=INK,
                     fontweight="bold", pad=10)
    axes[0, 0].set_ylim(y.min() - 2, y.max() + 6)  # 위쪽 라벨 공간 (sharey라 전 패널 적용)
    for ax in axes[1]:
        ax.set_xlabel("점유율 (%) →")
    for ax in axes[:, 0]:
        ax.set_ylabel("슈팅 마진 ↑")
    fig.tight_layout(h_pad=1.6)
    for ax, labs, on in pending:
        if labs:
            adjust_text(labs, ax=ax, x=list(x[on]), y=list(y[on]), expand=(1.4, 2.0), force_text=(0.8, 1.2),
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
    fig.savefig(os.path.join(OUT, "style_map.png"))
    plt.close(fig)


def leader_radar():
    """리그 선두들의 리그 내 백분위 레이더 (3×3)"""
    L = D["tactics"]["leaders"]
    labels = list(L[0]["pct"].keys())
    ang = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    # 5 + 4 두 줄 가로형: 축 위치를 직접 계산 (라벨이 옆 레이더와 겹치거나 잘리지 않도록)
    FW, FH, w = 20, 9.6, 0.125
    h = w * FW / FH
    fig = plt.figure(figsize=(FW, FH), dpi=100)
    axes = [fig.add_axes([cx - w / 2, 0.555, w, h], polar=True) for cx in (0.1, 0.3, 0.5, 0.7, 0.9)] +            [fig.add_axes([cx - w / 2, 0.075, w, h], polar=True) for cx in (0.2, 0.4, 0.6, 0.8)]
    for ax, t in zip(axes, L):
        v = [t["pct"][k] for k in labels]
        ax.set_facecolor(CARD)
        ax.plot(ang + ang[:1], [50] * (len(ang) + 1), color="#2c3a55", lw=1.5)    # 리그 중간값(50백분위)
        ax.fill(ang + ang[:1], v + v[:1], color=BLUE, alpha=.35, zorder=2)
        ax.plot(ang + ang[:1], v + v[:1], color=BLUE, lw=2.5, zorder=3)
        best = int(np.argmax(v))
        ax.scatter([ang[best]], [v[best]], s=90, color=AMBER, zorder=4)
        ax.set_ylim(0, 100); ax.set_yticks([25, 50, 75]); ax.set_yticklabels([])
        ax.set_xticks(ang); ax.set_xticklabels(labels, fontsize=14, color=INK2); ax.tick_params(axis="x", pad=10)
        ax.grid(color=GRID, lw=1); ax.spines["polar"].set_color(GRID)
        name = t["team"] + (f' ({t["group"][:2]})' if t["group"] else "")
        ax.set_title(f'{name}\n{t["league"]} · {t["style"]}', fontsize=16, color=INK, fontweight="bold", pad=18)
    fig.savefig(os.path.join(OUT, "leader_radar.png"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for old in ("correlation.png",):  # v2에서 뺀 차트
        p = os.path.join(OUT, old)
        if os.path.exists(p):
            os.remove(p)
    attack_defense(); league_dna(); style_map(); leader_radar()
    print("차트 저장:", sorted(os.listdir(OUT)))
