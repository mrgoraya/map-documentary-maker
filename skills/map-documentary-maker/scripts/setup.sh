#!/usr/bin/env bash
# One-time setup for map-documentary-maker. Safe to run again.
# Makes a Python 3.12 environment and downloads fonts + Natural Earth map data into the cache.
#   bash setup.sh            everything (about 2.5 GB with the voice and speech models)
#   bash setup.sh --no-voice skip Kokoro and Whisper (bring your own voiceover + timestamps)
set -euo pipefail
CACHE="${DOC_CACHE:-$HOME/.cache/map-documentary-maker}"
VENV="$CACHE/venv"
VOICE=1; [[ "${1:-}" == "--no-voice" ]] && VOICE=0
mkdir -p "$CACHE/fonts" "$CACHE/ne"

need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING: $1. $2"; exit 1; }; }
need ffmpeg "Install it: macOS 'brew install ffmpeg', Windows 'winget install ffmpeg', Linux 'sudo apt install ffmpeg'."
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv (Python manager)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [[ ! -x "$VENV/bin/python" ]]; then uv venv --python 3.12 "$VENV"; fi
PKGS="numpy opencv-python-headless pillow geopandas shapely rasterio soundfile requests"
[[ $VOICE == 1 ]] && PKGS="$PKGS kokoro faster-whisper"
uv pip install --python "$VENV/bin/python" $PKGS
# Kokoro's English phonemizer needs this spaCy model; it can't download it by itself inside a uv env
[[ $VOICE == 1 ]] && uv pip install --python "$VENV/bin/python" \
  "en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"

# Fonts (all SIL Open Font License, from the Google Fonts repository)
GF=https://raw.githubusercontent.com/google/fonts/main/ofl
get() { [[ -s "$2" ]] || curl -fL --retry 3 -o "$2" "$1"; }
get "$GF/bebasneue/BebasNeue-Regular.ttf" "$CACHE/fonts/BebasNeue.ttf"
get "$GF/inter/Inter%5Bopsz,wght%5D.ttf" "$CACHE/fonts/Inter.ttf"
get "$GF/sourceserif4/SourceSerif4%5Bopsz,wght%5D.ttf" "$CACHE/fonts/SourceSerif4.ttf"

# Natural Earth (public domain): country borders + grey shaded relief
NE=https://naciscdn.org/naturalearth
fetch_ne() {  # url, folder name
  if [[ ! -d "$CACHE/ne/$2" ]]; then
    get "$1" "$CACHE/ne/$2.zip"
    mkdir -p "$CACHE/ne/$2" && unzip -oq "$CACHE/ne/$2.zip" -d "$CACHE/ne/$2" && rm "$CACHE/ne/$2.zip"
  fi
}
fetch_ne "$NE/10m/cultural/ne_10m_admin_0_countries.zip" ne_10m_admin_0_countries
fetch_ne "$NE/10m/raster/GRAY_HR_SR_OB_DR.zip" GRAY_HR_SR_OB_DR

"$VENV/bin/python" - <<'EOF'
import cv2, geopandas, rasterio, PIL; print("render libraries OK")
try:
    import kokoro, faster_whisper; print("voice libraries OK")
except ImportError:
    print("voice libraries skipped")
EOF
echo
echo "Setup done. Python for every script: $VENV/bin/python"
