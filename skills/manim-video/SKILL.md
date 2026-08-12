---
name: manim-video
description: Manim으로 3Blue1Brown 스타일 수학 애니메이션 영상을 기획·코딩·프리뷰·렌더링한다. 수학 개념 시각화, 수식 변형 애니메이션, 그래프/벡터장/3D 궤적, 미분방정식·카오스 시뮬레이션 영상을 만들 때 사용. "수학 영상 만들어줘", "manim", "매님", "3Blue1Brown 스타일", "수식 애니메이션", "개념 시각화 영상", "로렌츠 끌개", "그래프 애니메이션" 같은 요청에 트리거.
---

# Manim 수학 영상 제작

수학 개념 하나를 **움직이는 그림 한 편**으로 바꾼다. 원본 방법론은
3Blue1Brown(Grant Sanderson)의 실제 제작 워크플로우다 —
`docs/source-video-analysis.md` 참조.

기본 엔진은 **Manim Community Edition (CE)**. ManimGL 요청 시에만
`references/manimgl.md`로 전환한다.

---

## 0. 시작 전 반드시 확인

```bash
python3 skills/manim-video/scripts/mv.py check
```

이 명령이 실패하면 **코드를 쓰기 전에** 환경부터 고친다.
`scripts/setup_manim.sh`가 설치를 처리한다 (manim CE, LaTeX, ffmpeg, 한글 폰트).

LaTeX가 없는 환경이면 `MathTex`/`Tex`는 전부 실패한다. 그 경우
사용자에게 알리고 `Text` + 유니코드 수학기호로 대체할지 확인받는다.
조용히 대체하지 않는다.

---

## 1. 파이프라인 (순서를 지킨다)

```
① 기획      주제 → 한 문장 핵심 → 비트시트(beat sheet)
② 씬 분할   비트 → Scene 클래스 (1 Scene = 1 아이디어 = 20~60초)
③ 코딩      템플릿에서 시작 → 씬 하나씩
④ 프리뷰    저해상도 스틸/영상으로 눈으로 확인 → 수정 (루프)
⑤ 최종      1080p 또는 4K 렌더 → 편집 툴로 인계
```

**한 번에 전체 영상을 렌더하지 않는다.** 원본 워크플로우의 핵심은
`checkpoint_paste` — 상태를 캐싱해 짧은 구간만 반복 확인하는 것이다.
Claude Code에서의 등가물은 **④ 프리뷰 루프**(아래 4절)다. 이 루프를
건너뛰고 만든 애니메이션은 거의 항상 타이밍이 틀린다.

---

## 2. 기획 — 비트시트

코드보다 먼저 쓴다. 상세 포맷은 `math-storyboard` 스킬을 쓰고,
간단한 건 여기서 바로 처리한다.

최소 형태:

| # | 비트(무엇을 보여주나) | 화면 | 길이 | 내레이션 |
|---|---|---|---|---|
| 1 | 문제 제기 | 수식 등장 | 8s | "…" |
| 2 | 직관 | 그래프 위 점 이동 | 20s | "…" |
| 3 | 일반화 | 수식 변형 | 15s | "…" |

규칙:
- **한 비트 = 시청자가 얻어가는 사실 하나.** 두 개면 쪼갠다.
- 내레이션 먼저 쓰고 화면을 붙인다. 반대로 하면 예쁘지만 안 팔리는
  애니메이션이 나온다.
- 총 길이는 비트 길이 합. 3~10분이 스위트스팟.

---

## 3. 코딩 규칙 (하드 룰)

템플릿에서 시작한다. `templates/` 안에:

| 파일 | 쓸 때 |
|---|---|
| `scene_base.py` | 모든 씬의 출발점. 색상 팔레트·헬퍼 포함 |
| `formula_walkthrough.py` | 수식을 항별로 색칠·강조·변형 |
| `graph_plot.py` | 함수 그래프, 접선, 리만합, 파라미터 슬라이더 |
| `ode_trajectory.py` | 로렌츠 끌개 등 ODE 수치해 3D 궤적 |
| `transform_anagram.py` | 수식 A → 수식 B 문자 단위 이동 |
| `vector_field.py` | 벡터장, 흐름선, 선형변환 |

### 지켜야 할 것

1. **좌표는 반드시 `axes.c2p(...)`를 거친다.**
   수학 좌표를 화면 좌표로 직접 계산하거나 하드코딩하지 않는다.
   축 범위를 바꾸는 순간 전부 깨진다.
   ```python
   dot.move_to(axes.c2p(x, y))          # O
   dot.move_to([x * 0.5, y * 0.5, 0])   # X
   ```

2. **색은 의미에 고정한다.** 변수 하나 = 색 하나. 그 변수가 수식에
   나오든 그래프에 나오든 라벨에 나오든 **같은 색**이다.
   `scene_base.py`의 `PALETTE` dict를 쓴다.
   ```python
   PALETTE = {"x": BLUE_B, "y": YELLOW, "z": RED_C, "accent": TEAL_A}
   ```
   색 3~4개를 넘기면 시청자가 추적을 포기한다.

