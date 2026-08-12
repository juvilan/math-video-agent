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

먼저 이 스킬의 렌더 CLI 경로를 잡는다. 아래 모든 명령이 이걸 쓴다.
`$MV`는 **이 SKILL.md가 있는 디렉터리** 기준이다.

```bash
MV="<이 스킬 디렉터리>/scripts/mv.py"     # 예: skills/manim-video/scripts/mv.py
python3 "$MV" check
```

이 명령이 실패하면 **코드를 쓰기 전에** 환경부터 고친다.
`<스킬 디렉터리>/scripts/setup_manim.sh`가 설치를 처리한다
(manim CE, LaTeX, ffmpeg, 한글 폰트).

LaTeX가 없는 환경이면 `MathTex`/`Tex`는 전부 실패한다. 그 경우
사용자에게 알리고 `Text` + 유니코드 수학기호로 대체할지 확인받는다.
조용히 대체하지 않는다.

---

## 1. 파이프라인 (순서를 지킨다)

```
① 기획      주제 → 한 문장 핵심 → 콘티        math-storyboard (사용자와 함께)
② 씬 분할   비트 → Scene 클래스 (1 Scene = 1 아이디어 = 20~60초)
③ 코딩      템플릿에서 시작 → 씬 하나씩
④ 검증      layout(텍스트) → still(이미지) → preview (루프)
⑤ 최종      1080p 또는 4K 렌더
⑥ 검수      렌더된 영상을 프레임으로 뜯어 확인  math-video-qc
```

**한 번에 전체 영상을 렌더하지 않는다.** 원본 워크플로우의 핵심은
`checkpoint_paste` — 상태를 캐싱해 짧은 구간만 반복 확인하는 것이다.
Claude Code에서의 등가물은 **④ 검증 루프**(아래 4절)다. 이 루프를
건너뛰고 만든 애니메이션은 거의 항상 타이밍이 틀린다.

④ 안에서도 순서가 있다: 좌표로 잡히는 건 `layout`(텍스트)으로,
눈으로만 알 수 있는 건 `still`(이미지)로. 비싼 걸 나중에 쓴다.

④와 ⑥은 보는 대상이 다르다. ④는 **정지 화면 하나의 구도**를,
⑥은 **완성된 영상의 흐름**을 본다. ④만으로는 죽은 시간, 자막과
화면의 불일치, 자막이 안전영역 밖으로 나간 것을 못 잡는다.

---

## 2. 기획 — 콘티

코드보다 먼저 쓴다. **`math-storyboard` 스킬로 넘긴다.**
그 스킬은 여섯 단계로 나눠 **사용자와 함께** 만든다 —
핵심 한 문장 → 대상/길이 → 비트 뼈대 → 콘티 → 내레이션 → 확정.
각 단계마다 멈추고 확인받는다.

여기서 직접 처리해도 되는 건 사용자가 이미 완성된 콘티를 들고
왔을 때뿐이다. 그 경우에도 아래는 확인한다:

- **한 비트 = 시청자가 얻어가는 사실 하나.** 두 개면 쪼갠다.
- 내레이션이 실제 문장으로 있는가. 요약만 있으면 길이를 못 잡는다.
- 비트별 목표 길이가 있는가. ⑥ 검수에서 실제와 대조한다.
- 총 길이 3~10분.

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

## 4. 검증 루프 ← 가장 중요

수정 → 확인 사이클을 **초 단위**로 유지한다.
그리고 **싼 것부터 돌린다.** 이 파이프라인에서 제일 비싼 동작은
렌더된 이미지를 Read 하는 것이다.

### 4-1. 먼저 좌표로 (이미지 없음, 반복 무료)

```bash
python3 "$MV" layout scenes/lorenz.py LorenzAttractor
```

씬을 끝까지 돌리되 이미지를 만들지 않고, 매 `play` 마다 배치를
좌표로 검사해 텍스트로 보고한다 — 화면 밖 / title-safe 이탈 /
글자 겹침 / 효과음 파일 없음.

```
배치 문제 1종:
  [play#19~play#21] MathTex('r') title-safe 밖 (x 6.28~6.47, 안전 ±6.40)
```

**여기가 깨끗해질 때까지 이미지를 보지 않는다.** 좌표로 잡을 수
있는 걸 눈으로 찾으면 같은 스틸을 몇 번씩 다시 보게 된다.
`scene_base.MathScene` 을 상속한 씬에서 동작한다.

### 4-2. 그다음 이미지로 (씬당 한 장)

```bash
# 마지막 프레임만 PNG로 (가장 빠름, 구도 확인용)
python3 "$MV" still scenes/lorenz.py LorenzAttractor

# 특정 애니메이션 구간만 (n번째 play부터 m번째까지)
python3 "$MV" still scenes/lorenz.py LorenzAttractor -n 3,5

# 저해상도 동영상 (480p15) — 타이밍 확인용
python3 "$MV" preview scenes/lorenz.py LorenzAttractor
```

**`still`로 나온 PNG는 Read 툴로 직접 열어서 본다.** 이게
`checkpoint_paste`의 대체물이다. 색이 배경과 붙는지, 그림이 의도한
모양인지, 한글이 네모로 나오는지는 좌표로는 절대 모른다.

