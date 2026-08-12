# math-video-agent

Manim으로 **3Blue1Brown 스타일 수학 애니메이션 영상**을 만드는
Claude Code 플러그인.

주제 한 줄을 주면 → 비트시트 → 씬 코드 → 프리뷰 검증 → 최종 렌더까지
간다.

방법론의 출처는 3Blue1Brown(Grant Sanderson)이 자신의 실제 제작
과정을 공개한 영상
[*How I animate 3Blue1Brown — A Manim demo with Ben Sparks*](https://www.youtube.com/watch?v=rbu7Zu5X1zI)
다. 영상에서 관찰된 워크플로우를 스킬·에이전트·템플릿으로 옮긴
매핑표는 [`docs/source-video-analysis.md`](docs/source-video-analysis.md)에 있다.

아래 그림은 전부 이 레포의 템플릿을 **실제로 렌더한 결과**다
(Manim CE v0.21.0, `mv.py still`).

| | |
|---|---|
| ![로렌츠 끌개](docs/images/lorenz-attractor.png) | ![로렌츠 방정식](docs/images/lorenz-equations.png) |
| `ode_trajectory.py LorenzAttractor` | `ode_trajectory.py LorenzEquations` |
| ![접선](docs/images/tangent-slope.png) | ![리만합](docs/images/riemann-sum.png) |
| `graph_plot.py TangentSlope` | `graph_plot.py RiemannSum` |
| ![선형변환](docs/images/linear-transform.png) | ![스모크 테스트](docs/images/title-demo.png) |
| `vector_field.py LinearTransform` | `scene_base.py TitleDemo` |

---

## 구성

```
agents/
  math-video-director.md      기획→렌더 전 과정을 몰고 가는 감독 에이전트
commands/
  math-video.md               /math-video  — 주제 → 완성 영상
  storyboard.md               /storyboard  — 기획서만
  mv-render.md                /mv-render   — 기존 씬을 검증 루프에 태워 렌더
skills/
  manim-video/                메인 스킬 — 파이프라인·코딩 규칙·프리뷰 루프
    references/               CE 쿡북 / 3b1b 연출 문법 / 한글 / ManimGL / 트러블슈팅
    templates/                씬 템플릿 6종
    scripts/                  mv.py (렌더 CLI), setup_manim.sh
  math-storyboard/            기획 스킬 — 비트시트·내레이션·수식 받아쓰기
docs/
  source-video-analysis.md    원본 영상 분석 + 이 레포로의 매핑
```

---

## 설치

### 1) Manim 환경

```bash
bash skills/manim-video/scripts/setup_manim.sh
python3 skills/manim-video/scripts/mv.py check
```

`check`가 전부 OK가 되어야 한다. LaTeX(수 GB)를 빼려면
`setup_manim.sh --no-tex` — 대신 `MathTex`를 못 쓴다.

### 2) 플러그인 등록

Claude Code에서:

```
/plugin marketplace add juvilan/math-video-agent
/plugin install math-video-agent
```

또는 로컬 프로젝트에 그냥 복사해서 `skills/`, `agents/`,
`commands/`를 쓰는 방식도 된다.

---

## 사용

```
/math-video 행렬식이 왜 넓이 배율인지
/math-video 로렌츠 끌개와 카오스 --길이 7분 --4k
/storyboard 푸리에 변환 --대상 학부1학년
/mv-render scenes/lorenz.py LorenzAttractor --4k
```

에이전트를 직접 부르려면:

```
math-video-director 에이전트로 "베이즈 정리" 영상 만들어줘
```

---

## 예제 — 파이프라인을 끝까지 돌린 결과

[`examples/circle-area/`](examples/circle-area/) 에 주제 한 줄에서
1080p60 완본(69.6초)까지 간 전체 기록이 있다. 기획서, 씬 코드,
그리고 **검증 루프에서 실제로 걸린 버그 3건**이 그대로 남아 있다.

![원의 넓이 예제](docs/images/example-circle-area.png)

> 원을 얇은 고리로 자른다 → 반지름 t인 고리의 길이는 2πt →
> 펴서 짧은 것부터 쌓으면 밑변 2πr, 높이 r인 삼각형 → ½ × 2πr × r = πr²

---

## 파이프라인

```
① 기획      주제 → 핵심 한 문장 → 비트시트          math-storyboard
② 씬 분할   비트 → Scene (1씬 = 1아이디어 = 20~60초)
③ 코딩      템플릿에서 시작                          manim-video/templates
④ 검증 ★   still(PNG) → 눈으로 확인 → preview(mp4)  mv.py
⑤ 최종      1080p60 / 4K60 렌더 → 편집 툴로 인계     mv.py final
```

### ④가 핵심이다

원본 영상에서 Grant가 쓰는 `checkpoint_paste` — 씬 상태를 캐싱해
짧은 구간만 반복 확인하는 Sublime 매크로 — 가 제작 속도를
좌우한다. Claude Code에는 그 매크로가 없으므로 세 가지로 재구성했다:

1. 씬을 20~60초로 **강제 분할**
2. `mv.py still ... -n 3,5` 로 특정 구간의 마지막 프레임만 PNG 렌더
3. 그 PNG를 **Read 툴로 열어서 실제로 본다**

Manim 코드는 문법이 통과해도 조용히 망가진다 — 객체가 화면 밖에
있거나, 라벨이 겹치거나, 한글이 네모로 나오거나, 3D 카메라가
물체 뒤를 보고 있어도 에러가 없다. **렌더한 그림을 보지 않은 씬은
완성된 게 아니다.**

---

## 씬 템플릿

| 파일 | 내용 |
|---|---|
| `scene_base.py` | 팔레트·한글 폰트·자막 헬퍼. 모든 씬의 출발점 |
| `ode_trajectory.py` | **로렌츠 끌개** — scipy 수치해, 초기조건 발산, 3D 카메라 회전, 잔상 꼬리 |
| `formula_walkthrough.py` | 수식을 항별로 색칠·강조·해설 |
| `transform_anagram.py` | 수식 A → B, 글자가 자리를 옮기는 변형 |
| `graph_plot.py` | 접선·기울기, 리만합→적분, 파라미터 훑기 |
| `vector_field.py` | 선형변환(행렬식=넓이배율), 벡터장·흐름선 |

`ode_trajectory.py`는 원본 영상의 메인 프로젝트를 CE로 통째로
포팅한 것이다. `lorenz_system`과 축 범위만 바꾸면 Rössler,
이중진자 등에 그대로 쓸 수 있다.

---

## 코딩 하드 룰

`skills/manim-video/SKILL.md` §3의 요약:

1. **좌표는 반드시 `axes.c2p()`를 거친다.** 하드코딩하면 축 범위를
   바꾸는 순간 전부 깨진다.
2. **변수 하나 = 색 하나.** 수식·그래프·라벨 어디에 나오든 같은 색.
   동시에 3~4색을 넘기지 않는다.
3. **시간이 흐르는 궤적은 `rate_func=linear`.** 기본값 `smooth`를
   쓰면 끝에서 시간이 느려지는 물리적으로 틀린 그림이 된다.
4. `run_time`은 내레이션 길이에서 역산한다.
5. 씬이 60초를 넘으면 쪼갠다.
6. 점 2000개 초과 시 `set_points_smoothly` 대신 `set_points_as_corners`.
7. 한글은 `Text(font=...)`, 수식은 `MathTex`. `Tex`에 한글을 넣지 않는다.

---

## 한국어 / 영어

기본은 한국어. 자막·라벨은 `Text(font="NanumGothic")`, 수식은
`MathTex`로 분리한다 (`Tex`는 기본 LaTeX 템플릿에서 한글이 깨진다).

영어 버전은 문자열을 `STRINGS` dict에 모아두고:

```bash
MV_LANG=en manim -qh scene.py MyScene
```

자세한 건 `skills/manim-video/references/typography-korean.md`.

---

## Manim CE vs ManimGL

기본은 **Community Edition**. 설치가 쉽고 문서가 있고 헤드리스에서
돈다. 원본 영상의 `embed()` 인터랙티브 워크플로우가 꼭 필요하거나
3b1b 공식 저장소 코드를 그대로 돌려야 할 때만 ManimGL로 간다 —
전환 가이드와 API 차이표는
`skills/manim-video/references/manimgl.md`.

CE 코드는 ManimGL에서 그대로 돌지 않는다. 호환 레이어가 없다.

---

## 경계

이 플러그인은 **Manim 렌더 파일까지** 만든다. 내레이션 녹음, 컷
편집, BGM, 썸네일, 업로드는 범위 밖이다 — Final Cut / Premiere /
DaVinci 쪽 작업이다. 원본 영상에서도 Grant는 렌더된 MP4를
Final Cut으로 가져가서 편집한다.

---

## 검증 상태

씬 템플릿 6개 파일의 **모든 Scene 클래스를 Manim CE v0.21.0에서
실제로 렌더해 통과**시켰다 (Python 3.11, LaTeX = TeX Live,
한글 = NanumGothic). `docs/images/`의 그림이 그 결과물이다.
렌더 스틸을 눈으로 보고 고친 것들:

- `FlowLines` — 장이 0이 되는 점에서 `StreamLines`의 `run_time`이
  음수가 되며 크래시. 0을 지나지 않는 장으로 교체.
- `FormulaWalkthrough` — `\left(` / `\right)` 를 별도 항으로 나누면
  글리프 분배가 어긋남. 평범한 괄호로 교체.
- `TangentSlope`, `RiemannSum` — 라벨이 곡선과 겹침. 위치 이동.
- `LorenzAttractor` — 궤적 8개가 한 덩어리로 뭉개짐. 5개로 축소.
- `TitleDemo` — 마지막에 전부 FadeOut 되어 스틸이 검은 화면.
  스모크 테스트로 쓰이도록 화면을 남김.

문서(`references/`)의 API 기술은 CE 0.18~0.21 기준이며, 이 중
실제 실행으로 확인된 것은 템플릿이 사용하는 범위다. ManimGL 절은
문서 대조로만 작성했고 실행 검증은 하지 않았다.

---

## 라이선스

MIT. Manim은 별도 라이선스(MIT)를 따르며 이 레포에 포함되지 않는다.
