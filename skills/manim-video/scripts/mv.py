#!/usr/bin/env python3
"""mv — Manim 영상 제작 루프를 위한 얇은 CLI 래퍼.

manim CLI를 직접 쳐도 되지만, 이 래퍼는 두 가지를 해준다:
  1. 프리뷰/최종 품질 플래그를 헷갈리지 않게 고정
  2. 출력 파일의 실제 경로를 마지막 줄에 단독으로 출력
     → Claude가 그 경로를 바로 Read 툴로 열어서 눈으로 확인할 수 있다

사용법:
    mv.py check
    mv.py scenes  <file.py>
    mv.py sketch  <file.py> [-s A,B,C]           비트별 스틸을 한 판으로 (승인용)
    mv.py layout  <file.py> <SceneName>          이미지 없이 배치만 텍스트로 검사
    mv.py still   <file.py> <SceneName> [-n 3,5]
    mv.py preview <file.py> <SceneName>
    mv.py final   <file.py> <SceneName> [--4k] [--transparent]
    mv.py join    <out.mp4> <a.mp4> <b.mp4> ...  씬 이어붙이기 (오디오 정규화)
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

FILE_READY = re.compile(r"File ready at[\s'\"]*(.+?)['\"]?\s*$", re.MULTILINE)


# ----------------------------------------------------------------- check


def _which(name: str) -> str | None:
    return shutil.which(name)


def _korean_fonts() -> list[str]:
    if not _which("fc-list"):
        return []
    try:
        out = subprocess.run(
            ["fc-list", ":lang=ko", "family"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return []
    names: set[str] = set()
    for line in out.splitlines():
        for part in line.split(","):
            part = part.strip()
            if part:
                names.add(part)
    return sorted(names)


def cmd_check(_args) -> int:
    checks: list[tuple[str, bool, str]] = []

    try:
        import manim  # noqa: F401
        checks.append(("manim (python)", True, getattr(manim, "__version__", "?")))
    except ImportError:
        checks.append(("manim (python)", False, "pip install manim"))

    for tool, hint in [
        ("manim", "pip install manim"),
        ("ffmpeg", "apt-get install ffmpeg  /  brew install ffmpeg"),
        ("latex", "apt-get install texlive texlive-latex-extra texlive-science"),
        ("dvisvgm", "apt-get install dvisvgm"),
    ]:
        path = _which(tool)
        checks.append((tool, path is not None, path or hint))

    try:
        import scipy  # noqa: F401
        checks.append(("scipy", True, scipy.__version__))
    except ImportError:
        checks.append(("scipy", False, "pip install scipy   (ODE 템플릿에 필요)"))

    fonts = _korean_fonts()
    checks.append((
        "한글 폰트",
        bool(fonts),
        ", ".join(fonts[:5]) if fonts else "apt-get install fonts-nanum fonts-noto-cjk",
    ))

    def display_width(text: str) -> int:
        # 한글은 터미널에서 두 칸을 차지한다
        return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)

    width = max(display_width(name) for name, _, _ in checks)
    failed = 0
    for name, ok, detail in checks:
        mark = "OK  " if ok else "MISS"
        if not ok:
            failed += 1
        pad = " " * (width - display_width(name))
        print(f"[{mark}] {name}{pad}  {detail}")

    if failed:
        print(f"\n{failed}개가 빠져 있다. 위 설치 명령을 실행하거나 "
              f"scripts/setup_manim.sh 를 돌린다.", file=sys.stderr)
        return 1

    print("\n환경 정상. 한글 렌더는 실제 스틸을 눈으로 확인할 것 "
          "(폰트가 없으면 에러 없이 네모로 나온다).")
    return 0


# ---------------------------------------------------------------- scenes


def cmd_scenes(args) -> int:
    """파일 안의 Scene 클래스 이름을 나열한다. 렌더 없이 텍스트만 본다."""
    source = Path(args.file).read_text(encoding="utf-8")
    names = re.findall(
        r"^class\s+(\w+)\s*\(\s*[\w\s,.]*Scene[\w\s,.]*\)\s*:", source, re.MULTILINE
    )
    if not names:
        print("Scene 클래스를 찾지 못했다.", file=sys.stderr)
        return 1
    for name in names:
        print(name)
    return 0


# ---------------------------------------------------------------- render


def _run(cmd: list[str]) -> tuple[int, str]:
    print("$ " + " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stderr.write(proc.stderr)
    sys.stdout.write(proc.stdout)
    return proc.returncode, proc.stdout + proc.stderr


def _run_ffmpeg(args: list[str]) -> tuple[int, str]:
    cmd = ["ffmpeg", "-hide_banner", "-y", *args]
    print("$ " + " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stderr


def _find_output(log: str, source: Path, scene: str, exts: tuple[str, ...]) -> str | None:
    matches = FILE_READY.findall(log)
    for candidate in reversed(matches):
        candidate = candidate.strip()
        if candidate.endswith(exts) and os.path.exists(candidate):
            return os.path.abspath(candidate)

    # 폴백: media 디렉터리에서 가장 최근 파일
    stem = source.stem
    found: list[str] = []
    for ext in exts:
        found += glob.glob(f"media/**/{stem}/**/{scene}*{ext}", recursive=True)
    if found:
        return os.path.abspath(max(found, key=os.path.getmtime))
    return None


def _uses_sound(source: Path) -> bool:
    try:
        text = source.read_text(encoding="utf-8")
    except OSError:
        return False
    return "add_sound(" in text or ".sfx(" in text


def _render(args, extra: list[str], exts: tuple[str, ...], label: str) -> int:
    source = Path(args.file)
    if not source.exists():
        print(f"파일이 없다: {source}", file=sys.stderr)
        return 1

    # 캐시가 켜져 있으면 캐시된 애니메이션은 skip_animations=True 로 돌고,
    # Scene.add_sound 가 그 플래그를 보고 **조용히 return** 한다. 결과는
    # 에러 없이 소리만 빠진 영상. 소리를 쓰는 파일은 캐시를 끈다.
    if _uses_sound(source) and "--disable_caching" not in extra:
        extra = [*extra, "--disable_caching"]
        print("(효과음이 있어 캐시를 끈다 — 캐시된 애니메이션에는 소리가 안 붙는다)",
              file=sys.stderr)

    cmd = ["manim", *extra, str(source), args.scene]
    if getattr(args, "n", None):
        cmd[1:1] = ["-n", args.n]

    code, log = _run(cmd)
    if code != 0:
        print(f"\n{label} 렌더 실패. 위 에러를 읽고, 막히면 "
              f"references/troubleshooting.md 를 본다.", file=sys.stderr)
        return code

    out = _find_output(log, source, args.scene, exts)
    if out is None:
        print("\n렌더는 됐는데 출력 파일을 못 찾았다. media/ 아래를 직접 확인한다.",
              file=sys.stderr)
        return 0

    print(f"\n{label} 완료:")
    print(out)  # ← 마지막 줄은 항상 경로만. Read 툴로 바로 열 수 있게.
    return 0


def cmd_still(args) -> int:
    """마지막 프레임 PNG. 가장 빠른 확인 수단 — 구도/겹침/색을 눈으로 본다."""
    return _render(args, ["-s", "-ql", "--format", "png"], (".png",), "스틸")


def cmd_preview(args) -> int:
    """480p15 동영상. 타이밍 확인용."""
    return _render(args, ["-ql"], (".mp4", ".mov"), "프리뷰")


def cmd_final(args) -> int:
    quality = "-qk" if args.uhd else "-qh"
    extra = [quality]
    exts: tuple[str, ...] = (".mp4",)
    if args.transparent:
        extra += ["-t"]
        exts = (".mov",)
    label = "4K 최종" if args.uhd else "1080p 최종"
    return _render(args, extra, exts, label)


# ------------------------------------------------------------------ sketch


def _label_still(src: Path, dst: Path, label: str, width: int) -> bool:
    """스틸 한 장에 씬 이름을 각인하고 타일 크기로 맞춘다."""
    font = None
    for candidate in (
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if os.path.exists(candidate):
            font = candidate
            break

    vf = f"scale={width}:-2"
    if font:
        safe = label.replace(":", r"\:").replace("'", "")
        vf += (
            f",drawtext=fontfile='{font}':text='{safe}':"
            f"x=10:y=10:fontsize=22:fontcolor=white:"
            f"box=1:boxcolor=black@0.7:boxborderw=8"
        )
    code, log = _run_ffmpeg(["-i", str(src), "-vf", vf, "-frames:v", "1", str(dst)])
    return code == 0 and dst.exists()


def cmd_sketch(args) -> int:
    """비트별 정지 화면을 한 판으로 묶어 **코딩을 마치기 전에** 보여준다.

    제작자가 텍스트 콘티가 아니라 실제 그림을 보고 판단할 수 있게
    하는 게 목적이다. 여기서 "구도가 아니다"가 나오면 버리는 코드가
    거의 없다. 완성본을 보고 나서 말하면 전부 다시 써야 한다.
    """
    source = Path(args.file)
    if not source.exists():
        return _fail(f"파일이 없다: {source}")

    if args.scenes:
        scenes = [s.strip() for s in args.scenes.split(",") if s.strip()]
    else:
        text = source.read_text(encoding="utf-8")
        scenes = re.findall(
            r"^class\s+(\w+)\s*\(\s*[\w\s,.]*Scene[\w\s,.]*\)\s*:",
            text, re.MULTILINE,
        )
    if not scenes:
        return _fail("Scene 클래스를 찾지 못했다")

    work = source.parent / "media" / "sketch"
    work.mkdir(parents=True, exist_ok=True)
    for old in work.glob("*.png"):
        old.unlink()

    cols = min(3, len(scenes))
    rows = math.ceil(len(scenes) / cols)
    tile_w = 640 if cols <= 2 else 480

    tiles: list[Path] = []
    for index, scene in enumerate(scenes):
        code, log = _run(
            ["manim", "-s", "-ql", "--format", "png", "--disable_caching",
             str(source), scene]
        )
        if code != 0:
            print(f"  {scene}: 렌더 실패 — 건너뛴다", file=sys.stderr)
            continue
        still = _find_output(log, source, scene, (".png",))
        if still is None:
            print(f"  {scene}: 출력 파일을 못 찾았다 — 건너뛴다", file=sys.stderr)
            continue
        dst = work / f"{index:03d}.png"
        if _label_still(Path(still), dst, f"{index + 1}. {scene}", tile_w):
            tiles.append(dst)

    if not tiles:
        return _fail("스틸을 한 장도 못 만들었다")

    # 번호를 다시 매겨 image2 demuxer 가 연속으로 읽게 한다
    for position, path in enumerate(sorted(tiles)):
        target = work / f"tile{position:03d}.png"
        if path != target:
            path.rename(target)

    out = source.parent / f"{source.stem}_sketch.png"
    code, log = _run_ffmpeg(
        ["-framerate", "1", "-i", str(work / "tile%03d.png"),
         "-vf", f"tile={cols}x{rows}:margin=8:padding=6:color=#202028",
         "-frames:v", "1", str(out)]
    )
    for leftover in work.glob("*.png"):
        leftover.unlink()
    if code != 0 or not out.exists():
        sys.stderr.write(log[-1500:])
        return _fail("스틸 판 생성 실패")

    print(f"\n비트 {len(tiles)}개를 {cols}x{rows} 판으로 묶었다.")
    print("이걸 제작자에게 보여주고 **구도·색·밀도**를 확인받은 뒤 코딩을 마무리한다.")
    print(out.resolve())
    return 0


# ------------------------------------------------------------------ layout


def cmd_layout(args) -> int:
    """씬을 돌리되 **이미지를 만들지 않고** 배치 문제만 텍스트로 받는다.

    scene_base.MathScene 을 상속한 씬에서 동작한다 (MV_LAYOUT=1 을 켜면
    self.play 마다 좌표를 검사한다). 스틸 PNG를 Read 하는 것보다 훨씬
    싸므로, 눈으로 볼 필요가 있는지 여기서 먼저 걸러낸다.
    """
    source = Path(args.file)
    if not source.exists():
        return _fail(f"파일이 없다: {source}")

    env = dict(os.environ, MV_LAYOUT="1")
    cmd = ["manim", "-ql", "-s", "--format", "png",
           "--disable_caching", str(source), args.scene]
    print("$ MV_LAYOUT=1 " + " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

    lines = [l for l in proc.stderr.splitlines() if l.startswith("[layout]")]
    sfx_missing = [l for l in proc.stderr.splitlines() if l.startswith("[sfx]")]

    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-2000:])
        return _fail("\n씬 실행 실패. 배치 이전에 코드가 안 돈다.")

    for line in sfx_missing:
        print(line)

    if not lines:
        print("배치 문제 없음 (화면 밖 / title-safe 이탈 / 글자 겹침 기준).")
        print("색 대비·의미·움직임은 여기서 안 잡힌다. 필요하면 still 로 본다.")
        return 0

    # 같은 문제가 여러 play 에 걸쳐 반복되면 한 줄로 접는다
    grouped: dict[str, list[str]] = {}
    for line in lines:
        _, label, problem = line.split(" ", 2)
        grouped.setdefault(problem, []).append(label)

    print(f"배치 문제 {len(grouped)}종:\n")
    for problem, labels in grouped.items():
        span = labels[0] if len(labels) == 1 else f"{labels[0]}~{labels[-1]}"
        print(f"  [{span}] {problem}")
    print("\n고친 뒤 다시 돌린다. 이미지는 이게 통과한 다음에 본다.")
    return 1


# -------------------------------------------------------------------- join


def _has_audio(video: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True,
    )
    return bool(out.stdout.strip())


def cmd_join(args) -> int:
    """씬 mp4 를 순서대로 이어붙인다.

    그냥 `ffmpeg -f concat -c copy` 로 붙이면 **오디오가 조용히 사라진다**:
    첫 파일에 오디오 트랙이 없으면 뒤 파일들의 소리가 통째로 버려지고
    경고조차 나오지 않는다. 그래서 붙이기 전에 모든 입력에 오디오
    트랙을 만들어 길이를 영상에 맞춘다.
    """
    out = Path(args.output)
    inputs = [Path(p) for p in args.inputs]
    missing = [str(p) for p in inputs if not p.exists()]
    if missing:
        return _fail("파일이 없다: " + ", ".join(missing))
    if len(inputs) < 2:
        return _fail("두 개 이상을 줘야 한다")

    work = out.parent / ".mv_join"
    work.mkdir(parents=True, exist_ok=True)
    normalized: list[Path] = []

    for i, src in enumerate(inputs):
        dst = work / f"{i:03d}_{src.stem}.mp4"
        if _has_audio(src):
            # 오디오가 영상보다 짧으면 이어붙일 때 뒤가 밀린다. 무음으로 채운다.
            cmd = ["-i", str(src), "-c:v", "copy",
                   "-af", "apad", "-c:a", "aac", "-ar", "44100", "-ac", "2",
                   "-shortest", str(dst)]
        else:
            cmd = ["-i", str(src),
                   "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                   "-c:v", "copy", "-c:a", "aac", "-shortest", str(dst)]
        code, log = _run_ffmpeg(cmd)
        if code != 0:
            sys.stderr.write(log[-1500:])
            return _fail(f"오디오 정규화 실패: {src}")
        normalized.append(dst)

    listing = work / "concat.txt"
    listing.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in normalized), encoding="utf-8")

    code, log = _run_ffmpeg(
        ["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(out)])
    if code != 0:
        sys.stderr.write(log[-1500:])
        return _fail("이어붙이기 실패")

    for path in normalized:
        path.unlink(missing_ok=True)
    listing.unlink(missing_ok=True)
    try:
        work.rmdir()
    except OSError:
        pass

    duration = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(out)],
        capture_output=True, text=True,
    ).stdout.strip()
    print(f"\n{len(inputs)}개 씬을 이어붙였다 ({float(duration):.2f}s):")
    print(out.resolve())
    return 0


# ------------------------------------------------------------------ main


def main() -> int:
    parser = argparse.ArgumentParser(prog="mv.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="manim/ffmpeg/latex/폰트 환경 점검").set_defaults(func=cmd_check)

    p = sub.add_parser("scenes", help="파일 안의 Scene 클래스 나열")
    p.add_argument("file")
    p.set_defaults(func=cmd_scenes)

    for name, fn, help_text in [
        ("still", cmd_still, "마지막 프레임 PNG (구도 확인)"),
        ("preview", cmd_preview, "480p15 mp4 (타이밍 확인)"),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("file")
        p.add_argument("scene")
        p.add_argument("-n", metavar="A[,B]",
                       help="A번째 애니메이션부터 (B번째까지)만 렌더")
        p.set_defaults(func=fn)

    p = sub.add_parser("sketch", help="비트별 스틸을 한 판으로 (제작자 승인용)")
    p.add_argument("file")
    p.add_argument("-s", "--scenes", metavar="A,B,C",
                   help="이 씬들만. 생략하면 파일 안 전부")
    p.set_defaults(func=cmd_sketch)

    p = sub.add_parser("layout", help="이미지 없이 배치만 텍스트로 검사 (제일 쌈)")
    p.add_argument("file")
    p.add_argument("scene")
    p.set_defaults(func=cmd_layout)

    p = sub.add_parser("join", help="씬 mp4 이어붙이기 (오디오 정규화 포함)")
    p.add_argument("output")
    p.add_argument("inputs", nargs="+")
    p.set_defaults(func=cmd_join)

    p = sub.add_parser("final", help="1080p60 또는 4K60 최종 렌더")
    p.add_argument("file")
    p.add_argument("scene")
    p.add_argument("--4k", dest="uhd", action="store_true", help="4K60으로 렌더")
    p.add_argument("--transparent", action="store_true",
                   help="투명 배경 .mov (편집 툴 오버레이용)")
    p.set_defaults(func=cmd_final)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
