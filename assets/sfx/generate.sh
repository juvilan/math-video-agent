#!/usr/bin/env bash
# 수학 애니메이션용 효과음 팩을 ffmpeg 로 합성한다.
#
#   bash assets/sfx/generate.sh
#
# 전부 순수 합성이라 저작권 문제가 없다. 톤이 마음에 안 들면 아래
# 수식의 주파수·감쇠 계수를 고쳐 다시 돌리면 된다.
#
# 설계 원칙
#  - 짧다. 수학 영상의 효과음은 "들렸다"는 느낌만 주고 사라져야 한다.
#  - 배음이 단순하다. 화면의 정보와 경쟁하지 않는다.
#  - 끝을 반드시 페이드아웃한다. 안 그러면 딸깍(클릭) 잡음이 남는다.
#  - 피크를 -3dBFS 근처로 맞춘다. 실제 음량은 sfx(gain=) 로 조절한다.
set -euo pipefail

cd "$(dirname "$0")"
SR=44100

# aevalsrc 는 t(초)에 대한 수식으로 파형을 만든다.
#   주파수를 (f0 + k*t) 로 쓰면 피치가 선형으로 쓸린다(sweep).
#   exp(-a*t) 를 곱하면 지수 감쇠 — 타악기 같은 붙임이 된다.
gen() {
  local name="$1" expr="$2" dur="$3"
  ffmpeg -y -loglevel error \
    -f lavfi -i "aevalsrc=${expr}:d=${dur}:s=${SR}" \
    -af "afade=t=out:st=$(python3 -c "print(max(${dur}-0.02,0))"):d=0.02,alimiter=limit=0.7:level=disabled" \
    -ac 1 -c:a pcm_s16le "${name}.wav"
}

# ── 등장 ─────────────────────────────────────────────────────────
# 피치가 살짝 떨어지는 짧은 사인. 객체 하나가 화면에 놓일 때.
gen pop "0.9*sin(2*PI*(760-260*t)*t)*exp(-26*t)" 0.16

# 아주 짧은 고음 클릭. 점 찍기, 라벨 붙이기처럼 작은 표시.
gen tick "0.7*sin(2*PI*2400*t)*exp(-150*t)" 0.05

# 단계 전환. tick 보다 낮고 둔탁하다.
gen click "0.8*sin(2*PI*1500*t)*exp(-80*t)" 0.09

# ── 움직임 ───────────────────────────────────────────────────────
# 피치가 올라가는 스윕 + 노이즈. 변형·이동.
ffmpeg -y -loglevel error \
  -f lavfi -i "aevalsrc=0.5*sin(2*PI*(180+1500*t)*t):d=0.42:s=$SR" \
  -f lavfi -i "anoisesrc=c=pink:a=0.28:d=0.42:r=$SR" \
  -filter_complex "[1:a]highpass=f=500,lowpass=f=7000[n];\
[0:a][n]amix=inputs=2:weights=1 0.9:normalize=0,\
afade=t=in:st=0:d=0.08:curve=exp,afade=t=out:st=0.18:d=0.24,alimiter=limit=0.7:level=disabled" \
  -ac 1 -c:a pcm_s16le whoosh.wav

# 더 길고 무거운 전환. 씬이 통째로 바뀔 때.
ffmpeg -y -loglevel error \
  -f lavfi -i "aevalsrc=0.5*sin(2*PI*(120+700*t)*t):d=0.9:s=$SR" \
  -f lavfi -i "anoisesrc=c=brown:a=0.35:d=0.9:r=$SR" \
  -filter_complex "[1:a]highpass=f=200,lowpass=f=4000[n];\
[0:a][n]amix=inputs=2:weights=1 1:normalize=0,\
afade=t=in:st=0:d=0.35:curve=exp,afade=t=out:st=0.62:d=0.28,alimiter=limit=0.7:level=disabled" \
  -ac 1 -c:a pcm_s16le sweep.wav

# ── 값의 변화 ────────────────────────────────────────────────────
# 올라가며 커진다. 누적·수렴 (리만합을 잘게 쪼갤 때 같은 것).
gen rise "0.75*sin(2*PI*(280+820*t)*t)*(t/0.55)" 0.55

# 내려가며 잦아든다. 감소·소멸.
gen drop "0.8*sin(2*PI*(1150-780*t)*t)*exp(-3.2*t)" 0.55

# ── 결론 ─────────────────────────────────────────────────────────
# 장3화음 벨(C6-E6-G6). 결론이 확정될 때 한 번만.
gen chime "(0.45*sin(2*PI*1046.5*t)+0.3*sin(2*PI*1318.5*t)+0.22*sin(2*PI*1568*t))*exp(-3.6*t)" 1.30

# 두 음이 올라간다. 결과 공개 — chime 보다 짧고 가볍다.
# 수식 안의 쉼표는 ffmpeg 필터 파서가 옵션 구분자로 읽는다. \, 로 escape.
gen reveal "if(lt(t\,0.13)\,0.8*sin(2*PI*880*t)*exp(-11*t)\,0.8*sin(2*PI*1318.5*(t-0.13))*exp(-7*(t-0.13)))" 0.55

echo
printf "%-12s %8s %10s %10s\n" 파일 길이 피크 RMS
for f in *.wav; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  stats=$(ffmpeg -hide_banner -i "$f" -af astats=measure_overall="Peak_level+RMS_level" -f null - 2>&1)
  peak=$(echo "$stats" | grep -m1 "Peak level" | awk '{print $NF}')
  rms=$(echo "$stats"  | grep -m1 "RMS level"  | awk '{print $NF}')
  printf "%-12s %7.2fs %9sdB %9sdB\n" "$f" "$dur" "$peak" "$rms"
done
