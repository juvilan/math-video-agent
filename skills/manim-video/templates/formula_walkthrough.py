"""수식을 항별로 색칠하고, 짚고, 설명을 붙인다.

수식 하나를 화면에 띄우고 "이 항이 무슨 뜻인지"를 순서대로
짚어주는, 수학 영상에서 가장 자주 쓰이는 패턴.

핵심은 **수식을 항별로 나눠 만드는 것**. 통짜 문자열로 만들면
인덱싱도 TransformMatchingTex도 제대로 안 된다.

    MathTex(r"e^{i\\pi} + 1 = 0")            # ✗ 통짜
    MathTex("e^{i\\pi}", "+", "1", "=", "0")  # ✓ 항별

렌더:
    manim -pql formula_walkthrough.py FormulaWalkthrough
    manim -pql formula_walkthrough.py GlyphIndexCheck   # 글리프 번호 확인용
"""

from manim import *

from scene_base import KR_FONT, PALETTE, MathScene, kr

# 항 → (색, 한국어 설명). 여기만 고치면 씬 전체가 따라온다.
ANNOTATIONS = [
    (0, PALETTE["x"], "변화율: 지금 얼마나 빠르게 변하는가"),
    (2, PALETTE["accent"], "비례상수: 얼마나 세게 끌어당기는가"),
    (4, PALETTE["y"], "차이: 목표에서 얼마나 떨어져 있는가"),
]


class FormulaWalkthrough(MathScene):
    """뉴턴 냉각법칙을 항별로 분해한다."""

    def construct(self):
        # \left( ... \right) 는 두 조각으로 나누면 글리프 분배가 어긋난다.
        # 항을 나눠 쓸 때는 평범한 괄호를 쓴다.
        eq = MathTex(
            r"\frac{dT}{dt}",  # 0
            "=",               # 1
            "-k",              # 2
            "(",               # 3
            "T - T_{env}",     # 4
            ")",               # 5
            font_size=64,
        )
        eq.to_edge(UP, buff=1.2)

        self.play(Write(eq), run_time=1.6)
        self.wait(1.0)

        # 항을 하나씩 짚는다. 색을 주는 순간이 곧 "여기 보세요" 신호다.
        for index, color, note in ANNOTATIONS:
            target = eq[index]

            box = SurroundingRectangle(target, color=color, buff=0.12, stroke_width=3)
            label = kr(note, size=30, color=color)
            label.next_to(eq, DOWN, buff=1.0)

            self.play(
                Create(box),
                target.animate.set_color(color),
                FadeIn(label, shift=UP * 0.2),
                run_time=0.8,
            )
            self.wait(2.2)  # 읽을 시간. 이 wait이 없으면 아무도 못 읽는다.
            self.play(FadeOut(box), FadeOut(label), run_time=0.4)

        self.wait(0.5)

        # 마지막에 전체를 한 번 강조하고 결론
        conclusion = kr("뜨거울수록 빨리 식는다 — 그게 전부다", size=34)
        conclusion.next_to(eq, DOWN, buff=1.2).set_color(PALETTE["accent"])
        self.play(
            Circumscribe(eq, color=PALETTE["accent"], buff=0.2, run_time=1.5),
            FadeIn(conclusion, shift=UP * 0.2),
        )
        self.wait(2.5)


class SubstringColoring(Scene):
    """통짜 수식에 부분 문자열로 색을 입히는 방법 (차선책).

    항을 나눠 만들 수 없는 상황 — 예를 들어 외부에서 받은 LaTeX
    문자열을 그대로 써야 할 때만 쓴다. 부분 문자열 매칭이라
    의도치 않은 곳까지 칠해지기 쉽다.
    """

    def construct(self):
        eq = MathTex(r"x^2 + y^2 = r^2", font_size=72)
        eq.set_color_by_tex("x", PALETTE["x"])
        eq.set_color_by_tex("y", PALETTE["y"])
        self.play(Write(eq))
        self.wait(1)

        warn = kr(
            "set_color_by_tex는 부분 문자열 매칭이다.\n"
            "정확히 하려면 항을 나눠 만들어라.",
            size=26,
            color=GREY_B,
        )
        warn.next_to(eq, DOWN, buff=1.0)
        self.play(FadeIn(warn))
        self.wait(3)


class GlyphIndexCheck(Scene):
    """글리프 인덱스를 눈으로 확인하는 스캐폴딩 씬.

    개별 글자를 움직이려면 eq[0][n]의 n을 알아야 하는데, LaTeX
    조판 결과의 글리프 순서는 소스 순서와 다를 수 있다.
    추측하지 말고 여기서 번호를 보고 쓴다.

        manim -s -ql formula_walkthrough.py GlyphIndexCheck

    로 스틸을 뽑아 Read 툴로 열어본다.
    """

    def construct(self):
        eq = MathTex(r"\int_0^\infty e^{-x^2}\,dx = \frac{\sqrt{\pi}}{2}", font_size=72)
        self.add(eq)
        self.add(index_labels(eq[0]))
        self.wait()
