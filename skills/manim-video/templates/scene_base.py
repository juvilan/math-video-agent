"""모든 씬의 출발점.

이 파일을 복사해서 시작한다. 팔레트·폰트·자막 헬퍼가 들어있고,
프로젝트 전체에서 이걸 import 해서 색과 폰트를 한 곳에서 관리한다.

    from scene_base import PALETTE, KR_FONT, subtitle, title_card

렌더:
    manim -pql scene_base.py TitleDemo
"""

import os
import sys
from pathlib import Path

from manim import *

# ---------------------------------------------------------------- 설정

config.background_color = "#0f0f14"  # 순검정보다 눈이 덜 아프다

KR_FONT = os.environ.get("MV_KR_FONT", "NanumGothic")
LANG = os.environ.get("MV_LANG", "ko")

# 제작자 취향 노브. .mv/intent.md 에 적어둔 값을 환경변수로 넘긴다.
# "더 천천히" / "글씨 좀 키워" 같은 요청을 코드를 안 고치고 처리하기 위한 것.
#
#   MV_PACE=1.25 manim ...     전체 속도 25% 느리게
#   MV_TEXT_SCALE=1.1 manim ...  글자 10% 크게
#
# PACE 는 play(run_time=...) 로 **명시한** 값과 wait 에만 걸린다.
# 애니메이션 객체에 직접 준 run_time 은 건드리지 않는다.
PACE = float(os.environ.get("MV_PACE", "1.0"))
TEXT_SCALE = float(os.environ.get("MV_TEXT_SCALE", "1.0"))

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
    return Text(text, font=KR_FONT, font_size=size * TEXT_SCALE,
                color=color, **kwargs)


def subtitle(text: str, size: int = 30) -> Text:
    """화면 하단 자막. 내레이션 전문이 아니라 핵심 구절만 넣는다.

    buff 0.45 로 두면 1080p에서 title-safe(90%) 하단선에 글자가 걸친다
    (qc.py guides 로 확인). 0.6 이 유튜브 진행바까지 피하는 최소값이다.
    """
    return kr(text, size=size, color=GREY_A).to_edge(DOWN, buff=0.6)


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
            self.wait(max(duration - 0.4, 0))
            self._sub = new
            return

        # 크로스페이드(FadeTransform)로 바꾸면 두 자막이 0.4초 동안 같은
        # 자리에 겹쳐 글자가 뭉개진다 (qc.py sheet 로 확인). 글자끼리는
        # 겹치지 않게 앞 자막을 먼저 지우고 새 자막을 넣는다.
        self.play(FadeOut(self._sub, shift=DOWN * 0.15), run_time=0.22)
        self.play(FadeIn(new, shift=UP * 0.15), run_time=0.22)
        self._sub = new
        self.wait(max(duration - 0.44, 0))

    def clear_subtitle(self):
        if self._sub is not None:
            self.play(FadeOut(self._sub), run_time=0.3)
            self._sub = None

    # ------------------------------------------------------------ 효과음

    def sfx(self, name: str, gain: float = -8.0, ahead: float = 0.06):
        """효과음을 지금 시점에 깐다.

        name 은 assets/sfx/ 안의 파일명(확장자 생략 가능) 또는 전체 경로.
        ahead 만큼 **앞당겨** 재생한다 — 소리는 화면보다 조금 먼저 나야
        붙어서 들린다.

        파일이 없으면 조용히 넘어가지 않고 경고를 찍는다. 소리가 빠진 건
        렌더 결과를 봐서는 알 수 없기 때문이다.
        """
        path = resolve_sfx(name)
        if path is None:
            print(f"[sfx] 없음: {name} (찾은 곳: {SFX_DIR}) — 소리 없이 진행",
                  file=sys.stderr)
            return

        # 씬 맨 앞에서 앞당기면 타임스탬프가 음수가 되어 manim 이
        # ValueError 를 낸다. 그런데 그 예외를 렌더러가 삼키고 렌더는
        # "성공"으로 끝난다 — 소리만 조용히 빠진다. 그래서 여기서 막는다.
        now = float(getattr(self.renderer, "time", 0.0) or 0.0)
        offset = -min(abs(ahead), now)
        self.add_sound(str(path), gain=gain, time_offset=offset)

    # ------------------------------------------------- 레이아웃 자동 점검

    def wait(self, duration: float = 1.0, **kwargs):
        return super().wait(duration * PACE, **kwargs)

    def play(self, *args, **kwargs):
        if PACE != 1.0 and "run_time" in kwargs:
            kwargs["run_time"] = kwargs["run_time"] * PACE
        result = super().play(*args, **kwargs)
        self._play_index = getattr(self, "_play_index", -1) + 1
        if LAYOUT_CHECK:
            report_layout(self, f"play#{self._play_index}")
        return result


# ---------------------------------------------------------------- 효과음

