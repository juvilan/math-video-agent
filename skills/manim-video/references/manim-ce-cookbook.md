# Manim CE 쿡북

Manim Community Edition v0.18~v0.19 기준. 필요한 절만 읽는다.

```python
from manim import *
```

---

## 1. 씬의 뼈대

```python
class MyScene(Scene):
    def construct(self):
        circle = Circle(radius=1.5, color=BLUE)
        self.play(Create(circle))      # 그리기
        self.wait(1)
        self.play(FadeOut(circle))
```

| 클래스 | 쓸 때 |
|---|---|
| `Scene` | 2D 기본 |
| `ThreeDScene` | 3D. 카메라 방위각 제어 |
| `MovingCameraScene` | 2D인데 카메라를 줌/팬 |
| `ZoomedScene` | 확대 인셋 화면 |

`ThreeDScene`과 `MovingCameraScene`을 동시에 쓰려면
`class S(ThreeDScene, MovingCameraScene)` — 단 `self.camera.frame`은
`ThreeDScene`에서 동작이 다르니 3D는 `set_camera_orientation` 쪽을 쓴다.

---

## 2. Mobject

### 도형
```python
Circle(radius=1, color=BLUE, fill_opacity=0.3)
Square(side_length=2)
Rectangle(width=4, height=2)
Line(start=LEFT, end=RIGHT)
Arrow(ORIGIN, RIGHT * 2, buff=0)
Dot(point=ORIGIN, radius=0.08, color=YELLOW)
Dot3D(point=ORIGIN, radius=0.05)     # 3D 씬에서 구체
Polygon(*points)
Arc(radius=1, start_angle=0, angle=PI/2)
```

### 텍스트 / 수식
```python
Text("한글은 여기", font="NanumGothic", font_size=36)
MarkupText('<span foreground="red">색</span>있는 텍스트')
MathTex(r"\frac{d}{dx} e^x = e^x")          # 수학 모드
Tex(r"영문 문장과 $x^2$ 혼용")               # 텍스트 모드
```

### 좌표계
```python
axes = Axes(
    x_range=[-3, 3, 1],          # [최소, 최대, 눈금간격]
    y_range=[-2, 2, 1],
    x_length=10, y_length=6,
    axis_config={"include_numbers": True},
)
axes.c2p(1.5, 0.8)               # 수학 좌표 → 화면 좌표 ★필수★
axes.p2c(some_point)             # 역변환
axes.get_axis_labels(x_label="x", y_label="f(x)")

NumberPlane()                     # 격자
ThreeDAxes(x_range=[-5,5,1], y_range=[-5,5,1], z_range=[0,5,1])
```

**`c2p`를 거치지 않은 좌표는 축 범위를 바꾸는 순간 전부 어긋난다.**

### 그룹
```python
group = VGroup(a, b, c)
group.arrange(DOWN, buff=0.4)          # 세로로 정렬
group.arrange_in_grid(rows=2, buff=0.3)
group[0]                                # 인덱싱 가능
```

---

## 3. 배치

```python
mob.move_to(ORIGIN)
mob.shift(UP * 2 + RIGHT)
mob.next_to(other, RIGHT, buff=0.5)
mob.to_edge(UP, buff=0.5)
mob.to_corner(UL)
mob.align_to(other, LEFT)
mob.scale(1.5)
mob.rotate(PI / 4)

# 방향 상수: UP DOWN LEFT RIGHT IN OUT ORIGIN UL UR DL DR
```

화면은 기본 8×14.22 유닛 (세로 8, 가로 14.22). `to_edge`로 붙이면
`buff` 기본 0.5만큼 여백이 남는다.

---

## 4. 애니메이션

```python
self.play(Create(mob))              # 선을 그려나감
self.play(Write(text))              # 글씨 쓰듯
self.play(FadeIn(mob, shift=UP))
self.play(FadeOut(mob))
self.play(Transform(a, b))          # a를 b 모양으로 (a 객체가 남음)
self.play(ReplacementTransform(a, b))  # a를 b로 교체 (b 객체가 남음)
self.play(GrowFromCenter(mob))
self.play(DrawBorderThenFill(mob))
self.play(Indicate(mob))            # 강조 펄스
self.play(Circumscribe(mob))        # 테두리 훑기
self.play(Flash(point))
self.play(Wiggle(mob))
```

