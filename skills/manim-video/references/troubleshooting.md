# 트러블슈팅

증상 → 원인 → 해법. 위에서부터 흔한 순서.

---

## LaTeX

### `LaTeX Error: File 'standalone.cls' not found`
LaTeX 배포판이 최소 설치(`texlive-base`)다. Manim은
`standalone`, `preview`, `amsmath`, `dvisvgm`이 필요하다.

```bash
sudo apt-get install -y texlive texlive-latex-extra texlive-fonts-extra \
    texlive-latex-recommended texlive-science dvisvgm
```
macOS: `brew install --cask mactex-no-gui` (BasicTeX는 부족한 경우가 많다)

### `latex failed but did not produce a log file`
`latex` 실행 파일 자체가 PATH에 없다. `which latex dvisvgm`으로 확인.

### 컴파일은 되는데 수식이 안 보임
`dvisvgm`이 없어서 dvi→svg 변환이 실패. 위 패키지에 포함.

### LaTeX 없이 가야 하는 환경
`MathTex`/`Tex`를 전부 `Text`로 바꾸고 유니코드 수학기호를 쓴다.
`∫ ∑ √ π ∞ ≈ ≤ ≥ → ∂ Δ θ σ ρ β α λ μ ω`
품질이 확실히 떨어지므로 **사용자에게 먼저 알리고 동의를 받는다.**

---

## 폰트 / 한글

### 한글이 네모(□□□)로 나옴
한글 폰트가 없거나 이름이 틀렸다. Manim은 **에러를 내지 않고**
그냥 tofu를 그린다.

```bash
fc-list :lang=ko family | sort -u        # 설치된 한글 폰트 확인
sudo apt-get install -y fonts-nanum fonts-noto-cjk && fc-cache -fv
```
```python
from manim import Text; print(Text.font_list())
```
폰트 이름은 파일명(`NanumGothic.ttf`)이 아니라 패밀리명(`NanumGothic`).

### 폰트를 지정했는데도 다른 폰트로 나옴
패밀리명 오타. Pango는 못 찾으면 조용히 기본 폰트로 폴백한다.
`fc-match "이름"`으로 실제 매칭 결과를 확인.

---

## 렌더

### `ffmpeg not found`
```bash
sudo apt-get install -y ffmpeg     # 또는  brew install ffmpeg
```

### 출력 파일이 안 생김 / 어디 있는지 모름
```
media/videos/<스크립트파일명>/<해상도>/<SceneName>.mp4
media/images/<스크립트파일명>/<SceneName>.png     # -s 로 스틸
```
`manim --media_dir out/` 로 바꿀 수 있다.

### 렌더는 끝났는데 영상이 검다
- 객체를 `self.add()`나 `self.play()` 없이 만들기만 했다
- 객체가 화면 밖에 있다 → `mv.py still`로 확인
- 색이 배경과 같다 (검정 배경에 검정 선)
- 3D에서 카메라가 물체 안쪽/뒤쪽을 보고 있다

### 3D 씬에서 객체가 안 보임
`z_range`와 실제 데이터 범위가 안 맞는다. 로렌츠는 z가 0~50인데
기본 `ThreeDAxes`의 z_range는 [-3,3]이다. 축 범위를 데이터에
맞추고 `c2p`를 쓴다.

### 캐시 때문에 수정이 반영 안 됨
```bash
manim --disable_caching scene.py MyScene
rm -rf media/  # 최후의 수단
```

---

## 성능

### 렌더가 너무 느림
| 원인 | 해법 |
|---|---|
| 점 수천 개에 `set_points_smoothly` | `set_points_as_corners` |
| `always_redraw`로 무거운 객체 재생성 | `add_updater`로 좌표만 갱신 |
| 씬이 너무 김 | 20~60초로 분할 |
| 반복 확인을 `-qh`로 함 | 프리뷰는 `-ql`, 최종만 `-qh`/`-qk` |
| `Surface` resolution 과다 | 프리뷰는 `(16,16)`, 최종만 `(48,48)` |

### 메모리 부족 / 프로세스 죽음
4K 긴 씬은 GB 단위로 먹는다. 씬을 쪼개고 편집에서 붙인다.

---

## 애니메이션이 이상함

### `Transform` 후 객체를 못 없앰
```python
self.play(Transform(a, b))       # 화면에 남는 건 a (모양만 b)
self.play(FadeOut(b))            # ✗ b는 화면에 없음
self.play(FadeOut(a))            # ✓
```
헷갈리면 `ReplacementTransform(a, b)` 쓰고 이후엔 `b`를 참조한다.

### 궤적이 끝에서 느려짐
`rate_func`가 기본 `smooth`다. 시간 흐름에는 `linear`.

### 업데이터가 애니메이션 끝나고도 계속 돎
```python
mob.clear_updaters()
# 또는
mob.remove_updater(fn)
```
안 지우면 다음 `play`에서 예상 못 한 움직임이 생긴다.

### `MathTex` 인덱싱이 엉뚱한 글자를 가리킴
LaTeX 조판 결과의 글리프 순서는 소스 순서와 다를 수 있다.
```python
self.add(index_labels(eq[0]))
```
를 넣고 `mv.py still`로 번호를 눈으로 확인한 뒤 인덱스를 쓴다.

### `TransformMatchingTex`가 아무 매칭도 못 함
`MathTex(r"a+b")`처럼 통짜 문자열이면 매칭할 항이 없다.
`MathTex("a", "+", "b")`로 나눠 만든다.

---

## 환경 점검

막히면 먼저:
```bash
python3 skills/manim-video/scripts/mv.py check
```
manim / ffmpeg / latex / dvisvgm / 한글 폰트를 한 번에 확인하고
빠진 것의 설치 명령을 출력한다.
