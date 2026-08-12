"""함수 그래프 — 접선, 리만합, 파라미터 훑기.

좌표는 전부 axes.c2p()를 거친다. 축 범위를 바꿔도 안 깨지는
유일한 방법이다.

렌더:
    manim -pql graph_plot.py TangentSlope
    manim -pql graph_plot.py RiemannSum
    manim -pql graph_plot.py ParameterSweep
"""

import numpy as np
from manim import *

from scene_base import PALETTE, MathScene, kr


def make_axes(x_range=(-1, 4, 1), y_range=(-1, 9, 2)) -> Axes:
    return Axes(
        x_range=list(x_range),
        y_range=list(y_range),
        x_length=10,
        y_length=6,
        axis_config={"include_numbers": True, "font_size": 24},
        tips=False,
    ).to_edge(DOWN, buff=0.6)


class TangentSlope(MathScene):
    """접선의 기울기가 곧 도함수라는 걸 점을 움직여 보여준다."""

    def construct(self):
        axes = make_axes()
        func = lambda x: x**2
        graph = axes.plot(func, x_range=[-0.6, 3.0], color=PALETTE["x"])
        # 라벨 위치는 스틸을 보고 정한다. UR로 두면 곡선 위에 겹친다.
        graph_label = axes.get_graph_label(
            graph, MathTex("f(x) = x^2"), x_val=1.4, direction=UL, buff=0.4
        )

        self.play(Create(axes), run_time=1.0)
        self.play(Create(graph), Write(graph_label), run_time=1.5)
        self.wait(0.8)

        # ValueTracker: 애니메이션 가능한 스칼라. 이걸 축으로 삼는다.
        x = ValueTracker(0.4)

        # always_redraw는 매 프레임 새로 만든다. 가벼운 객체에만.
        dot = always_redraw(
            lambda: Dot(axes.c2p(x.get_value(), func(x.get_value())),
                        color=PALETTE["y"], radius=0.08)
        )
        tangent = always_redraw(
            lambda: TangentLine(graph, alpha=_alpha(axes, graph, x.get_value()),
                                length=5, color=PALETTE["y"], stroke_width=3)
        )
        slope_label = always_redraw(
            lambda: MathTex(f"f'({x.get_value():.2f}) = {2 * x.get_value():.2f}",
                            font_size=40, color=PALETTE["y"]).to_corner(UR, buff=0.8)
        )

        self.add(tangent, dot, slope_label)
        self.wait(0.5)

        self.say("점을 옮기면 접선의 기울기가 따라 변한다", 2.0)
        # 파라미터를 훑는 동작은 등속이어야 한다
        self.play(x.animate.set_value(2.8), run_time=5, rate_func=linear)
        self.play(x.animate.set_value(0.4), run_time=4, rate_func=linear)

        self.say("그 기울기를 모아놓은 게 도함수다", 2.5)
        self.clear_subtitle()


def _alpha(axes, graph, x_val: float) -> float:
    """x값을 그래프 위 상대 위치(0~1)로 바꾼다. TangentLine이 alpha를 받기 때문."""
    x_min, x_max = graph.t_min, graph.t_max
    return float(np.clip((x_val - x_min) / (x_max - x_min), 0.0, 1.0))


class RiemannSum(MathScene):
    """직사각형을 잘게 쪼개면 넓이에 수렴한다."""

    def construct(self):
        axes = make_axes(x_range=(0, 3.5, 1), y_range=(0, 10, 2))
        func = lambda x: x**2
        graph = axes.plot(func, x_range=[0, 3], color=PALETTE["x"])

        self.play(Create(axes), Create(graph), run_time=1.5)

        area = axes.get_area(graph, x_range=[0, 3], color=PALETTE["accent"], opacity=0.25)
        self.play(FadeIn(area), run_time=0.8)
        self.say("이 넓이를 구하고 싶다", 2.0)

        rects = axes.get_riemann_rectangles(
            graph, x_range=[0, 3], dx=0.5,
            color=(PALETTE["y"], PALETTE["z"]), stroke_width=1, fill_opacity=0.7,
        )
        self.play(FadeOut(area), Create(rects), run_time=1.2)
        self.say("직사각형으로 근사한 뒤", 1.8)

        # 폭을 줄여가며 교체 — 수렴을 눈으로 보여준다
        for dx in (0.25, 0.125, 0.0625, 0.03125):
            finer = axes.get_riemann_rectangles(
                graph, x_range=[0, 3], dx=dx,
                color=(PALETTE["y"], PALETTE["z"]), stroke_width=0.4, fill_opacity=0.7,
            )
            self.play(Transform(rects, finer), run_time=0.7)

        self.say("폭을 0으로 보내면, 그게 적분이다", 2.5)

        # 곡선이 오른쪽 위를 차지하므로 결과는 왼쪽 위로 뺀다
        result = MathTex(r"\int_0^3 x^2\,dx = 9", font_size=52, color=PALETTE["accent"])
        result.to_corner(UL, buff=0.8)
        self.play(Write(result), run_time=1.2)
        self.wait(2.0)
        self.clear_subtitle()


class ParameterSweep(MathScene):
    """계수 하나를 움직이면 곡선 전체가 어떻게 변하는가."""

    def construct(self):
        axes = make_axes(x_range=(-3, 3, 1), y_range=(-3, 3, 1))
        a = ValueTracker(1.0)

        graph = always_redraw(
            lambda: axes.plot(
                lambda x: np.sin(a.get_value() * x),
                x_range=[-3, 3, 0.02],
                color=PALETTE["x"],
            )
        )
        label = always_redraw(
            lambda: MathTex(rf"\sin({a.get_value():.1f}\,x)", font_size=44,
                            color=PALETTE["x"]).to_corner(UR, buff=0.8)
        )

        self.play(Create(axes), run_time=1.0)
        self.add(graph, label)
        self.wait(0.6)

        self.say("계수 하나가 파동의 촘촘함을 정한다", 2.0)
        self.play(a.animate.set_value(4.0), run_time=5, rate_func=linear)
        self.play(a.animate.set_value(0.5), run_time=4, rate_func=linear)
        self.play(a.animate.set_value(1.0), run_time=2, rate_func=smooth)
        self.wait(1.0)
        self.clear_subtitle()
