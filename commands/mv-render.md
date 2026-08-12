---
description: 기존 Manim 씬을 검증 루프에 태워 렌더한다
argument-hint: <file.py> [Scene] [--4k] [--all]
---

# /mv-render

대상: **$ARGUMENTS**

이미 작성된 씬 파일을 렌더한다. 씬 이름을 안 주면
`mv.py scenes <file>`로 목록을 뽑아 사용자에게 확인받는다.

씬마다:

1. `python3 skills/manim-video/scripts/mv.py still <file> <Scene>`
2. 출력 마지막 줄의 PNG 경로를 **Read 툴로 열어서 확인한다**
   ```
   □ 화면 밖으로 나간 요소 없음
   □ 라벨/수식 겹침 없음
   □ 색이 배경과 구분됨
   □ 한글이 네모(□)가 아님
   □ 3D면 물체가 카메라 앞
   ```
3. 문제가 있으면 코드를 고치고 1번으로.
4. 통과하면 `mv.py preview`로 타이밍 확인.
5. 전부 통과 후에만 `mv.py final`(`--4k`면 4K).

렌더 에러는 `skills/manim-video/references/troubleshooting.md`를 본다.
같은 씬에서 3회 실패하면 멈추고 보고하되, **나머지 씬은 마저
완성한 뒤** 무엇이 안 됐는지 함께 알린다.

끝나면 파일 경로와 길이를 정리해서 출력한다.
