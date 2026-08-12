# 예제 — 원의 넓이는 왜 πr² 인가

이 플러그인의 파이프라인을 처음부터 끝까지 한 번 돌린 결과물이다.
주제 한 줄에서 시작해 1080p60 완본까지 갔다.

| | |
|---|---|
| 길이 | 64.0초 (씬 4개) |
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
QC=../../skills/manim-video/scripts/qc.py
export MV_SFX_DIR=../../assets/sfx          # 효과음 위치

python3 $MV check                              # 환경 점검

# ④-1 좌표로 (이미지 없음, 반복 무료)
for s in Hook Rings Unroll Result; do python3 $MV layout circle_area.py $s; done

# ④-2 이미지로 — 깨끗해진 뒤에
python3 $MV still   circle_area.py Unroll
python3 $MV still   circle_area.py Rings -n 0,7   # 강조 구간만
python3 $MV preview circle_area.py Unroll         # 타이밍 확인

# ⑤ 최종
for s in Hook Rings Unroll Result; do
  python3 $MV final circle_area.py $s
done
```

씬 잇기 — **손으로 `ffmpeg concat` 하지 않는다.** 첫 파일에 오디오가
없으면 뒤 씬 소리가 경고 없이 사라진다.

```bash
cd media/videos/circle_area/1080p60
python3 ../../../../../../skills/manim-video/scripts/mv.py join \
    circle-area-full.mp4 Hook.mp4 Rings.mp4 Unroll.mp4 Result.mp4
```

```bash
# ⑥ 검수 — 완성본을 프레임으로 뜯어본다
python3 $QC stats  media/videos/circle_area/1080p60/circle-area-full.mp4
python3 $QC sheet  media/videos/circle_area/1080p60/circle-area-full.mp4 -g 4x4
python3 $QC guides media/videos/circle_area/1080p60/circle-area-full.mp4 46.0
```

## 효과음

6군데에 들어 있다 (`whoosh` ×3, `pop`, `tick`, `chime`).
음원은 레포 루트 `assets/sfx/` 의 **ffmpeg 합성 자리표시자**다 —
사인파와 핑크노이즈라 저작권 문제가 없고, 실제 음원으로 갈아끼우라고
넣어둔 것이다.

```python
self.sfx("whoosh", gain=-12)      # play 앞에 놓는다
self.play(Create(circle), run_time=1.6)
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

## ⑥ 검수에서 걸린 것

렌더가 끝난 뒤 `qc.py`로 완성본을 다시 뜯어봤다. **스틸 검사에서는
하나도 안 걸렸던 것들이다** — 정지 화면 하나로는 보이지 않는 부류다.

| 도구 | 발견 | 조치 |
|---|---|---|
| `stats` | 4초 이상 정지 3건 (7.9s/5.3s, 51.3s/5.5s, 57.7s/4.4s) | 51.3s 구간의 `wait` 축소. 나머지 둘은 결론을 읽는 시간이라 유지 |
| `sheet` | 같은 자막이 4.3초 간격 두 칸에 걸침 — 15~20s, 41~46s | `LaggedStart run_time` 3.2→2.4, 홀드 축소 |
| `sheet` | 자막 전환 순간 두 자막이 같은 자리에 겹쳐 뭉개짐 | `MathScene.say()` 의 `FadeTransform` → 순차 FadeOut/FadeIn |
| `guides` | 자막이 title-safe(90%) 하단선에 걸침 | `subtitle()` buff 0.45→0.6 |

뒤의 두 건은 예제가 아니라 **템플릿(`scene_base.py`) 쪽 버그**였다.
이 예제를 검수하다 찾아서 템플릿을 고쳤으니 앞으로 만드는 모든
영상에 적용된다.

수정 후 재렌더 → 재검수까지 돌렸다. 남은 정지 2건은 결론 수식과
훅의 물음표를 읽는 시간이라 의도적으로 남겼다.

## ④-1 좌표 검사(`layout`)가 잡은 것

검수(⑥)까지 통과한 뒤에 `mv.py layout` 을 붙였더니 **이미지로는
아무도 못 봤던 게 하나 더 나왔다.**

```
[play#19~play#21] MathTex('r') title-safe 밖
                  (x 6.28~6.47, y -0.05~0.15, 안전 ±6.40/±3.60)
```

`Unroll` 의 높이 라벨이 안전영역을 0.07 유닛 넘어가 있었다.
`guides` 로 본 프레임(50초)에는 그 라벨이 아직 안 떠 있어서
안 보였던 것. **이미지 한 장 없이, 토큰 거의 0으로 잡았다.**

## 효과음을 붙이다 발견한 것

| 증상 | 원인 |
|---|---|
| 렌더는 성공인데 오디오 트랙이 없음 | manim 캐시가 켜져 있으면 캐시된 애니메이션은 `skip_animations=True` 로 돌고 `add_sound` 가 조용히 return 한다. `mv.py` 가 소스에 소리가 있으면 캐시를 자동으로 끄게 고침 |
| 씬 첫 소리에서 traceback, 그런데 렌더는 성공 | `time_offset` 이 음수라 타임스탬프가 0 미만 → `ValueError`. 렌더러가 그 예외를 삼킨다. `sfx()` 가 현재 시각을 보고 앞당길 양을 잘라내게 고침 |
| 이어붙이니 소리가 전부 사라짐 | `concat -c copy` 는 첫 파일에 오디오가 없으면 뒤 소리를 버린다. `mv.py join` 이 모든 입력에 오디오를 만들어 길이를 맞추게 함 |

셋 다 **에러 없이 소리만 없어지는** 종류다. `qc.py stats` 가
오디오 트랙과 길이를 항상 찍는 이유.

## 기획 대비 실제 길이

| 씬 | 기획 | 초판 | 검수 후 |
|---|---|---|---|
| Hook | 14s | 13.3s | 12.6s |
| Rings | 22s | 19.1s | 16.5s |
| Unroll | 30s | 24.6s | 22.0s |
| Result | 16s | 12.7s | 12.8s |
| **합계** | **82s** | **69.6s** | **64.0s** |

전체가 기획보다 22% 짧다. 비트시트의 길이 추정이 넉넉했던 쪽이고,
검수에서 죽은 시간을 걷어내며 더 줄었다. 자막을 읽는 데 부족한
구간은 없다. 내레이션을 실제로 녹음해 붙일 때는 이 차이만큼
`wait`을 늘려 맞추면 된다.
