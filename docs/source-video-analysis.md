# 원본 분석 — "How I animate 3Blue1Brown | A Manim demo with Ben Sparks"

- 채널: 3Blue1Brown (Grant Sanderson)
- 게스트: Ben Sparks (수학교육가, Numberphile)
- 공개: 2024-10-12
- URL: https://www.youtube.com/watch?v=rbu7Zu5X1zI

이 레포의 스킬·에이전트·템플릿은 전부 이 영상에서 관찰된 실제
제작 워크플로우를 코드화한 것이다. 아래는 영상 내용 정리와,
각 항목이 이 레포 어디로 옮겨졌는지의 매핑이다.

---

## 1. Manim의 정체와 두 갈래 (00:52)

Grant가 대학 졸업 무렵, 수학적 변환(transformation)을 코드로
시각화하려고 직접 쓴 Python 라이브러리.

| | ManimGL (3b1b 원본) | Manim Community (CE) |
|---|---|---|
| 관리 | Grant 개인 | 커뮤니티 |
| 방향 | 인터랙티브·성능 최적화 | 문서화·테스트·안정성 |
| 설치 | 까다로움 (OpenGL 의존) | `pip install manim` |
| 권장 | 영상 제작 전문가 | **입문자·대부분의 경우** |

> **이 레포의 선택**: 기본은 CE. ManimGL은
> `skills/manim-video/references/manimgl.md`로 대응.

---

## 2. 실시간 코딩 환경 (02:35)

- 에디터: Sublime Text
- 터미널: Terminus (에디터 내장 터미널)
- 두 개를 붙여서 "코드 선택 → 단축키 → 즉시 화면 반영" 구조

### checkpoint_paste (06:17) ← 영상 최대의 인사이트

긴 씬을 매번 처음부터 렌더하지 않는다. 특정 지점까지의 **씬 상태를
캐싱**해두고, 선택한 코드 블록만 그 상태 위에 붙여 실행한다.
Jupyter 노트북의 셀 실행과 같은 감각을 애니메이션 제작에 가져온 것.

이게 없으면 30초짜리 씬의 마지막 3초를 고칠 때마다 30초를 다시
렌더해야 한다. 제작 속도를 좌우하는 핵심 장치.

> **이 레포로의 이식**: Claude Code에는 Sublime 매크로가 없으므로
> 등가물을 세 가지로 재구성했다 —
> ① 씬을 20~60초 단위로 강제 분할,
> ② `mv.py still ... -n <구간>`으로 특정 애니메이션 구간의 마지막
>    프레임만 PNG 렌더,
> ③ 그 PNG를 Read 툴로 **직접 눈으로 확인**.
> `SKILL.md` 4절 "프리뷰 루프"가 이것이다.

---

## 3. Hello World 예제 (02:40)

- `Scene` 클래스 정의 → `construct()` 안에서 mobject 생성·배치
- `self.add(...)`: 그냥 놓기
- `self.play(Write(text))`, `self.play(Transform(text, circle))`:
  텍스트가 원으로 부드럽게 변형

### Rate function / 이징 (09:51)

애니메이션 속도 곡선. 기본은 smooth(cubic bezier: 천천히→빠르게→
천천히), `linear`로 바꾸면 등속.

> **이식**: `SKILL.md` 코딩 규칙 #3 — 시간이 흐르는 궤적은 반드시
> `linear`. `references/3b1b-style.md`에 상황별 rate_func 표.

---

## 4. 로렌츠 끌개 (10:31) ← 영상의 메인 프로젝트

카오스 이론의 대표 모델을 수식에서 애니메이션까지 통째로 만든다.

| 단계 | 내용 | 타임스탬프 |
|---|---|---|
| 수치해 | `scipy.integrate.solve_ivp`로 ODE 풀기 | 13:20 |
| 좌표 변환 | 수학 좌표 → Manim 3D 좌표 (`c2p`) | 16:49 |
| 초기조건 | epsilon 차이의 여러 점을 동시에 출발 | 20:26 |
| 발산 시각화 | 궤적들이 갈라지지만 끌개 구조 안에 머무름 | 28:42 |
| 3D 카메라 | 프레임을 천천히 회전·팬해서 입체감 확보 | 33:50 |
| 잔상 꼬리 | 점 뒤로 서서히 사라지는 trail | 39:13 |
| 최종 렌더 | CLI로 4K MP4 → Final Cut으로 반출 | 41:58 |

> **이식**: `skills/manim-video/templates/ode_trajectory.py`가
> 이 프로젝트 전체를 CE로 포팅한 것이다. 위 7단계가 전부 들어있고
> 상수만 바꾸면 다른 ODE(Rössler, 이중진자 등)에 그대로 쓸 수 있다.

---

## 5. LaTeX 수식 다루기 (44:36)

### Mathpix (44:57)
화면의 수식을 캡처 → LaTeX 코드/SVG로 즉시 변환. 논문·교과서
수식을 손으로 옮겨치지 않는 우회로.

> **이식**: Claude가 이미지에서 LaTeX를 읽을 수 있으므로 별도 툴이
> 불필요. `math-storyboard` 스킬에 "수식 이미지를 주면 LaTeX로
> 받아쓴다" 경로를 넣었다.

### 수식 요소별 색상·인덱싱 (46:26)
수식 안의 특정 변수(x, y, z)에 색을 매핑. 개별 글자를 인덱싱해
따로 움직인다.

### 아나그램 애니메이션 (49:10)
수식 A의 각 글자가 수식 B의 대응 위치로 날아가는 변형.

> **이식**: `templates/formula_walkthrough.py`(색 매핑·항 강조),
> `templates/transform_anagram.py`(`TransformMatchingTex` 기반
> 문자 단위 이동).

---

## 6. 렌더와 반출 (41:58)

코딩이 끝나면 CLI로 4K MP4 렌더 → Final Cut 등 편집 프로그램에서
내레이션·컷편집·BGM.

> **이식**: `scripts/mv.py final --4k`, 그리고 SKILL.md 5절이
> "Manim의 역할은 렌더까지"라는 경계를 명시한다.

---

## 매핑 요약

| 영상의 관찰 | 이 레포의 산출물 |
|---|---|
| CE vs GL 선택 | 기본 CE + `references/manimgl.md` |
| checkpoint_paste | `SKILL.md` §4 프리뷰 루프 + `mv.py still -n` |
| rate function | 코딩 규칙 #3 + `3b1b-style.md` 이징 표 |
| 로렌츠 전 과정 | `templates/ode_trajectory.py` |
| c2p 좌표변환 | 코딩 규칙 #1 (하드 룰) |
| 3D 카메라 무빙 | `manim-ce-cookbook.md` 카메라 절 |
| 잔상 꼬리 | `ode_trajectory.py`의 `TracedPath` |
| 수식 색 매핑 | `templates/formula_walkthrough.py` |
| 아나그램 변형 | `templates/transform_anagram.py` |
| Mathpix | 이미지→LaTeX 경로 (`math-storyboard`) |
| 4K 렌더 → 편집 | `mv.py final --4k` + SKILL.md §5 |

---

## 각주

영상 원문은 이 환경의 네트워크 정책상 직접 열람이 불가했다. 위
타임스탬프와 내용 구조는 사용자가 제공한 상세 분석과 공개된 영상
메타데이터에 근거한다. 기술적 내용(API, 워크플로우)은 Manim CE
공식 문서와 대조해 검증했다.