루프:
```
layout → 텍스트 보고 전부 수정 → layout … (깨끗해질 때까지)
       → still → Read(png) → 색·모양 확인
       → preview(mp4) → 타이밍 → run_time 수정
       → 다음 씬
```

씬 하나가 통과하기 전에 다음 씬으로 넘어가지 않는다.
**같은 씬의 스틸을 세 번 넘게 보고 있으면** `layout` 으로 돌아간다.
비용 순서 전체는 `references/token-budget.md`.

---

## 5. 최종 렌더

```bash
# 1080p60
python3 "$MV" final scenes/lorenz.py LorenzAttractor

# 4K60
python3 "$MV" final scenes/lorenz.py LorenzAttractor --4k

# 투명 배경 (편집 툴에서 오버레이용, .mov)
python3 "$MV" final scenes/lorenz.py LorenzAttractor --transparent
```

출력은 `media/videos/<파일명>/<해상도>/<Scene>.mp4`.

4K 렌더는 씬당 수 분~수십 분 걸린다. 반드시 프리뷰가 통과한 뒤에만
돌린다.

**렌더가 끝났다고 완성이 아니다. ⑥ 검수로 간다.**

---

## 6. 검수 ← 렌더 뒤 반드시

④ 프리뷰 루프는 정지 화면 하나의 구도를 본다. 그걸로는 못 잡는
게 있다 — 자막이 4초 넘게 멈춰 있는 죽은 시간, 자막은 "고리로
자릅니다"인데 화면엔 아직 고리가 없는 불일치, 자막이 title-safe
경계에 걸쳐 유튜브 UI에 덮이는 것, 씬을 이어붙였을 때 구성이 튀는 것.

```bash
QC="<이 스킬 디렉터리>/scripts/qc.py"

python3 "$QC" stats  out.mp4              # 검은 화면 / 4초 이상 정지 / 규격
python3 "$QC" sheet  out.mp4 -g 4x4       # 전체 대조표 한 장 → Read 로 연다
python3 "$QC" guides out.mp4 50.0         # 안전영역 + 자막 밴드 → 자막 위치 판정
python3 "$QC" strip  out.mp4 36 41 -n 8   # 특정 구간 촘촘히 → 동작 검사
```

**출력된 PNG를 Read 툴로 실제로 연다.** 뽑아만 놓고 안 열었으면
검수한 게 아니다. 체크리스트 전문은 `references/qc-checklist.md`,
절차 전체는 `math-video-qc` 에이전트.

검수에서 고친 게 있으면 해당 씬을 다시 렌더하고 **검수를 다시**
돌린다. 고치면서 다른 걸 깨뜨렸는지는 또 봐야만 안다.

검수까지 통과하면 사용자에게 **파일 경로와 길이, 그리고 검수에서
고치지 않기로 한 것**을 함께 알려준다. 최종 편집(내레이션 녹음,
컷 편집, BGM)은 Final Cut / Premiere / DaVinci 쪽 작업이며 Manim의
역할은 여기까지다.

---

## 7. 효과음

`assets/sfx/` 에 음원을 두고:

```python
self.sfx("whoosh", gain=-12)      # play **앞에** 놓는다
self.play(Create(circle), run_time=1.5)
```

한 씬에 3개를 넘기지 않는다. 과하면 유치해진다.

**소리는 조용히 사라진다.** 함정 셋 — ① 캐시가 켜져 있으면
`add_sound` 가 아무 일도 안 한다(`mv.py` 가 자동으로 끈다),
② 씬 맨 앞에서 앞당기면 예외가 나는데 렌더는 성공으로 끝난다,
③ `ffmpeg concat -c copy` 로 이어붙이면 첫 파일에 오디오가 없을 때
뒤 소리가 전부 버려진다.

```bash
python3 "$MV" join out.mp4 Hook.mp4 Rings.mp4 Unroll.mp4 Result.mp4
python3 "$QC" stats out.mp4        # 오디오 트랙이 실제로 붙었는지
```

자세한 건 `references/audio.md`.

---

## 8. 한국어 자막·라벨

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

## 9. 참조 파일 색인

| 파일 | 내용 |
|---|---|
| `references/manim-ce-cookbook.md` | CE API 치트시트 — mobject, 애니메이션, 업데이터, 카메라, 3D, LaTeX |
| `references/3b1b-style.md` | 3Blue1Brown 연출 문법 — 색·타이밍·카메라·구도의 실제 규칙 |
| `references/qc-checklist.md` | 검수 체크리스트 — 자동 검사 임계값, 자막·안전영역, 동작, 보고 형식 |
| `references/token-budget.md` | 언제 이미지를 보고 언제 텍스트로 때우나 — 비용 순서 |
| `references/audio.md` | 효과음·음악 — `sfx()`, 조용히 실패하는 함정 셋, 음량, 저작권 |
| `references/typography-korean.md` | 한글 폰트, `Text` vs `MathTex`, 자막 레이아웃 |
| `references/manimgl.md` | ManimGL(3b1b 원본) 전환 — `embed()`, `checkpoint_paste`, CE와의 API 차이 |
| `references/troubleshooting.md` | LaTeX 에러, 폰트 깨짐, 렌더 실패, 성능 문제 |
| `docs/source-video-analysis.md` | 원본 영상 분석 (레포 루트) |