SFX_DIR = Path(os.environ.get("MV_SFX_DIR", "assets/sfx"))
SFX_EXTS = (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aiff")


def resolve_sfx(name: str) -> Path | None:
    """효과음 파일을 찾는다. 확장자 없이 이름만 줘도 된다."""
    candidate = Path(name)
    if candidate.is_file():
        return candidate
    if candidate.suffix:
        path = SFX_DIR / candidate.name
        return path if path.is_file() else None
    for ext in SFX_EXTS:
        path = SFX_DIR / f"{name}{ext}"
        if path.is_file():
            return path
    return None


# ------------------------------------------------------- 레이아웃 점검

# MV_LAYOUT=1 이면 self.play 마다 화면 배치를 좌표로 검사해 텍스트로 찍는다.
# 스틸 PNG를 Read 하지 않고도 화면 밖 / 안전영역 이탈 / 글자 겹침을 잡을 수
# 있다 — 이미지 한 장이 텍스트 리포트 수십 줄보다 훨씬 비싸다.
LAYOUT_CHECK = os.environ.get("MV_LAYOUT", "") not in ("", "0", "false")

FRAME_HALF_W = config.frame_width / 2      # 7.11
FRAME_HALF_H = config.frame_height / 2     # 4.0
TITLE_SAFE = 0.90                          # 방송 기준. 이 밖은 잘릴 수 있다
SAFE_HALF_W = FRAME_HALF_W * TITLE_SAFE
SAFE_HALF_H = FRAME_HALF_H * TITLE_SAFE

TEXTLIKE = (Text, MarkupText, MathTex, Tex, SingleStringMathTex)


def _describe(mob) -> str:
    name = type(mob).__name__
    for attr in ("text", "tex_string"):
        value = getattr(mob, attr, None)
        if isinstance(value, str) and value.strip():
            snippet = value.strip().replace("\n", " ")[:22]
            return f"{name}('{snippet}')"
    return name


def _box(mob):
    """(left, right, bottom, top). 점이 없으면 None."""
    if not mob.get_all_points().size:
        return None
    return (
        float(mob.get_left()[0]), float(mob.get_right()[0]),
        float(mob.get_bottom()[1]), float(mob.get_top()[1]),
    )


def _is_textlike(mob) -> bool:
    if isinstance(mob, TEXTLIKE):
        return True
    subs = getattr(mob, "submobjects", [])
    return bool(subs) and all(isinstance(s, TEXTLIKE) for s in subs)


def report_layout(scene, label: str = "") -> list[str]:
    """현재 화면 배치를 좌표로 검사해 문제를 텍스트로 돌려준다.

    잡는 것: 화면 밖 / title-safe 밖 / 글자끼리 겹침.
    못 잡는 것: 색 대비, 의미가 통하는지, 움직임의 자연스러움.
    그건 여전히 눈으로 봐야 한다.
    """
    problems: list[str] = []
    boxed = []

    for mob in scene.mobjects:
        box = _box(mob)
        if box is None:
            continue
        left, right, bottom, top = box
        if getattr(mob, "get_fill_opacity", None) and not mob.get_all_points().size:
            continue
        boxed.append((mob, box))

        if right > FRAME_HALF_W + 1e-3 or left < -FRAME_HALF_W - 1e-3:
            problems.append(
                f"{_describe(mob)} 화면 좌우 밖 "
                f"(x {left:.2f}~{right:.2f}, 한계 ±{FRAME_HALF_W:.2f})")
        elif top > FRAME_HALF_H + 1e-3 or bottom < -FRAME_HALF_H - 1e-3:
            problems.append(
                f"{_describe(mob)} 화면 상하 밖 "
                f"(y {bottom:.2f}~{top:.2f}, 한계 ±{FRAME_HALF_H:.2f})")
        elif _is_textlike(mob) and (
            right > SAFE_HALF_W or left < -SAFE_HALF_W
            or top > SAFE_HALF_H or bottom < -SAFE_HALF_H
        ):
            problems.append(
                f"{_describe(mob)} title-safe 밖 "
                f"(x {left:.2f}~{right:.2f}, y {bottom:.2f}~{top:.2f}, "
                f"안전 ±{SAFE_HALF_W:.2f}/±{SAFE_HALF_H:.2f})")

    texts = [(m, b) for m, b in boxed if _is_textlike(m)]
    for i, (mob_a, box_a) in enumerate(texts):
        for mob_b, box_b in texts[i + 1:]:
            overlap_w = min(box_a[1], box_b[1]) - max(box_a[0], box_b[0])
            overlap_h = min(box_a[3], box_b[3]) - max(box_a[2], box_b[2])
            if overlap_w > 0.02 and overlap_h > 0.02:
                problems.append(
                    f"{_describe(mob_a)} ↔ {_describe(mob_b)} 글자 겹침 "
                    f"({overlap_w:.2f}×{overlap_h:.2f})")

    for problem in problems:
        print(f"[layout] {label} {problem}", file=sys.stderr)
    return problems


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
