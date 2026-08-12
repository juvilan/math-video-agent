# 예제 — 원의 넓이는 왜 πr² 인가

이 플러그인의 파이프라인을 처음부터 끝까지 한 번 돌린 결과물이다.
주제 한 줄에서 시작해 1080p60 완본까지 갔다.

| | |
|---|---|
| 길이 | 69.6초 (씬 4개) |
| 대상 | 중1~중2 |
| 해상도 | 1920×1080 @ 60fps |

## 파일

```
storyboard.md     ① 기획 — 비트시트, 내레이션, 색 팔레트
scene_base.py     템플릿에서 복사해온 공용 베이스 (팔레트·한글·자막 헬퍼)
circle_area.py    ②③ 씬 4개 — Hook / Rings / Unroll / Result
```

렌더 결과(`media/`)는 `.gitignore` 대상이라 커밋되지 않는다.
아래 명령으로 직접 뽑는다.

## 재현

```bash
cd examples/circle-area
MV=../../skills/manim-video/scripts/mv.py

python3 $MV check                              # 환경 점검

# ④ 검증 루프 — 스틸을 뽑아 눈으로 본 뒤 고친다
python3 $MV still   circle_area.py Unroll
python3 $MV still   circle_area.py Rings -n 0,7   # 강조 구간만
python3 $MV preview circle_area.py Unroll         # 타이밍 확인

# ⑤ 최종
for s in Hook Rings Unroll Result; do
  python3 $MV final circle_area.py $s
done
```

씬을 하나로 잇는 건 Manim의 일이 아니라 편집의 일이지만,
빠르게 확인하려면:

```bash
cd media/videos/circle_area/1080p60
printf "file 'Hook.mp4'\nfile 'Rings.mp4'\nfile 'Unroll.mp4'\nfile 'Result.mp4'\n" > concat.txt
ffmpeg -f concat -safe 0 -i concat.txt -c copy circle-area-full.mp4
```

## 아이디어

원을 얇은 고리로 자른다. 반지름 t인 고리의 길이는 2πt.
이 고리들을 펴서 짧은 것부터 쌓으면 밑변 2πr, 높이 r인 삼각형이 된다.

```
½ × 2πr × r = πr²
```

## 검증 루프에서 실제로 걸린 것

스틸을 Read로 열어보고 나서야 발견한 것들. 코드만 봐서는 전부
멀쩡해 보였다.

| 씬 | 증상 | 원인 |
|---|---|---|
| `Unroll` | 높이 표시 `r`이 아예 안 보임 | 고리들이 만든 밝은 면 위에 같은 계열 색으로 그림. 삼각형 바깥으로 빼고 브레이스로 교체 |
| `Result` | `=`가 아래 수식 위에 겹침 | 두 수식 간격이 좁아 중간점이 아래 수식 안으로 들어감 |
| `Hook` | LaTeX 컴파일 실패 | `MathTex(r"\text{넓이}")` — 한글은 기본 LaTeX 템플릿에서 못 쓴다. `Text` + `MathTex` 조합으로 분리 |

## 기획 대비 실제 길이

| 씬 | 기획 | 실제 |
|---|---|---|
| Hook | 14s | 13.3s |
| Rings | 22s | 19.1s |
| Unroll | 30s | 24.6s |
| Result | 16s | 12.7s |
| **합계** | **82s** | **69.6s** |

전체가 기획보다 15% 짧다. 비트시트의 길이 추정이 넉넉했던 쪽이고,
자막을 읽는 데 부족한 구간은 없다. 내레이션을 실제로 녹음해 붙일
때는 이 차이만큼 `wait`을 늘려 맞추면 된다.
