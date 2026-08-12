"""원의 넓이는 왜 πr² 인가 — storyboard.md 의 4개 비트를 씬으로 옮긴 것.

렌더:
    python3 ../../skills/manim-video/scripts/mv.py still   circle_area.py Hook
    python3 ../../skills/manim-video/scripts/mv.py preview circle_area.py Unroll
    python3 ../../skills/manim-video/scripts/mv.py final   circle_area.py Unroll
"""

import numpy as np
from manim import *

from scene_base import PALETTE, MathScene, kr

# ---------------------------------------------------------------- 공통 설정

R = 1.7          # 화면상 원의 반지름 (유닛). 펴면 밑변이 2πR ≈ 10.7 유닛이 되는데,
                 # 화면 가로가 14.22 유닛이므로 여백을 두고 딱 들어간다.
N_RINGS = 80     # 고리 개수. 얇을수록 삼각형에 가까워진다.
HIGHLIGHT = 52   # 강조할 고리의 인덱스

RING_OUTER = BLUE_B
RING_INNER = TEAL_A

CIRCLE_CENTER = np.array([0.0, 0.35, 0.0])
# 삼각형 꼭짓점 (t=0 인 고리가 여기로 간다). 밑변은 여기서 R 만큼 아래.
# 삼각형이 2πr : r ≈ 6.3 : 1 로 납작하므로 화면 세로 가운데에 오도록 잡는다.
APEX = np.array([0.0, 0.9, 0.0])


def ring_radii() -> np.ndarray:
    """t=0 인 고리는 길이가 0이라 만들 수 없으므로 R/N 부터 시작한다."""
    return np.linspace(R / N_RINGS, R, N_RINGS)


def ring_color(t: float):
    """바깥일수록 진한 파랑, 안쪽일수록 청록. 펴진 뒤에도 이 색을 유지한다."""
    return interpolate_color(RING_INNER, RING_OUTER, t / R)


def make_rings() -> VGroup:
    rings = VGroup()
    for t in ring_radii():
        ring = Circle(radius=t, stroke_width=3.2, stroke_color=ring_color(t))
        ring.move_to(CIRCLE_CENTER)
        rings.add(ring)
    return rings


def make_unrolled() -> VGroup:
    """반지름 t 인 고리 → 길이 2πt 인 가로선.

    짧은 것(t≈0)이 위, 긴 것(t=R)이 아래로 가도록 y = APEX_y - t 에 놓는다.
    그러면 밑변 2πR, 높이 R 인 삼각형이 된다.
    """
    lines = VGroup()
    for t in ring_radii():
        half = PI * t
        line = Line(
            APEX + np.array([-half, -t, 0.0]),
            APEX + np.array([half, -t, 0.0]),
            stroke_width=3.2,
            stroke_color=ring_color(t),
        )
        lines.add(line)
    return lines


# ------------------------------------------------------------------ 비트 1


class Hook(MathScene):
    """공식은 아는데 이유는 모른다."""

    def construct(self):
        circle = Circle(radius=R, stroke_width=4, stroke_color=RING_OUTER)
        circle.move_to(CIRCLE_CENTER)
        circle.set_fill(RING_OUTER, opacity=0.12)

        radius_line = Line(CIRCLE_CENTER, CIRCLE_CENTER + RIGHT * R, stroke_width=3)
        radius_line.set_color(YELLOW)
        r_label = MathTex("r", font_size=40, color=YELLOW)
        r_label.next_to(radius_line, UP, buff=0.15)

        self.sfx("whoosh", gain=-15)
        self.play(Create(circle), run_time=1.6)
        self.play(Create(radius_line), Write(r_label), run_time=0.9)
        self.wait(0.6)

        # 한글은 LaTeX에서 깨지므로 Text로 만들고 수식만 MathTex로 붙인다
        formula = VGroup(
            kr("넓이", size=42),
            MathTex("=", font_size=52),
            MathTex(r"\pi r^2", font_size=56, color=PALETTE["accent"]),
        ).arrange(RIGHT, buff=0.25, aligned_edge=DOWN)
        formula.next_to(circle, DOWN, buff=0.8)

        question = kr("?", size=64, color=YELLOW).next_to(formula, RIGHT, buff=0.4)

        self.say("원의 넓이는 파이 알 제곱", 2.4)
        self.sfx("pop", gain=-12)
        self.play(Write(formula), run_time=1.2)
        self.wait(0.8)

        self.say("외우긴 했는데, 왜 그럴까요?", 2.6)
        self.sfx("reveal", gain=-13)
        self.play(FadeIn(question, scale=1.4), run_time=0.6)
        self.play(Indicate(question, color=YELLOW, scale_factor=1.3), run_time=0.9)
        self.wait(1.0)


