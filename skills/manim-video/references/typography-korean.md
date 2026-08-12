# 한글 타이포그래피

Manim에서 한글이 깨지는 이유는 두 갈래이고, 해법이 서로 다르다.

---

## 1. 두 개의 텍스트 엔진

| | `Text` / `MarkupText` | `Tex` / `MathTex` |
|---|---|---|
| 렌더 엔진 | Pango (시스템 폰트) | LaTeX |
| 한글 | **폰트만 있으면 됨** | 기본 템플릿에서 깨짐 |
| 수식 | 불가 (유니코드 기호로 흉내만) | 완전 지원 |
| 속도 | 빠름 | 느림 (LaTeX 컴파일) |

### 원칙

- **한글 문장 → `Text`** (폰트 지정 필수)
- **수식 → `MathTex`** (영문·기호만)
- 둘을 한 줄에 → `VGroup(...).arrange(RIGHT)` 로 나란히

```python
row = VGroup(
    Text("넓이는 ", font=KR_FONT, font_size=36),
    MathTex(r"\pi r^2", font_size=44),
    Text(" 입니다", font=KR_FONT, font_size=36),
).arrange(RIGHT, buff=0.15)
```

`MathTex`와 `Text`는 기준선이 달라서 `arrange(RIGHT)`만으로는
미묘하게 어긋난다. 정밀하게 맞추려면:
```python
row.arrange(RIGHT, buff=0.15, aligned_edge=DOWN)
```

---

## 2. 폰트 지정

```python
KR_FONT = "NanumGothic"      # 또는 "Noto Sans KR", "Pretendard"

Text("초기 조건의 미세한 차이", font=KR_FONT, font_size=36)
```

폰트 이름은 **설치된 패밀리 이름**이어야 한다. 파일명이 아니다.
확인:

```python
from manim import Text
print(Text.font_list())          # 사용 가능한 폰트 전체
```
또는
```bash
fc-list :lang=ko family | sort -u
```

### 설치

```bash
# Debian/Ubuntu
sudo apt-get install -y fonts-nanum fonts-noto-cjk && fc-cache -fv

# macOS
brew install --cask font-nanum-gothic
```

`scripts/setup_manim.sh`가 이걸 처리한다.

### 폴백

폰트가 없으면 Manim은 에러 없이 **네모(tofu)로 렌더한다**. 조용히
망가지므로 `mv.py check`가 한글 렌더 테스트를 포함한다. 반드시
스틸 렌더로 눈으로 확인한다.

---

## 3. 부분 색칠

`Text`는 `t2c`(text to color):

```python
Text(
    "x는 파랑, y는 노랑",
    font=KR_FONT,
    t2c={"x": BLUE_B, "y": YELLOW},
)
```

인덱스 범위로도 된다 (한글은 글자 단위):
```python
Text("초기조건이 중요하다", font=KR_FONT, t2c={"[0:4]": TEAL_A})
```

`MarkupText`는 Pango 마크업:
```python
MarkupText(
    '<span foreground="#58C4DD">파란</span> 글씨와 <b>굵은</b> 글씨',
    font=KR_FONT,
)
```

기타: `t2w`(weight), `t2s`(slant), `t2f`(font).

---

## 4. 자막 레이아웃

내레이션 자막을 화면에 깔 때:

```python
def subtitle(txt):
    return Text(txt, font=KR_FONT, font_size=30, color=GREY_A).to_edge(DOWN, buff=0.4)

sub = subtitle("여기서 발산이 시작됩니다")
self.play(FadeIn(sub, shift=UP * 0.2))
self.wait(2)
self.play(FadeOut(sub))
```

- 한 줄 최대 25자. 넘으면 `line_spacing`을 주고 두 줄로.
- `font_size=28~32`가 1080p에서 적당. 4K에서도 상대 크기라 그대로.
- 자막은 **내레이션 전문이 아니라 핵심 구절**만. 전문을 깔면
  시청자가 읽느라 화면을 안 본다.

```python
Text("긴 문장을\n두 줄로", font=KR_FONT, line_spacing=0.8)
```

---

## 5. 한글을 LaTeX에 꼭 넣어야 한다면

권장하지 않는다. 굳이 하면 `kotex`가 깔린 LaTeX 배포판 +
XeLaTeX 커스텀 템플릿이 필요하다:

```python
kr_template = TexTemplate(
    tex_compiler="xelatex",
    output_format=".xdv",
    preamble=r"""
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{kotex}
""",
)
Tex(r"넓이 $= \pi r^2$", tex_template=kr_template)
```

TeX Live full + `texlive-lang-korean` 설치가 필요하고 컴파일이
느리다. `Text` + `MathTex` 조합이 거의 항상 낫다.

---

## 6. 영어 버전으로 낼 때

같은 씬을 ko/en 두 벌로 뽑는 구조:

```python
LANG = os.environ.get("MV_LANG", "ko")

STRINGS = {
    "ko": {"title": "카오스란 무엇인가", "hint": "초기값에 민감하다"},
    "en": {"title": "What is chaos?",   "hint": "Sensitive to initial conditions"},
}
S = STRINGS[LANG]

def label(key, **kw):
    if LANG == "ko":
        return Text(S[key], font=KR_FONT, **kw)
    return Text(S[key], **kw)
```

```bash
MV_LANG=en manim -qh scene.py MyScene
```

문자열을 씬 코드 안에 흩뿌리지 말고 `STRINGS` dict 한 곳에 모은다.
