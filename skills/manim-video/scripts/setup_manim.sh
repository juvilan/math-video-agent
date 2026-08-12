#!/usr/bin/env bash
# Manim CE + LaTeX + ffmpeg + 한글 폰트 설치.
#
#   bash setup_manim.sh          # 전부 설치
#   bash setup_manim.sh --no-tex # LaTeX 빼고 (수식 없이 Text만 쓸 때)
#
# 설치 후 반드시:  python3 mv.py check
set -euo pipefail

WITH_TEX=1
[[ "${1:-}" == "--no-tex" ]] && WITH_TEX=0

log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

OS="$(uname -s)"

if [[ "$OS" == "Darwin" ]]; then
  command -v brew >/dev/null || { echo "Homebrew가 필요하다: https://brew.sh"; exit 1; }

  log "ffmpeg / cairo / pango"
  brew install ffmpeg cairo pango pkg-config

  log "한글 폰트"
  brew install --cask font-nanum-gothic || true

  if [[ $WITH_TEX == 1 ]]; then
    log "LaTeX (MacTeX, 수 GB — 오래 걸린다)"
    brew install --cask mactex-no-gui
    echo "설치 후 새 셸을 열거나: eval \"\$(/usr/libexec/path_helper)\""
  fi

elif [[ "$OS" == "Linux" ]]; then
  SUDO=""
  [[ $EUID -ne 0 ]] && SUDO="sudo"

  if ! command -v apt-get >/dev/null; then
    echo "apt 계열이 아니다. 아래를 배포판 패키지 매니저로 직접 설치할 것:"
    echo "  ffmpeg, cairo, pango, texlive(+latex-extra, science), dvisvgm, 나눔/Noto CJK 폰트"
    exit 1
  fi

  log "apt 갱신"
  $SUDO apt-get update -qq

  log "빌드 의존성 / ffmpeg"
  $SUDO apt-get install -y --no-install-recommends \
    build-essential python3-dev pkg-config \
    libcairo2-dev libpango1.0-dev ffmpeg

  log "한글 폰트"
  $SUDO apt-get install -y --no-install-recommends fonts-nanum fonts-noto-cjk
  fc-cache -f >/dev/null 2>&1 || true

  if [[ $WITH_TEX == 1 ]]; then
    log "LaTeX (수 GB — 오래 걸린다)"
    $SUDO apt-get install -y --no-install-recommends \
      texlive texlive-latex-extra texlive-latex-recommended \
      texlive-fonts-extra texlive-science dvisvgm
  fi

else
  echo "지원하지 않는 OS: $OS"
  echo "Windows는 Chocolatey로: choco install ffmpeg miktex"
  exit 1
fi

log "Python 패키지"
python3 -m pip install --upgrade pip
python3 -m pip install "manim>=0.18" scipy numpy

log "점검"
python3 "$(dirname "$0")/mv.py" check
