---
description: 수학 개념을 받아 Manim 영상을 기획부터 최종 렌더까지 만든다
argument-hint: <주제> [--길이 5분] [--en]
---

# /math-video

주제: **$ARGUMENTS**

`math-video-director` 에이전트의 절차를 따라 끝까지 진행한다.

1. `python3 skills/manim-video/scripts/mv.py check` — 환경 점검.
   MISS가 있으면 멈추고 보고한다.
2. `math-storyboard` 스킬로 콘티 작성. **사용자와 단계별로** —
   핵심 한 문장 / 대상·길이 / 비트 뼈대 / 콘티 / 내레이션 각각에서
   멈추고 확인받는다. 혼자 완성해서 코딩으로 넘어가지 않는다.
3. `manim-video` 스킬의 템플릿에서 씬 코드 작성.
4. 씬마다 **`mv.py layout` 먼저** (이미지 없이 좌표로 — 화면 밖 /
   title-safe 이탈 / 글자 겹침). 깨끗해진 뒤에 `mv.py still` →
   **PNG를 Read로 열어 색·모양 확인** → `mv.py preview`로 타이밍.
   통과 전에 다음 씬으로 넘어가지 않는다.
5. 전부 통과하면 `mv.py final`. 씬이 여럿이면 `mv.py join` 으로
   이어붙인다 (손으로 ffmpeg concat 하면 오디오가 사라진다).
6. **검수** — `math-video-qc` 절차. `qc.py stats` / `sheet` / `guides` 를
   돌리고 **출력 PNG를 Read로 열어서** 죽은 시간, 자막-화면 불일치,
   자막 안전영역 이탈을 찾는다. 고쳤으면 재렌더 후 재검수.
7. 파일 경로·길이·기획 대비 차이·검수 결과·못 한 것을 정리해 인계한다.

옵션:
- `--길이 N분` — 목표 길이 (기본 5분)
- `--en` — 영어 버전 (`MV_LANG=en`)
- `--4k` — 최종을 4K로