# ------------------------------------------------------------------ 비트 2


class Rings(MathScene):
    """원은 얇은 고리를 겹겹이 쌓은 것이다."""

    def construct(self):
        outline = Circle(radius=R, stroke_width=4, stroke_color=RING_OUTER)
        outline.move_to(CIRCLE_CENTER)
        self.add(outline)

        rings = make_rings()

        self.say("원을 아주 얇은 고리로 잘라봅니다", 2.4)
        # 안쪽부터 바깥으로 차오르게. lag_ratio를 주면 한꺼번에 터지지 않는다.
        self.sfx("rise", gain=-14)
        self.play(
            LaggedStart(*[Create(r) for r in rings], lag_ratio=0.012),
            run_time=2.4,
        )
        self.remove(outline)
        self.wait(0.4)

        # 고리 하나만 남기고 나머지를 죽여서 시선을 모은다
        target = rings[HIGHLIGHT]
        others = VGroup(*[r for i, r in enumerate(rings) if i != HIGHLIGHT])

        t = ring_radii()[HIGHLIGHT]
        radius_line = Line(
            CIRCLE_CENTER, CIRCLE_CENTER + RIGHT * t, stroke_width=3, color=YELLOW
        )
        t_label = MathTex("t", font_size=38, color=YELLOW)
        t_label.next_to(radius_line, DOWN, buff=0.12)

        self.say("반지름이 t 인 고리 하나를 봅시다", 2.2)
        self.play(
            others.animate.set_stroke(opacity=0.18),
            target.animate.set_stroke(color=YELLOW, width=5),
            run_time=1.0,
        )
        self.sfx("tick", gain=-16)
        self.play(Create(radius_line), Write(t_label), run_time=0.8)
        self.wait(0.4)

        circ = VGroup(
            kr("고리의 길이", size=30),
            MathTex("=", font_size=38),
            MathTex(r"2\pi t", font_size=44, color=YELLOW),
        ).arrange(RIGHT, buff=0.22, aligned_edge=DOWN)
        circ.next_to(rings, DOWN, buff=0.7)

        self.say("이 고리의 길이는 2πt 입니다", 2.8)
        self.play(Write(circ), run_time=1.2)
        self.play(Indicate(target, color=YELLOW, scale_factor=1.06), run_time=1.0)
        self.wait(0.6)

        self.play(
            FadeOut(radius_line), FadeOut(t_label), FadeOut(circ),
            others.animate.set_stroke(opacity=1.0),
            target.animate.set_stroke(color=ring_color(t), width=3.2),
            run_time=1.0,
        )
        self.clear_subtitle()


# ------------------------------------------------------------------ 비트 3