`Transform` vs `ReplacementTransform`: 이후에 참조할 변수가
`a`면 `Transform`, `b`면 `ReplacementTransform`. 섞으면 나중에
`FadeOut(b)`이 아무것도 안 하는 버그가 난다.

### 속성 애니메이션
```python
self.play(mob.animate.shift(RIGHT * 2).set_color(RED))
self.play(mob.animate(rate_func=linear).rotate(PI))
```

### 동시 / 순차
```python
self.play(Create(a), Write(b))                  # 동시
self.play(AnimationGroup(x, y, lag_ratio=0.2))  # 살짝 어긋나게
self.play(LaggedStart(*anims, lag_ratio=0.1))   # 줄줄이
self.play(Succession(x, y))                     # 완전 순차
```

### 타이밍
```python
self.play(Create(c), run_time=3, rate_func=linear)
self.wait(2)
```

| rate_func | 언제 |
|---|---|
| `smooth` (기본) | 등장·퇴장·형태 변형 |
| `linear` | **시간이 흐르는 궤적, 회전, 스캔** |
| `rush_into` / `rush_from` | 앞/뒤에 다른 동작이 이어질 때 |
| `there_and_back` | 강조하고 원복 |
| `ease_in_out_sine` | 부드러운 왕복 |
| `wiggle` | 흔들기 |

---

## 5. 업데이터 (매 프레임 갱신)

```python
# ValueTracker: 애니메이션할 수 있는 숫자
t = ValueTracker(0)

dot = always_redraw(lambda: Dot(axes.c2p(t.get_value(), f(t.get_value()))))
self.add(dot)
self.play(t.animate.set_value(3), run_time=4, rate_func=linear)
```

```python
# add_updater: 객체가 다른 객체를 따라감
label.add_updater(lambda m: m.next_to(dot, UP, buff=0.2))
self.add(label)
...
label.clear_updaters()      # 끝나면 반드시 제거
```

`always_redraw`는 매 프레임 객체를 새로 만든다. 무거운 객체
(수천 점 곡선)에는 쓰지 말고 `add_updater`로 좌표만 갱신한다.

### 잔상 꼬리
```python
trail = TracedPath(
    dot.get_center,
    stroke_width=3,
    stroke_color=YELLOW,
    dissipating_time=0.6,     # 이 시간 뒤 사라짐. None이면 영구
)
self.add(trail)
```

---

## 6. 그래프 / 함수

```python
axes = Axes(x_range=[-3, 3], y_range=[-1, 5])
graph = axes.plot(lambda x: x**2, color=BLUE, x_range=[-2.2, 2.2])
label = axes.get_graph_label(graph, MathTex("x^2"), x_val=2, direction=UR)

# 특정 점
point = axes.input_to_graph_point(1.5, graph)

# 접선
tangent = TangentLine(graph, alpha=0.6, length=4, color=YELLOW)

# 리만합
rects = axes.get_riemann_rectangles(graph, x_range=[0, 2], dx=0.2)

# 면적
area = axes.get_area(graph, x_range=[0, 2], color=BLUE, opacity=0.4)

# 곡선 따라 이동
self.play(MoveAlongPath(dot, graph), run_time=4, rate_func=linear)
```

### 임의 점 배열로 곡선 만들기
```python
curve = VMobject()
curve.set_points_smoothly([axes.c2p(*p) for p in points])   # 점 2000개 이하
curve.set_points_as_corners([axes.c2p(*p) for p in points]) # 그 이상
curve.set_stroke(color=BLUE, width=2)
```

---

## 7. 3D

```python
class S(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        self.set_camera_orientation(phi=70 * DEGREES, theta=-45 * DEGREES, zoom=0.8)

        self.begin_ambient_camera_rotation(rate=0.06)   # rad/s, 천천히
        self.wait(10)
        self.stop_ambient_camera_rotation()

        self.move_camera(phi=40 * DEGREES, theta=30 * DEGREES, run_time=3)
```

