---
description: 수학 개념을 받아 Manim 영상을 기획부터 최종 렌더까지 만든다
argument-hint: <주제> [--길이 5분] [--en]
---

# /math-video

주제: **$ARGUMENTS**

`math-video-director` 에이전트의 절차를 따라 끝까지 진행한다.

1. `python3 skills/manim-video/scripts/mv.py check` — 환경 점검.
   MISS가 있으면 멈추고 보고한다.
2. `math-storyboard` 스킬로 비트시트 작성 → 사용자에게 보여준다.
3. `manim-video` 스킬의 템플릿에서 씬 코드 작성.
4. 씬마다 `mv.py still` → **PNG를 Read로 열어 눈으로 확인** →
   `mv.py preview`로 타이밍 확인. 통과 전에 다음 씬으로 넘어가지 않는다.
5. 전부 통과하면 `mv.py final`.
6. 파일 경로·길이·내레이션 스크립트·못 한 것을 정리해 인계한다.

옵션:
- `--길이 N분` — 목표 길이 (기본 5분)
- `--en` — 영어 버전 (`MV_LANG=en`)
- `--4k` — 최종을 4K로
