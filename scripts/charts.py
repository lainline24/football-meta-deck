"""matplotlib 정적 차트 → assets/charts/*.png (덱의 카드 배경색과 동일한 다크 테마)"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402

DECK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DECK, "assets", "charts")
D = json.load(open(os.path.join(DECK, "data.json"), encoding="utf-8"))

INK, INK2, MUTED, GRID = "#ffffff", "#c3c2b7", "#898781", "#2c2c2a"
BLUE, RED, DIM = "#3987e5", "#e66767", "#5d5c57"
CARD = "#151a21"  # index.html의 --card 와 같은 값

for f in ("malgun.ttf", "malgunbd.ttf"):
    p = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", f)
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams.update({
    "font.family": "Malgun Gothic", "axes.unicode_minus": False, "font.size": 17,
    "text.color": INK2, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": GRID, "axes.facecolor": CARD, "figure.facecolor": CARD, "savefig.facecolor": CARD,
    "axes.grid": True, "grid.color": "#232a33", "grid.linewidth": 1, "axes.spines.top": False, "axes.spines.right": False,
})


def is_leader(t):
    return t["rank"] == 1


def attack_defense():
    T = D["teams"]
    fig, ax = plt.subplots(figsize=(12, 6.9), dpi=140)
    gf = np.array([t["gf"] for t in T]); ga = np.array([t["ga"] for t in T])
    ax.axvline(np.median(gf), color="#383835", lw=1.2, zorder=1)
    ax.axhline(np.median(ga), color="#383835", lw=1.2, zorder=1)
    others = [t for t in T if not is_leader(t)]
    ax.scatter([t["gf"] for t in others], [t["ga"] for t in others], s=46, color=DIM, edgecolor=CARD, lw=1.2, zorder=2,
               label="그 외 구단")
    leads = [t for t in T if is_leader(t)]
    ax.scatter([t["gf"] for t in leads], [t["ga"] for t in leads], s=120, color=BLUE, edgecolor=CARD, lw=2, zorder=3,
               label="리그 선두")
    from adjustText import adjust_text
    labels = [ax.text(t["gf"] + (-0.08 if t["gf"] > 4 else 0.06), t["ga"] - 0.14, t["team"] + (f' ({t["group"][:2]})' if t["group"] else ""), color=INK, fontsize=17,
                      fontweight="bold", zorder=4, ha="right" if t["gf"] > 4 else "left") for t in leads]
    ax.invert_yaxis()
    ax.set_xlabel("경기당 득점 →", fontsize=15, loc="right")
    ax.set_ylabel("← 경기당 실점 (위로 갈수록 적게 먹음)", fontsize=15, loc="top")
    xmax, ymax = gf.max() + .3, ga.max() + .3
    ax.set_xlim(0, xmax); ax.set_ylim(ymax, 0)
    adjust_text(labels, ax=ax, x=list(gf), y=list(ga), expand=(1.25, 1.6), force_text=(0.6, 0.9),
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))
    for txt, x, y, ha, va in [("화력 + 철벽", xmax - .05, .08, "right", "top"), ("철벽형", .05, .08, "left", "top"),
                              ("화력형", xmax - .05, ymax - .1, "right", "bottom"), ("고전", .05, ymax - .1, "left", "bottom")]:
        ax.text(x, y, txt, ha=ha, va=va, color=MUTED, fontsize=14)
    leg = ax.legend(loc="upper center", bbox_to_anchor=(.5, 1.08), ncol=2, frameon=False, fontsize=14)
    for t in leg.get_texts():
        t.set_color(INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "attack_defense.png"))
    plt.close(fig)


def correlation():
    T = D["teams"]
    ppg = np.array([t["ppg"] for t in T])
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), dpi=120, sharey=True)
    for ax, key, label, color, r in [(axes[0], "gf", "경기당 득점", BLUE, D["corr"]["gf"]),
                                      (axes[1], "ga", "경기당 실점", RED, D["corr"]["ga"])]:
        x = np.array([t[key] for t in T])
        ax.scatter(x, ppg, s=34, color=color, alpha=.55, edgecolor="none")
        k, b = np.polyfit(x, ppg, 1)
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, k * xs + b, color=INK, lw=2.5)
        ax.set_xlabel(label, fontsize=15)
        ax.text(.03, .95, f"r = {r:+.2f}", transform=ax.transAxes, fontsize=26, fontweight="bold", color=INK, va="top",
                bbox=dict(facecolor=CARD, edgecolor="none", alpha=.85, pad=3))
        ax.text(.03, .82, f"기울기 {k:+.2f} 승점 / 1골", transform=ax.transAxes, fontsize=14, color=INK2, va="top",
                bbox=dict(facecolor=CARD, edgecolor="none", alpha=.85, pad=3))
    axes[0].set_ylabel("경기당 승점", fontsize=15)
    axes[0].set_ylim(-0.15, 3.25)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "correlation.png"))
    plt.close(fig)


def league_dna():
    """리그 × 지표 히트맵: 각 지표를 리그 간 0~1로 정규화, 셀에는 원래 값"""
    M = D["meta"]
    cols = [("gpg", "경기당 골", "{:.2f}"), ("draw", "무승부율", "{:.0%}"), ("spread", "격차\n(승점/경기 편차)", "{:.2f}"),
            ("unbeaten", "무패 팀", "{:d}"), ("games", "평균 경기 수", "{:.0f}")]
    leagues = [m["league"] for m in M]
    raw = np.array([[m[c] for c, _, _ in cols] for m in M], dtype=float)
    norm = (raw - raw.min(0)) / np.where(np.ptp(raw, 0) == 0, 1, np.ptp(raw, 0))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#1c2430", "#184f95", "#3987e5", "#9ec5f4"])
    fig, ax = plt.subplots(figsize=(14, 6.6), dpi=120)
    ax.imshow(norm, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    ax.grid(False)
    ax.set_xticks(range(len(cols)), [c[1] for c in cols], fontsize=15, color=INK2)
    ax.set_yticks(range(len(leagues)), leagues, fontsize=16, color=INK)
    ax.tick_params(length=0); ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(len(leagues)):
        for j, (_, _, fmt) in enumerate(cols):
            v = raw[i, j]
            txt = fmt.format(int(v)) if fmt == "{:d}" else fmt.format(v)
            ax.text(j, i, txt, ha="center", va="center", fontsize=16, fontweight="bold",
                    color="#0b0b0b" if norm[i, j] > .72 else INK)
    for x in np.arange(-.5, len(cols), 1):
        ax.axvline(x, color=CARD, lw=4)
    for y in np.arange(-.5, len(leagues), 1):
        ax.axhline(y, color=CARD, lw=4)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "league_dna.png"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    attack_defense(); correlation(); league_dna()
    print("차트 저장:", sorted(os.listdir(OUT)))
