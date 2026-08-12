#!/usr/bin/env python3
"""qc — 렌더된 영상을 실제로 들여다보는 검수 도구.

스틸(마지막 프레임)만 봐서는 알 수 없는 것들이 있다. 중간에 뭐가
겹쳤는지, 자막이 언제 사라지는지, 화면이 몇 초 동안 얼어 있는지,
검은 구간이 있는지. 이 스크립트는 그걸 보게 해준다.

  qc.py stats  <video>              자동 검사 — 검은 화면 / 정지 구간 / 규격
  qc.py sheet  <video> [-g 4x4]     등간격 프레임 대조표 한 장 (타임스탬프 각인)
  qc.py frame  <video> <시각>       특정 시각 한 프레임 (원본 해상도)
  qc.py guides <video> <시각>       안전영역 + 자막 밴드 가이드를 덧그린 프레임
  qc.py strip  <video> <시작> <끝>  구간을 촘촘히 뽑은 대조표 (동작 검사용)

시각은 초(12.5) 또는 hh:mm:ss(00:00:12.5) 둘 다 된다.
마지막 줄에 항상 출력 파일 경로만 단독으로 찍는다 — Read 툴로 바로 연다.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 자막 밴드: 화면 아래쪽 몇 %를 자막 영역으로 보는가.
# scene_base.subtitle() 이 to_edge(DOWN, buff=0.6) 로 놓는 위치와 맞춰져 있다.
SUBTITLE_BAND_TOP = 0.80
# 방송 기준 타이틀 세이프. 이 밖으로 나간 글자는 잘릴 수 있다고 본다.
TITLE_SAFE = 0.90


def _fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 1


def _need_ffmpeg() -> str | None:
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            return tool
    return None


def _font() -> str | None:
    """drawtext 는 fontfile 이 있어야 한다. 없으면 타임스탬프를 포기한다."""
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if os.path.exists(path):
            return path
    if shutil.which("fc-match"):
        try:
            out = subprocess.run(
                ["fc-match", "-f", "%{file}", "DejaVu Sans"],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
            if out and os.path.exists(out):
                return out
        except (subprocess.SubprocessError, OSError):
            pass
    return None


def _probe(video: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(video)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "ffprobe 실패")
    return json.loads(out.stdout)


def _video_info(video: Path) -> dict:
    data = _probe(video)
    stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if stream is None:
        raise RuntimeError("비디오 스트림이 없다")
    num, _, den = stream.get("r_frame_rate", "0/1").partition("/")
    fps = float(num) / float(den) if float(den) else 0.0
    return {
        "duration": float(data["format"].get("duration", 0.0)),
        "size": int(data["format"].get("size", 0)),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps": fps,
    }


def _parse_time(text: str) -> float:
    if ":" not in text:
        return float(text)
    parts = [float(p) for p in text.split(":")]
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def _run_ffmpeg(args: list[str]) -> tuple[int, str]:
    cmd = ["ffmpeg", "-hide_banner", "-y", *args]
    print("$ " + " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stderr


def _out_path(video: Path, suffix: str) -> Path:
    out_dir = video.parent / "qc"
    out_dir.mkdir(exist_ok=True)
    return out_dir / f"{video.stem}_{suffix}.png"


def _timestamp_filter(font: str | None, size: int = 26) -> str:
    """프레임에 원본 타임스탬프를 각인한다. fps 필터보다 **앞에** 놓아야
    선택된 프레임의 실제 시각이 찍힌다."""
    if font is None:
        return ""
    return (
        f"drawtext=fontfile='{font}':text='%{{pts\\:hms}}':"
        f"x=10:y=10:fontsize={size}:fontcolor=yellow:"
        f"box=1:boxcolor=black@0.65:boxborderw=6,"
    )


# ------------------------------------------------------------------ stats


def _detect(video: Path, vf: str, pattern: str) -> list[str]:
    code, log = _run_ffmpeg(["-i", str(video), "-vf", vf, "-f", "null", "-"])
    if code != 0:
        return []
    return re.findall(pattern, log)


def cmd_stats(args) -> int:
    video = Path(args.video)
    if not video.exists():
        return _fail(f"파일이 없다: {video}")

    info = _video_info(video)
    print(f"파일      {video}")
    print(f"길이      {info['duration']:.2f}s")
    print(f"해상도    {info['width']}x{info['height']} @ {info['fps']:.0f}fps")
    print(f"용량      {info['size'] / 1024 / 1024:.1f} MB")

    problems = 0

    # 검은 화면 — 씬 사이 공백, 객체를 add 안 한 구간, 카메라가 빈 곳을 보는 경우.
    #
    # 임계값 주의: blackdetect 의 흔한 기본값(pic_th=0.98, pix_th=0.10)은
    # 이 스타일에서 쓸 수 없다. 어두운 배경에 얇은 선과 수식만 있는 화면은
    # 원래 픽셀의 98% 이상이 검정이라, 내용이 멀쩡히 있는 씬 전체가
    # "검은 화면"으로 잡힌다(실제로 그렇게 오탐이 났다).
    # pix_th=0.07 은 배경색 #0f0f14(luma≈0.06) 바로 위, pic_th=0.995 는
    # "정말로 아무것도 없는" 프레임만 남긴다.
    blacks = _detect(
        video,
        "blackdetect=d=0.4:pic_th=0.995:pix_th=0.07",
        r"black_start:([\d.]+) black_end:([\d.]+)",
    )
    # 씬 첫머리 짧은 암전은 Create/FadeIn 이 0에서 시작하니 정상이다.
    blacks = [(s, e) for s, e in blacks if not (float(s) < 0.1 and float(e) < 1.0)]
    if blacks:
        problems += len(blacks)
        print("\n[검은 화면]")
        for start, end in blacks:
            print(f"  {float(start):6.2f}s ~ {float(end):6.2f}s "
                  f"({float(end) - float(start):.2f}s)")
        print("  → 의도한 암전이 아니면 객체가 화면 밖이거나 add를 빠뜨린 것이다.")

    # 정지 구간 — wait이 너무 길거나 애니메이션이 안 걸린 곳
    freezes = _detect(
        video,
        f"freezedetect=n=-55dB:d={args.freeze}",
        r"freeze_start: ([\d.]+)[\s\S]*?freeze_duration: ([\d.]+)",
    )
    if freezes:
        problems += len(freezes)
        print(f"\n[{args.freeze}초 이상 정지]")
        for start, dur in freezes:
            print(f"  {float(start):6.2f}s 부터 {float(dur):.2f}s")
        print("  → 내레이션이 깔릴 구간이면 정상. 아니면 죽은 시간이다.")

    if info["duration"] > 75:
        problems += 1
        print(f"\n[씬 길이] {info['duration']:.1f}s — 60초를 넘는다. "
              f"쪼개면 검증 루프가 빨라진다.")

    if problems == 0:
        print("\n자동 검사 통과. 다음은 눈으로 본다:")
    else:
        print(f"\n자동 검사에서 {problems}건. 아래로 눈으로 확인한다:")
    print(f"  python3 {sys.argv[0]} sheet {video}")
    return 0


# ------------------------------------------------------------------ sheet


def cmd_sheet(args) -> int:
    video = Path(args.video)
    if not video.exists():
        return _fail(f"파일이 없다: {video}")

    match = re.fullmatch(r"(\d+)x(\d+)", args.grid)
    if not match:
        return _fail(f"격자 형식이 틀렸다: {args.grid} (예: 4x4)")
    cols, rows = int(match.group(1)), int(match.group(2))
    tiles = cols * rows

    info = _video_info(video)
    duration = info["duration"]
    if duration <= 0:
        return _fail("영상 길이를 읽지 못했다")

    # 첫 프레임과 마지막 프레임 사이를 등분한다. 칸 수보다 프레임이
    # 모자라면 tile 필터가 빈 칸을 남기므로 살짝 넉넉히 뽑는다.
    interval = duration / tiles
    tile_w = max(240, min(480, 1920 // cols))

    vf = (
        f"{_timestamp_filter(_font())}"
        f"fps=1/{interval:.6f},"
        f"scale={tile_w}:-2,"
        f"tile={cols}x{rows}:margin=6:padding=4:color=#202028"
    )
    out = _out_path(video, f"sheet_{cols}x{rows}")
    code, log = _run_ffmpeg(["-i", str(video), "-vf", vf, "-frames:v", "1", str(out)])
    if code != 0 or not out.exists():
        sys.stderr.write(log[-2000:])
        return _fail("대조표 생성 실패")

    print(f"\n{duration:.1f}초를 {tiles}칸으로 (칸당 {interval:.1f}초 간격)")
    print("대조표 완료:")
    print(out.resolve())
    return 0


def cmd_strip(args) -> int:
    """짧은 구간을 촘촘히 — 변형 애니메이션이 제대로 도는지 볼 때."""
    video = Path(args.video)
    if not video.exists():
        return _fail(f"파일이 없다: {video}")

    start, end = _parse_time(args.start), _parse_time(args.end)
    if end <= start:
        return _fail("끝 시각이 시작 시각보다 뒤여야 한다")

    span = end - start
    tiles = args.count
    cols = min(4, tiles)
    rows = math.ceil(tiles / cols)
    interval = span / tiles
    tile_w = max(240, min(480, 1920 // cols))

    vf = (
        f"{_timestamp_filter(_font())}"
        f"fps=1/{interval:.6f},"
        f"scale={tile_w}:-2,"
        f"tile={cols}x{rows}:margin=6:padding=4:color=#202028"
    )
    out = _out_path(video, f"strip_{start:.1f}-{end:.1f}")
    # -copyts 가 없으면 -ss 로 잘라낸 구간의 pts 가 0부터 다시 시작해서
    # 각인되는 타임스탬프가 원본 시각이 아니라 구간 상대시각이 된다.
    code, log = _run_ffmpeg(
        ["-copyts", "-ss", str(start), "-to", str(end), "-i", str(video),
         "-vf", vf, "-frames:v", "1", str(out)]
    )
    if code != 0 or not out.exists():
        sys.stderr.write(log[-2000:])
        return _fail("구간 대조표 생성 실패")

    print(f"\n{start:.1f}s ~ {end:.1f}s 를 {tiles}칸으로 ({interval:.2f}초 간격)")
    print("구간 대조표 완료:")
    print(out.resolve())
    return 0


# ------------------------------------------------------------ frame/guides


def cmd_frame(args) -> int:
    video = Path(args.video)
    if not video.exists():
        return _fail(f"파일이 없다: {video}")

    at = _parse_time(args.time)
    out = _out_path(video, f"t{at:.2f}".replace(".", "_"))
    code, log = _run_ffmpeg(
        ["-ss", str(at), "-i", str(video), "-frames:v", "1", str(out)]
    )
    if code != 0 or not out.exists():
        sys.stderr.write(log[-2000:])
        return _fail("프레임 추출 실패")
    print(f"\n{at:.2f}s 프레임:")
    print(out.resolve())
    return 0


def cmd_guides(args) -> int:
    """안전영역과 자막 밴드를 덧그린다.

    자막이 밴드 안에 들어와 있는지, 글자가 타이틀 세이프 밖으로
    나갔는지를 눈으로 판정할 수 있게 하는 게 목적이다.
    """
    video = Path(args.video)
    if not video.exists():
        return _fail(f"파일이 없다: {video}")

    at = _parse_time(args.time)
    margin = (1 - TITLE_SAFE) / 2
    font = _font()

    parts = [
        # 타이틀 세이프 (노랑): 이 밖의 글자는 잘릴 수 있다
        f"drawbox=x=iw*{margin}:y=ih*{margin}:"
        f"w=iw*{TITLE_SAFE}:h=ih*{TITLE_SAFE}:color=yellow@0.55:t=2",
        # 자막 밴드 (청록): 자막은 이 안에 있어야 한다
        f"drawbox=x=0:y=ih*{SUBTITLE_BAND_TOP}:w=iw:h=ih*{1 - SUBTITLE_BAND_TOP}:"
        f"color=cyan@0.45:t=2",
        # 세로 중심선 (회색): 구도가 한쪽으로 쏠렸는지
        "drawbox=x=iw/2:y=0:w=1:h=ih:color=white@0.25:t=1",
    ]
    if font:
        # drawtext 의 좌표식에는 iw/ih 가 없다 (drawbox 와 다르다).
        # 입력 프레임 크기는 w/h 로 쓴다.
        parts.append(
            f"drawtext=fontfile='{font}':text='title-safe {int(TITLE_SAFE * 100)}%%':"
            f"x=w*{margin}+8:y=h*{margin}+8:fontsize=22:fontcolor=yellow@0.9"
        )
        parts.append(
            f"drawtext=fontfile='{font}':text='subtitle band':"
            f"x=12:y=h*{SUBTITLE_BAND_TOP}+8:fontsize=22:fontcolor=cyan@0.9"
        )

    out = _out_path(video, f"guides_t{at:.2f}".replace(".", "_"))
    code, log = _run_ffmpeg(
        ["-ss", str(at), "-i", str(video), "-vf", ",".join(parts),
         "-frames:v", "1", str(out)]
    )
    if code != 0 or not out.exists():
        sys.stderr.write(log[-2000:])
        return _fail("가이드 프레임 생성 실패")
    print(f"\n{at:.2f}s + 안전영역 가이드:")
    print(out.resolve())
    return 0


# ------------------------------------------------------------------- main


def main() -> int:
    missing = _need_ffmpeg()
    if missing:
        return _fail(f"{missing} 가 없다. apt-get install ffmpeg / brew install ffmpeg")

    parser = argparse.ArgumentParser(
        prog="qc.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("stats", help="검은 화면 / 정지 구간 / 규격 자동 검사")
    p.add_argument("video")
    p.add_argument("--freeze", type=float, default=4.0,
                   metavar="초", help="이 시간 이상 멈춰 있으면 보고 (기본 4)")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("sheet", help="등간격 프레임 대조표 한 장")
    p.add_argument("video")
    p.add_argument("-g", "--grid", default="4x4", metavar="열x행")
    p.set_defaults(func=cmd_sheet)

    p = sub.add_parser("strip", help="짧은 구간을 촘촘히 뽑은 대조표")
    p.add_argument("video")
    p.add_argument("start")
    p.add_argument("end")
    p.add_argument("-n", "--count", type=int, default=8, metavar="칸수")
    p.set_defaults(func=cmd_strip)

    p = sub.add_parser("frame", help="특정 시각 한 프레임 (원본 해상도)")
    p.add_argument("video")
    p.add_argument("time")
    p.set_defaults(func=cmd_frame)

    p = sub.add_parser("guides", help="안전영역 + 자막 밴드 가이드를 덧그린 프레임")
    p.add_argument("video")
    p.add_argument("time")
    p.set_defaults(func=cmd_guides)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