class Unroll(MathScene):
    """고리를 펴서 짧은 것부터 쌓으면 삼각형이 된다."""

    def construct(self):
        rings = make_rings()
        self.add(rings)
        self.wait(0.5)

        self.say("이 고리들을 하나씩 펴서", 2.2)

        lines = make_unrolled()
        # VGroup 순서가 서로 대응하므로 고리 i 가 선 i 로 간다.
        # 시간이 흐르는 변형이 아니라 형태 변형이므로 rate_func는 기본 smooth.
        self.sfx("sweep", gain=-13)
        self.play(
            LaggedStart(
                *[Transform(ring, line) for ring, line in zip(rings, lines)],
                lag_ratio=0.008,
            ),
            run_time=4.5,
        )
        self.wait(0.8)

        self.say("짧은 것부터 쌓으면, 삼각형이 됩니다", 2.2)

        base_y = APEX[1] - R
        tri = Polygon(
            APEX,
            np.array([-PI * R, base_y, 0.0]),
            np.array([PI * R, base_y, 0.0]),
            stroke_width=3,
            stroke_color=WHITE,
            fill_opacity=0,
        )
        self.sfx("pop", gain=-14)
        self.play(Create(tri), run_time=1.6)
        self.wait(0.3)

        base_brace = Brace(
            Line(np.array([-PI * R, base_y, 0.0]), np.array([PI * R, base_y, 0.0])),
            direction=DOWN,
            color=PALETTE["accent"],
        )
        base_label = MathTex(r"2\pi r", font_size=44, color=PALETTE["accent"])
        base_label.next_to(base_brace, DOWN, buff=0.12)

        # 높이 표시는 삼각형 **바깥**에 둔다. 안쪽에 그리면 고리들이 만든
        # 밝은 면에 묻혀서 스틸에서 아예 안 보인다 (실제로 그래서 옮겼다).
        # +0.35 로 두면 브레이스와 r 라벨이 title-safe 밖으로 나간다
        # (mv.py layout 이 좌표로 잡아줬다). 0.12 가 상한.
        guide_x = PI * R + 0.12
        guide = DashedLine(
            APEX, np.array([guide_x, APEX[1], 0.0]),
            stroke_width=2, color=GREY_B, dash_length=0.08,
        )
        height_brace = BraceBetweenPoints(
            np.array([guide_x, base_y, 0.0]),
            np.array([guide_x, APEX[1], 0.0]),
            direction=RIGHT,
            color=PALETTE["accent"],
        )
        height_label = MathTex("r", font_size=44, color=PALETTE["accent"])
        height_label.next_to(height_brace, RIGHT, buff=0.12)

        self.say("밑변은 가장 바깥 고리의 길이, 2πr", 2.8)
        self.play(GrowFromCenter(base_brace), Write(base_label), run_time=1.0)
        self.wait(0.8)

        self.say("높이는 반지름 r", 2.4)
        self.play(Create(guide), run_time=0.5)
        self.play(GrowFromCenter(height_brace), Write(height_label), run_time=0.9)
        self.wait(1.2)
        self.clear_subtitle()


# ------------------------------------------------------------------ 비트 4


class Result(MathScene):
    """계산하면 공식이 나온다."""

    def construct(self):
        step1 = MathTex(
            r"\frac{1}{2}", r"\times", r"2\pi r", r"\times", "r", font_size=60
        )
        step1[2].set_color(PALETTE["accent"])
        step1[4].set_color(PALETTE["accent"])
        step1.move_to(UP * 1.1)

        caption = kr("삼각형 넓이 = ½ × 밑변 × 높이", size=30, color=GREY_A)
        caption.next_to(step1, UP, buff=0.6)

        self.play(FadeIn(caption, shift=DOWN * 0.2), run_time=0.6)
        self.play(Write(step1), run_time=1.4)
        self.wait(1.4)

        self.say("계산하면", 1.4)

        # step1/step2 를 충분히 벌린다. 가까이 두면 사이의 "=" 가
        # 아래 수식 위에 겹쳐 붙는다 (스틸에서 확인하고 벌린 값이다).
        step2 = MathTex(r"\pi", "r", "^2", font_size=76, color=PALETTE["accent"])
        step2.move_to(DOWN * 1.35)

        arrow = MathTex("=", font_size=52).move_to(DOWN * 0.1)
        self.play(Write(arrow), run_time=0.4)
        self.sfx("click", gain=-16)
        self.play(TransformFromCopy(step1, step2), run_time=1.6)
        self.wait(1.0)

        box = SurroundingRectangle(step2, color=PALETTE["accent"], buff=0.25, stroke_width=3)
        self.sfx("chime", gain=-12)
        self.play(Create(box), run_time=0.8)
        self.say("원의 넓이, 파이 알 제곱입니다", 3.2)
        self.wait(1.0)
