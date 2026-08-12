"""벡터장, 흐름선, 선형변환.

"공간 전체가 움직인다"를 보여주는 패턴. 선형대수/미분방정식
영상의 핵심 도구.

렌더:
    manim -pql vector_field.py LinearTransform
    manim -pql vector_field.py FlowLines
"""

import numpy as np
from manim import *

from scene_base import PALETTE, MathScene, kr


class LinearTransform(MathScene):
    """행렬은 격자 전체를 늘이고 비트는 것이다."""

    def construct(self):
        plane = NumberPlane(
            x_range=[-7, 7, 1],
            y_range=[-4, 4, 1],
            background_line_style={"stroke_opacity": 0.4, "stroke_width": 1},
        )
        self.add(plane)

        # 기저벡터 — 변환 전후를 추적할 대상
        i_hat = Arrow(plane.c2p(0, 0), plane.c2p(1, 0), buff=0, color=PALETTE["x"])
        j_hat = Arrow(plane.c2p(0, 0), plane.c2p(0, 1), buff=0, color=PALETTE["y"])
        unit_square = Polygon(
            plane.c2p(0, 0), plane.c2p(1, 0), plane.c2p(1, 1), plane.c2p(0, 1),
            stroke_width=0, fill_color=PALETTE["accent"], fill_opacity=0.35,
        )

        self.play(FadeIn(unit_square), GrowArrow(i_hat), GrowArrow(j_hat), run_time=1.2)
        self.say("단위 정사각형의 넓이는 1", 2.0)

        matrix = [[2, 1], [1, 2]]
        matrix_tex = MathTex(
            r"\begin{bmatrix} 2 & 1 \\ 1 & 2 \end{bmatrix}", font_size=48
        ).to_corner(UL, buff=0.6)
        self.play(Write(matrix_tex), run_time=1.0)

        self.say("이 행렬을 곱하면 공간 전체가 늘어난다", 2.2)
        self.play(
            plane.animate.apply_matrix(matrix),
            i_hat.animate.apply_matrix(matrix),
            j_hat.animate.apply_matrix(matrix),
            unit_square.animate.apply_matrix(matrix),
            run_time=3,
        )
        self.wait(0.8)

        det = MathTex(r"\det = 3", font_size=48, color=PALETTE["accent"])
        det.next_to(matrix_tex, DOWN, buff=0.4)
        self.play(Write(det))
        self.say("넓이가 3배 — 그게 행렬식이다", 3.0)
        self.clear_subtitle()


class FlowLines(MathScene):
    """벡터장 위를 점들이 흘러간다."""

    def construct(self):
        # 장이 0이 되는 점이 있으면 StreamLines가 길이 0짜리 선을 만들어
        # run_time이 음수가 되며 터진다. 어디서도 0이 되지 않는 장을 쓴다.
        def field_func(pos):
            return np.sin(pos[1] / 2) * RIGHT + np.cos(pos[0] / 2) * UP

        field = ArrowVectorField(
            field_func,
            colors=[PALETTE["muted"], PALETTE["x"], PALETTE["accent"]],
        )
        self.play(Create(field), run_time=2.0)
        self.say("각 점마다 '어디로 갈지'가 정해져 있다", 2.5)

        stream = StreamLines(
            field_func,
            x_range=[-7, 7, 1],      # 간격을 넓혀야 화면이 선으로 뒤덮이지 않는다
            y_range=[-4, 4, 1],
            stroke_width=2,
            virtual_time=3,
            max_anchors_per_line=30,
        )
        self.add(stream)
        stream.start_animation(warm_up=False, flow_speed=1.5)
        self.say("따라가면 이런 흐름이 된다", 3.0)
        self.wait(stream.virtual_time / stream.flow_speed)

        self.play(field.animate.set_opacity(0.15), run_time=1.0)
        self.wait(2)
        stream.end_animation()
        self.clear_subtitle()
