"""모든 씬의 출발점.

이 파일을 복사해서 시작한다. 팔레트·폰트·자막 헬퍼가 들어있고,
프로젝트 전체에서 이걸 import 해서 색과 폰트를 한 곳에서 관리한다.

    from scene_base import PALETTE, KR_FONT, subtitle, title_card

렌더:
    manim -pql scene_base.py TitleDemo
"""

import os

from manim import *

# ---------------------------------------------------------------- 설정

config.background_color = "#0f0f14"  # 순검정보다 눈이 덜 아프다

KR_FONT = os.environ.get("MV_KR_FONT", "NanumGothic")
LANG = os.environ.get("MV_LANG", "ko")

# 변수 하나 = 색 하나. 수식·그래프·라벨 어디에 나오든 같은 색을 쓴다.
PALETTE = {
    "x": BLUE_B,
    "y": YELLOW,
    "z": RED_C,
    "accent": TEAL_A,
    "muted": GREY_B,
}


# ---------------------------------------------------------------- 헬퍼


def kr(text: str, size: int = 36, color=WHITE, **kwargs) -> Text:
    """한글 텍스트. font 인자를 매번 쓰지 않기 위한 래퍼."""
    return Text(text, font=KR_FONT, font_size=size, color=color, **kwargs)


def subtitle(text: str, size: int = 30) -> Text:
    """화면 하단 자막. 내레이션 전문이 아니라 핵심 구절만 넣는다."""
    return kr(text, size=size, color=GREY_A).to_edge(DOWN, buff=0.45)


def title_card(text: str, size: int = 52) -> Text:
    """상단 고정 제목. 씬 내내 같은 위치를 유지한다."""
    return kr(text, size=size).to_edge(UP, buff=0.5)


def mixed(*parts, buff: float = 0.15) -> VGroup:
    """한글과 수식을 한 줄에 섞는다.

    문자열은 Text로, MathTex/Mobject는 그대로 배치한다.

        mixed("넓이는 ", MathTex(r"\\pi r^2"), " 입니다")
    """
    mobs = [kr(p) if isinstance(p, str) else p for p in parts]
    return VGroup(*mobs).arrange(RIGHT, buff=buff, aligned_edge=DOWN)


def colored_eq(*tex_parts, colors: dict | None = None, **kwargs) -> MathTex:
    """항별로 나눠 만든 수식에 색을 입힌다.

        colored_eq("x", "+", "y", "=", "z",
                   colors={"x": PALETTE["x"], "y": PALETTE["y"]})

    통짜 문자열이 아니라 항을 나눠 넘겨야 인덱싱과
    TransformMatchingTex가 제대로 동작한다.
    """
    eq = MathTex(*tex_parts, **kwargs)
    for i, part in enumerate(tex_parts):
        if colors and part in colors:
            eq[i].set_color(colors[part])
    return eq


class MathScene(Scene):
    """자막 관리가 붙은 Scene 베이스.

    self.say("...", 2.5) 로 자막을 띄우고 지운다.
    """

    def setup(self):
        super().setup()
        self._sub = None

    def say(self, text: str, duration: float = 2.0):
        """자막을 띄우고 duration 만큼 기다린 뒤 다음 자막으로 교체한다."""
        new = subtitle(text)
        if self._sub is None:
            self.play(FadeIn(new, shift=UP * 0.2), run_time=0.4)
        else:
            self.play(FadeTransform(self._sub, new), run_time=0.4)
        self._sub = new
        self.wait(max(duration - 0.4, 0))

    def clear_subtitle(self):
        if self._sub is not None:
            self.play(FadeOut(self._sub), run_time=0.3)
            self._sub = None


# ---------------------------------------------------------------- 데모


class TitleDemo(MathScene):
    """베이스가 제대로 동작하는지 확인하는 스모크 테스트 씬.

    한글 폰트, LaTeX, 색 팔레트, 자막을 한 번에 검증한다.
    깨지는 게 있으면 여기서 먼저 드러난다.
    """

    def construct(self):
        title = title_card("카오스란 무엇인가")
        self.play(Write(title), run_time=1.2)
        self.wait(0.6)

        eq = colored_eq(
            r"\frac{dx}{dt}", "=", r"\sigma", "(", "y", "-", "x", ")",
            colors={"y": PALETTE["y"], "x": PALETTE["x"]},
            font_size=56,
        )
        self.play(Write(eq), run_time=1.5)
        self.wait(1.0)

        self.say("초기 조건의 아주 작은 차이가", 2.2)
        self.say("전혀 다른 미래를 만듭니다", 2.2)

        self.play(Indicate(eq[4], color=PALETTE["accent"], scale_factor=1.4))
        self.wait(0.5)

        # 스모크 테스트이므로 마지막 프레임에 전부 남겨둔다.
        # (still 렌더로 한글·수식·색을 한 장에서 확인할 수 있어야 한다)
        self.wait(1.0)
