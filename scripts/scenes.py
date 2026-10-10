"""manim 데이터 모션 영상 (Python 3.12 venv에서 실행)
    manim -qh --format mp4 scripts/scenes.py GoalsRace EPLParadox
"""
import json
import os

from manim import (PI, TAU, Arc, always_redraw, DOWN, LEFT, RIGHT, UP, Circle, Create, FadeIn, FadeOut, GrowFromEdge, Indicate, Line,
                   LaggedStart, Rectangle, Scene, Text, Transform, ValueTracker, VGroup, Write, config, linear, smooth)

DECK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(DECK, "data.json"), encoding="utf-8"))

config.background_color = "#151a21"  # index.html --card
FONT = "Malgun Gothic"
INK, INK2, MUTED, GRID = "#ffffff", "#c3c2b7", "#898781", "#2c333d"
BLUE, RED, GRAY = "#3987e5", "#e66767", "#5d5c57"


def T(s, size=28, color=INK2, weight="NORMAL"):  # 한글 텍스트 (LaTeX 없이 Pango 렌더링)
    return Text(s, font=FONT, font_size=size, color=color, weight=weight)


class GoalsRace(Scene):
    """리그별 경기당 골: 막대가 0에서 자라며 숫자가 함께 카운트업"""

    def construct(self):
        meta = D["meta"]  # 이미 경기당 골 내림차순
        x0, width, row_h = -3.2, 8.6, 0.74
        top = 3.0
        vmax = max(m["gpg"] for m in meta) * 1.05
        base = Line([x0, top + 0.45, 0], [x0, top - row_h * len(meta) + 0.2, 0], color=GRID, stroke_width=2)
        self.play(Create(base), run_time=0.4)

        rows = []
        for i, m in enumerate(meta):
            y = top - i * row_h
            label = T(m["league"], 24, INK).next_to([x0, y, 0], LEFT, buff=0.3)
            bar = Rectangle(width=m["gpg"] / vmax * width, height=row_h * 0.62, stroke_width=0,
                            fill_color=BLUE if i == 0 else GRAY, fill_opacity=1)
            bar.move_to([x0 + bar.width / 2, y, 0])
            tracker = ValueTracker(0)
            num = always_redraw(lambda t=tracker, b=bar: Text(f"{t.get_value():.2f}", font=FONT, font_size=26, color=INK)
                                .next_to(b, RIGHT, buff=0.2))
            rows.append((label, bar, tracker, num, m))

        self.play(LaggedStart(*[FadeIn(r[0], shift=RIGHT * 0.2) for r in rows], lag_ratio=0.08), run_time=1.0)
        for r in rows:
            self.add(r[3])
        self.play(*[GrowFromEdge(r[1], LEFT) for r in rows],
                  *[r[2].animate.set_value(r[4]["gpg"]) for r in rows], run_time=2.2, rate_func=smooth)
        for r in rows:  # 카운트업이 끝나면 정적인 텍스트로 고정
            self.remove(r[3])
            fixed = Text(f'{r[4]["gpg"]:.2f}', font=FONT, font_size=26, color=INK).next_to(r[1], RIGHT, buff=0.2)
            self.add(fixed)

        best, worst = rows[0], rows[-1]
        worst_bar_red = worst[1].copy().set_fill(RED)
        self.play(Indicate(best[1], color=BLUE, scale_factor=1.04), run_time=0.9)
        self.play(Transform(worst[1], worst_bar_red), run_time=0.6)
        note = T(f'{best[4]["league"]} {best[4]["gpg"]:.2f}골  vs  {worst[4]["league"]} {worst[4]["gpg"]:.2f}골',
                 26, INK2).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(note, shift=UP * 0.2), run_time=0.6)
        self.wait(1.5)


class EPLParadox(Scene):
    """국내 무승부율 1위(32%) ↔ 유럽대항전 8전 8승"""

    def construct(self):
        epl_meta = next(m for m in D["meta"] if m["league"] == "프리미어리그")
        epl_eu = next(e for e in D["europe"] if e["league"] == "프리미어리그")
        draw_rank = sorted(D["meta"], key=lambda m: -m["draw"]).index(epl_meta) + 1

        # 왼쪽: 무승부율 링
        left_c = LEFT * 3.4 + UP * 0.5
        ring_bg = Circle(radius=1.6, color=GRID, stroke_width=22).move_to(left_c)
        tracker = ValueTracker(0)
        arc = always_redraw(lambda: Arc(radius=1.6, start_angle=PI / 2, angle=-TAU * max(tracker.get_value(), 0.001) / 100,
                                        stroke_width=22, color=INK2).move_arc_center_to(left_c))
        pct = always_redraw(lambda: Text(f"{tracker.get_value():.0f}%", font=FONT, font_size=60, color=INK,
                                         weight="BOLD").move_to(left_c))
        lcap = T("국내 리그 무승부율", 28, INK2).next_to(ring_bg, DOWN, buff=0.45)
        lsub = T(f"8개 리그 중 {draw_rank}위", 24, MUTED).next_to(lcap, DOWN, buff=0.15)

        self.play(Create(ring_bg), FadeIn(lcap), run_time=0.6)
        self.add(arc, pct)
        self.play(tracker.animate.set_value(epl_meta["draw"] * 100), run_time=1.6, rate_func=smooth)
        self.play(FadeIn(lsub, shift=UP * 0.1), run_time=0.4)

        # 오른쪽: 유럽대항전 8경기 결과 점등
        right_c = RIGHT * 3.2 + UP * 0.5
        n = epl_eu["n"]
        dots = VGroup(*[Circle(radius=0.36, color=GRID, fill_color=GRID, fill_opacity=1, stroke_width=0) for _ in range(n)])
        dots.arrange_in_grid(rows=2, buff=0.28).move_to(right_c + UP * 0.35)
        results = ["승"] * epl_eu["w"] + ["무"] * epl_eu["d"] + ["패"] * epl_eu["l"]
        rec = T(f'{epl_eu["w"]}승 {epl_eu["d"]}무 {epl_eu["l"]}패', 52, INK, "BOLD").next_to(dots, DOWN, buff=0.45)
        rcap = T(f'유럽대항전 · 득실 {epl_eu["gf"]}:{epl_eu["ga"]}', 28, INK2).next_to(rec, DOWN, buff=0.3)
        self.play(FadeIn(dots, lag_ratio=0.1), run_time=0.6)
        self.play(LaggedStart(*[d.animate.set_fill({"승": BLUE, "무": GRAY, "패": RED}[r]) for d, r in zip(dots, results)],
                              lag_ratio=0.18), run_time=1.6)
        self.play(Write(rec), FadeIn(rcap, shift=UP * 0.1), run_time=0.8)

        vs = T("↔", 48, MUTED).move_to(UP * 0.5)
        self.play(FadeIn(vs), run_time=0.3)
        punch = T("안에서는 비기고, 밖에서는 이긴다", 34, INK, "BOLD").to_edge(DOWN, buff=0.45)
        self.play(Write(punch), run_time=1.0)
        self.wait(1.8)
