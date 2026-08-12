---
description: 수학 개념을 받아 Manim 영상을 만든다 (세 지점에서 확인받으며)
argument-hint: <주제> [--길이 5분] [--en] [--4k] [--빨리]
---

# /math-video

주제: **$ARGUMENTS**

`math-video-director` 에이전트의 절차를 따른다. **세 번 멈춘다.**

## 0. 준비

1. `python3 skills/manim-video/scripts/mv.py check` — MISS 있으면 멈춘다
2. **`.mv/intent.md` 를 읽는다.** 톤·색·속도·금지 목록이 이미
   있으면 그건 다시 묻지 않는다. 없으면
   `skills/manim-video/templates/project/intent.md` 를 복사해 만든다

## G1 — 방향

`math-storyboard` 로 핵심 한 문장 후보 **3개**, 대상, 길이,
비트 뼈대(제목만)를 확인받는다. `AskUserQuestion` 을 쓴다.
내레이션은 아직 안 쓴다.

→ `.mv/decisions.md` 에 기록. **기록 없이 다음으로 가지 않는다.**

## G2 — 그림 ← 가장 중요

비트별로 **최종 화면만** 만든다 (애니메이션 없이 `self.add`).

```bash
python3 skills/manim-video/scripts/mv.py layout <file> <Scene>
python3 skills/manim-video/scripts/mv.py sketch <file>
```

나온 스틸 판을 **SendUserFile 로 보여주고** 구도·색·밀도·비유를
확인받는다. 수정 요청이 오면 스틸만 고쳐 다시 보여준다.
**승인 전에 애니메이션을 쓰지 않는다.**

→ `.mv/decisions.md` 에 기록.

## G3 — 첫 씬

첫 비트에만 애니메이션을 입혀 `mv.py preview` 로 보여준다.
속도·자막 분량·효과음 정도를 확인받는다. 여기서 정해진 게
**나머지 씬 전부에 적용된다.**

→ `.mv/decisions.md` 에 기록.

## 이후 — 묻지 않고 달린다

4. 나머지 씬: `layout` → `still` → `preview`
5. `mv.py final`, 씬이 여럿이면 `mv.py join`
6. 검수: `qc.py stats` / `sheet` / `guides` → **PNG를 Read로 연다**
7. 인계 + **`.mv/intent.md` 갱신** (특히 "이건 아닌데"를 하지 말 것에)

## 옵션

- `--길이 N분` 목표 길이 (기본 5분)
- `--en` 영어 버전 (`MV_LANG=en`)
- `--4k` 최종을 4K로
- `--빨리` G1·G3 생략. **G2는 생략하지 않는다.**
  생략했으면 인계할 때 무엇을 안 물었는지 명시한다
