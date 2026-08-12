---
description: 렌더된 영상을 프레임 단위로 검수한다 (자막 위치, 겹침, 죽은 시간)
argument-hint: <video.mp4> [--fix] [--grid 4x4]
---

# /mv-qc

대상: **$ARGUMENTS**

`math-video-qc` 에이전트의 절차를 따른다. 경로를 안 주면
`media/videos/**/*.mp4`를 찾아 목록을 보여주고 고르게 한다.

```bash
QC=skills/manim-video/scripts/qc.py
```

1. `python3 "$QC" stats <video>` — 검은 화면 / 4초 이상 정지 / 규격
2. `python3 "$QC" sheet <video> -g 4x4` — **출력 PNG를 Read로 연다**
   ```
   □ 자막과 화면이 어긋난 칸
   □ 같은 자막이 연속 두 칸에 걸친 곳 (= 4초 이상 정지)
   □ 빈 칸
   □ 씬 사이 구성이 튀는 곳
   □ 색 일관성
   ```
3. `python3 "$QC" guides <video> <시각>` — 자막 있는 시각 2~3개.
   Read로 열어 청록 밴드 + 노란 title-safe 안에 있는지 확인.
   **경계에 걸친 것도 실패다.**
4. `python3 "$QC" strip <video> <시작> <끝> -n 8` — 이상해 보인 구간과
   변형/카메라 구간을 확대해서 확인.
5. 스토리보드가 있으면 비트 순서·길이·내용 중복을 대조.

결과는 `references/qc-checklist.md`의 보고 형식(표)으로 정리한다.
**고치지 않기로 한 것도 이유와 함께 적는다.**

`--fix`를 주면 작고 확실한 것(자막 여백, `wait`, `run_time`, 라벨
위치)까지 고치고 해당 씬을 다시 렌더한 뒤 **1~2단계를 다시 돌린다.**
내용 변경에 해당하는 건 고치지 않고 보고만 한다.

PNG를 뽑아놓고 Read로 열지 않았으면 검수한 게 아니다.
