# ManimGL (3Blue1Brown 원본) 전환 가이드

기본은 CE다. 아래 경우에만 ManimGL로 간다:

- 사용자가 명시적으로 ManimGL / 3b1b 원본 라이브러리를 요구
- 원본 영상의 `embed()` 인터랙티브 워크플로우를 그대로 재현해야 함
- 3b1b 공식 저장소(`3b1b/videos`)의 씬 코드를 그대로 돌려야 함

**CE 코드는 ManimGL에서 그대로 돌지 않는다.** 호환 레이어가 없다.

---

## 1. 설치

```bash
pip install manimgl
# 시스템 의존: ffmpeg, LaTeX(TeX Live), OpenGL
```

Linux 헤드리스 환경에서는 OpenGL 컨텍스트가 없어서 실행이
안 되는 경우가 많다. `xvfb-run`으로 우회:
```bash
xvfb-run -a manimgl scene.py MyScene
```
그래도 실패하면 CE로 돌아가는 게 빠르다. 이 판단을 사용자에게
알린다.

---

## 2. 실행

```bash
manimgl scene.py MyScene          # 창을 띄우고 인터랙티브
manimgl scene.py MyScene -w       # 파일로 씀
manimgl scene.py MyScene -o       # 쓰고 열기
manimgl scene.py MyScene -s       # 마지막 프레임만
manimgl scene.py MyScene --hd     # 1080p
manimgl scene.py MyScene --uhd    # 4K
```

CE의 `-pql` 같은 품질 플래그 체계가 다르다.

---

## 3. 핵심 차이표

| 개념 | CE | ManimGL |
|---|---|---|
| import | `from manim import *` | `from manimlib import *` |
| 그리기 | `Create` | `ShowCreation` |
| 좌표 | `axes.c2p` | `axes.c2p` (동일) |
| 카메라 | `self.set_camera_orientation(phi=, theta=)` | `self.frame.reorient(θ, φ, γ)` |
| 카메라 객체 | `self.camera.frame` (MovingCameraScene) | `self.frame` (모든 씬) |
| 3D 씬 | `ThreeDScene` | `Scene` 그대로 (frame으로 제어) |
| 수식 | `MathTex` | `Tex` |
| 텍스트 수식 | `Tex` | `TexText` |
| 인터랙티브 | 없음 | `self.embed()` |
| 항상 갱신 | `always_redraw(f)` | `always(f, ...)`, `f_always(...)` |
| 색 상수 | 대체로 동일 | 대체로 동일 |

### 카메라 (가장 큰 차이)

```python
# CE
self.set_camera_orientation(phi=70 * DEGREES, theta=-45 * DEGREES)
self.begin_ambient_camera_rotation(rate=0.05)

# ManimGL
frame = self.frame
frame.reorient(-45, 70, 0)                       # theta, phi, gamma (도 단위)
frame.add_updater(lambda m, dt: m.increment_theta(0.05 * dt))
```

`reorient`는 **도(degree) 단위 정수**를 받는다. CE처럼 `* DEGREES`를
곱하면 안 된다.

---

## 4. `embed()` — 영상에 나온 인터랙티브 워크플로우

```python
class MyScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(ShowCreation(circle))
        self.embed()          # ← 여기서 IPython 셸이 열린다
```

`manimgl scene.py MyScene`을 실행하면 이 지점에서 씬 상태가
살아있는 채로 IPython 프롬프트가 뜬다. 거기서:

```
>>> self.play(circle.animate.shift(RIGHT))
>>> circle.set_color(YELLOW)
>>> touch()          # 파일 다시 읽기
```

창을 보면서 실시간으로 실험한다. 이게 CE에 없는 ManimGL의
존재 이유다.

### checkpoint_paste

Grant의 Sublime Text 매크로. 에디터에서 코드 블록을 선택하고
단축키를 누르면:

1. 선택 블록의 첫 줄이 주석(`# 뭔가`)이면 그 주석을 키로 **씬
   상태를 체크포인트에 저장/복원**
2. 블록을 `embed()` 셸에 붙여넣어 실행

즉 같은 블록을 반복 수정하며 누를 때마다, 그 블록 **직전 상태**로
되돌린 뒤 새 코드를 돌린다. 30초짜리 씬의 마지막 3초만 고칠 때
30초를 다시 렌더하지 않아도 되는 이유.

구현은 `manimlib.utils.` 쪽 `checkpoint_paste`와 에디터
플러그인(3b1b가 공개한 Sublime 설정)의 조합이다. 에디터 매크로가
필요하므로 **Claude Code에서는 그대로 쓸 수 없다.**

> Claude Code에서의 등가물은 메인 SKILL.md §4 "프리뷰 루프" —
> 씬 분할 + `-n` 구간 스틸 렌더 + PNG를 Read로 직접 확인.

---

## 5. CE → GL 포팅 체크리스트

```
□ import 교체:  manim → manimlib
□ Create        → ShowCreation
□ MathTex       → Tex
□ Tex           → TexText
□ ThreeDScene   → Scene + self.frame
□ set_camera_orientation(phi=a*DEGREES, theta=b*DEGREES)
                → self.frame.reorient(b, a, 0)     # 도 단위 정수
□ always_redraw(f)  → always(mob.method, arg) 또는 f_always
□ config.xxx    → CONFIG dict 또는 CLI 플래그
□ get_riemann_rectangles 등 CE 전용 헬퍼 → 직접 구현 필요
```

포팅이 30분 넘게 걸릴 것 같으면 사용자에게 CE 유지를 제안한다.
