"""수식 A → 수식 B, 글자가 제자리를 찾아 날아가는 변형.

원본 영상의 "아나그램" 기법. 식을 다시 쓰는 게 아니라 **같은
글자가 이동한다**는 걸 보여줘서, 두 식이 같은 식이라는 사실을
시각적으로 납득시킨다.

세 가지 도구가 있고 쓰임이 다르다:

  TransformMatchingTex     항 문자열이 같은 것끼리 매칭 (권장)
  TransformMatchingShapes  글리프 모양이 비슷한 것끼리 (통짜 수식용)
  Transform(eq[i], eq2[j]) 손으로 짝지음 (완전 통제)

렌더:
    manim -pql transform_anagram.py RearrangeEquation
"""

from manim import *

from scene_base import PALETTE, kr


class RearrangeEquation(Scene):
    """이차방정식을 완전제곱식으로 옮긴다 — 항이 자리를 바꾼다."""

    def construct(self):
        # 변수 하나 = 색 하나. 항의 모양이 바뀌어도(b → b/a) 색은 따라간다.
        colors = {
            "a": PALETTE["x"],
            "b": PALETTE["y"],
            "c": PALETTE["z"],
            r"\frac{b}{a}": PALETTE["y"],
            r"-\frac{c}{a}": PALETTE["z"],
        }

        def tint(eq):
            for part in eq:
                tex = part.get_tex_string()
                if tex in colors:
                    part.set_color(colors[tex])
            return eq

        # TransformMatchingTex는 '같은 tex 문자열'을 키로 매칭한다.
        # 그래서 양쪽 다 항을 같은 방식으로 쪼개 만들어야 한다.
        eq1 = tint(MathTex("a", "x^2", "+", "b", "x", "+", "c", "=", "0", font_size=64))
        eq2 = tint(MathTex("a", "x^2", "+", "b", "x", "=", "-", "c", font_size=64))
        eq3 = tint(MathTex("x^2", "+", r"\frac{b}{a}", "x", "=", r"-\frac{c}{a}", font_size=64))

        self.play(Write(eq1), run_time=1.5)
        self.wait(1.2)

        # c가 우변으로 날아간다
        self.play(TransformMatchingTex(eq1, eq2), run_time=1.8)
        self.wait(1.5)

        self.play(TransformMatchingTex(eq2, eq3), run_time=1.8)
        self.wait(2.0)

        note = kr("항이 사라졌다 나타나는 게 아니라, 옮겨간다", size=30, color=GREY_A)
        note.next_to(eq3, DOWN, buff=1.0)
        self.play(FadeIn(note, shift=UP * 0.2))
        self.wait(2.5)


class GlyphAnagram(Scene):
    """글리프 단위로 손수 짝지어 움직이는 버전.

    TransformMatchingTex가 매칭에 실패하거나, 특정 글자만 튀게
    움직이고 싶을 때. 인덱스는 GlyphIndexCheck 씬으로 먼저 확인한다.
    """

    def construct(self):
        src = MathTex(r"e^{i\pi} + 1 = 0", font_size=80)
        dst = MathTex(r"e^{i\pi} = -1", font_size=80)

        self.play(Write(src), run_time=1.5)
        self.wait(1.5)

        # 모양이 비슷한 글리프끼리 알아서 이어준다.
        # 통짜 수식(항 분리 없음)에는 이쪽이 실용적이다.
        self.play(TransformMatchingShapes(src, dst), run_time=2.0)
        self.wait(2.0)


class HighlightThenSplit(Scene):
    """한 수식에서 부분식을 떼어내 따로 키워 보여준 뒤 되돌린다.

    "이 안에 이런 게 숨어 있다"를 보여주는 패턴.
    """

    def construct(self):
        eq = MathTex(
            r"\sum_{n=1}^{\infty}", r"\frac{1}{n^2}", "=", r"\frac{\pi^2}{6}",
            font_size=64,
        )
        self.play(Write(eq), run_time=1.5)
        self.wait(1.0)

        # 부분식을 복제해서 떼어낸다 (원본은 그대로 남겨둔다)
        piece = eq[1].copy()
        self.play(
            piece.animate.scale(2.2).next_to(eq, DOWN, buff=1.2).set_color(PALETTE["accent"]),
            eq.animate.set_opacity(0.35),
            run_time=1.2,
        )

        label = kr("역수의 제곱을 전부 더한다", size=30, color=PALETTE["accent"])
        label.next_to(piece, DOWN, buff=0.5)
        self.play(FadeIn(label, shift=UP * 0.2))
        self.wait(2.5)

        self.play(
            FadeOut(label),
            piece.animate.scale(1 / 2.2).move_to(eq[1]).set_color(WHITE),
            eq.animate.set_opacity(1.0),
            run_time=1.0,
        )
        self.remove(piece)
        self.wait(1.0)