- `phi`: z축에서 기울인 각 (0이면 위에서 내려다봄, 90°면 옆에서)
- `theta`: 수평 회전각
- `zoom`: 1보다 작으면 넓게

3D에서 텍스트가 같이 회전하는 게 싫으면:
```python
self.add_fixed_in_frame_mobjects(title)     # 화면에 고정
self.add_fixed_orientation_mobjects(label)  # 위치는 따라가되 항상 정면
```

3D 표면:
```python
surface = Surface(
    lambda u, v: axes.c2p(u, v, u**2 - v**2),
    u_range=[-2, 2], v_range=[-2, 2],
    resolution=(24, 24),
)
```

---

## 8. LaTeX 다루기

### 항 분리
```python
eq = MathTex(r"\frac{dx}{dt}", "=", r"\sigma", "(", "y", "-", "x", ")")
eq[4].set_color(YELLOW)     # y만 노랑
```
인자를 나눠 넘기면 각 인자가 서브모브젝트가 된다. 인덱스로 접근.

### 문자열로 색칠
```python
eq = MathTex(r"x^2 + y^2 = r^2")
eq.set_color_by_tex("x", BLUE)      # "x"를 포함한 부분식 전체
```
`set_color_by_tex`는 부분 문자열 매칭이라 오작동하기 쉽다.
정확히 하려면 위처럼 인자를 나눠라.

### 개별 글자
```python
eq = MathTex(r"a + b = c")
eq[0][0]     # 'a'
eq[0][2]     # '+'
```
`MathTex` 인자가 하나면 `eq[0]`이 전체이고, 그 안이 글리프 배열이다.
글리프 인덱스는 LaTeX 조판 결과에 따라 달라지므로 **반드시
`index_labels(eq[0])`로 눈으로 확인하고 쓴다.**

```python
self.add(index_labels(eq[0]))   # 각 글리프 위에 번호 표시 → still 렌더로 확인
```

### 수식 → 수식 변형
```python
self.play(TransformMatchingTex(eq1, eq2))     # 같은 tex 문자열끼리 매칭
self.play(TransformMatchingShapes(eq1, eq2))  # 모양이 비슷한 글리프끼리
```
`TransformMatchingTex`는 `MathTex`를 항별로 나눠 만들었을 때만
제대로 동작한다.

---

## 9. 색

```python
BLUE_E BLUE_D BLUE BLUE_C BLUE_B BLUE_A     # 진함 → 연함
# 같은 패턴: TEAL GREEN YELLOW GOLD RED MAROON PURPLE GREY
WHITE BLACK GREY_BROWN LIGHT_BROWN PINK ORANGE
```

3Blue1Brown 팔레트의 뼈대는 `BLUE_D`(주), `YELLOW`(강조),
`RED_C`(대비), `GREY_B`(보조). 배경은 기본 `#000000`에 가까운
어두운 회색.

```python
config.background_color = "#0f0f14"
mob.set_color_by_gradient(BLUE, YELLOW)
```

---

## 10. CLI

```bash
manim -pql scene.py MyScene      # 480p15, 렌더 후 재생
manim -pqm scene.py MyScene      # 720p30
manim -pqh scene.py MyScene      # 1080p60
manim -qk  scene.py MyScene      # 4K60
manim -s   scene.py MyScene      # 마지막 프레임 PNG만
manim -n 3,5 scene.py MyScene    # 3~5번째 애니메이션 구간만
manim -t   scene.py MyScene      # 투명 배경 (.mov)
manim --format=gif scene.py MyScene
manim -a scene.py                # 파일 안 모든 씬
```

플래그: `-p` 재생, `-q{l,m,h,k}` 품질, `-s` 스틸, `-n` 구간,
`-t` 투명, `-a` 전체.

출력: `media/videos/<파일명>/<해상도>/<Scene>.mp4`

### 파일 내 설정
```python
config.background_color = "#0f0f14"
config.frame_rate = 60
config.pixel_width, config.pixel_height = 3840, 2160
```