3. **`rate_func`를 의식적으로 고른다.** 기본값 `smooth`는
   "무언가 등장/변형"에 맞고, 물리적 이동·시간 흐름은 `linear`여야
   한다. 시간이 흐르는 궤적에 `smooth`를 쓰면 끝에서 부자연스럽게
   느려진다.
   ```python
   self.play(Create(curve), rate_func=linear, run_time=10)
   ```

4. **`run_time`은 내레이션 길이에서 역산한다.** 비트시트에 8초라고
   썼으면 그 비트의 `self.play` + `self.wait` 합이 8초여야 한다.

5. **씬은 짧게 자른다.** 한 `Scene` 클래스가 60초를 넘으면 프리뷰
   루프가 느려져서 반복 수정이 불가능해진다. 쪼갠 뒤 편집에서 붙인다.

6. **점 개수가 2000을 넘으면 `set_points_smoothly` 대신
   `set_points_as_corners`를 쓴다.** 스플라인 피팅이 O(n) 이상으로
   느려지고, 촘촘한 점에서는 육안 차이가 없다.

7. **하드코딩된 `wait(1)` 남발 금지.** 모든 `wait`는 내레이션에서
   나온 숫자여야 한다.

### 자주 쓰는 API는 참조 파일로

전체 API 치트시트: `references/manim-ce-cookbook.md`
(mobject / 애니메이션 / 업데이터 / 카메라 / 3D / LaTeX 색인)

---

## 4. 프리뷰 루프 ← 가장 중요

수정 → 확인 사이클을 **초 단위**로 유지한다.

```bash
# 마지막 프레임만 PNG로 (가장 빠름, 구도 확인용)
python3 skills/manim-video/scripts/mv.py still scenes/lorenz.py LorenzAttractor

# 특정 애니메이션 구간만 (n번째 play부터 m번째까지)
python3 skills/manim-video/scripts/mv.py still scenes/lorenz.py LorenzAttractor -n 3,5

# 저해상도 동영상 (480p15) — 타이밍 확인용
python3 skills/manim-video/scripts/mv.py preview scenes/lorenz.py LorenzAttractor
```

**`still`로 나온 PNG는 Read 툴로 직접 열어서 본다.** 이게
`checkpoint_paste`의 대체물이다. 구도가 잘렸는지, 라벨이 겹쳤는지,
색이 배경과 붙는지는 코드만 봐서는 절대 모른다.

루프:
```
still → Read(png) → 구도 문제 발견 → 코드 수정 → still → Read …
구도 OK → preview(mp4) → 타이밍 문제 → run_time 수정 → preview …
타이밍 OK → 다음 씬
```

씬 하나가 통과하기 전에 다음 씬으로 넘어가지 않는다.

---

## 5. 최종 렌더

```bash
# 1080p60
python3 skills/manim-video/scripts/mv.py final scenes/lorenz.py LorenzAttractor

# 4K60
python3 skills/manim-video/scripts/mv.py final scenes/lorenz.py LorenzAttractor --4k

# 투명 배경 (편집 툴에서 오버레이용, .mov)
python3 skills/manim-video/scripts/mv.py final scenes/lorenz.py LorenzAttractor --transparent
```

출력은 `media/videos/<파일명>/<해상도>/<Scene>.mp4`.

렌더가 끝나면 사용자에게 **파일 경로와 길이**를 알려준다. 최종
편집(내레이션 녹음, 컷 편집, BGM)은 Final Cut / Premiere / DaVinci
쪽 작업이며 Manim의 역할은 여기까지다.

4K 렌더는 씬당 수 분~수십 분 걸린다. 반드시 프리뷰가 통과한 뒤에만
돌린다.

---

## 6. 한국어 자막·라벨

`Text`는 한글 폰트를 지정해야 한다. `MathTex`/`Tex`는 기본
LaTeX 템플릿에서 한글이 깨진다.

```python
Text("초기 조건의 미세한 차이", font="NanumGothic", font_size=36)
```

- **한글 문장 → `Text` 또는 `MarkupText`** (폰트 지정 필수)
- **수식 → `MathTex`** (영문/기호만)
- 한글과 수식을 한 줄에 섞을 땐 `VGroup`으로 나란히 배치한다.
  `Tex`에 한글을 넣지 않는다.

폰트 설치·대체 폰트·`t2c` 부분 색칠은 `references/typography-korean.md`.

---

## 7. 참조 파일 색인

| 파일 | 내용 |
|---|---|
| `references/manim-ce-cookbook.md` | CE API 치트시트 — mobject, 애니메이션, 업데이터, 카메라, 3D, LaTeX |
| `references/3b1b-style.md` | 3Blue1Brown 연출 문법 — 색·타이밍·카메라·구도의 실제 규칙 |
| `references/typography-korean.md` | 한글 폰트, `Text` vs `MathTex`, 자막 레이아웃 |
| `references/manimgl.md` | ManimGL(3b1b 원본) 전환 — `embed()`, `checkpoint_paste`, CE와의 API 차이 |
| `references/troubleshooting.md` | LaTeX 에러, 폰트 깨짐, 렌더 실패, 성능 문제 |
| `docs/source-video-analysis.md` | 원본 영상 분석 (레포 루트) |
