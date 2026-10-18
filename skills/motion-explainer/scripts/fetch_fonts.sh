#!/usr/bin/env bash
# Stage the open-source (OFL-1.1) fonts a project needs into <project>/assets/fonts/.
#   bash fetch_fonts.sh <project-dir>
# The film's default face is GenSeki Gothic Bold (源石黑體 粗體, ButTaiwan, OFL-1.1) from the
# official GitHub release (~48 MB zip; only the Bold .otf is kept). theme.json "font" applies it
# to every piece of text. The faces below are what frame workers author with before theming:
# Latin faces come from the @fontsource npm packages (pinned); CJK faces are Noto Sans/Serif TC,
# copied from the system if installed (Windows ships them in C:\Windows\Fonts), otherwise
# downloaded from the google/fonts GitHub repo (variable fonts, renamed to *-VF.ttf).
# Needs bash (Git Bash or WSL on Windows), curl, npm and Python 3 (set PYTHON=... to pick one).
set -euo pipefail
PROJECT="$(cd "${1:-.}" && pwd)"
DEST="$PROJECT/assets/fonts"
TMP="$(mktemp -d)"
mkdir -p "$DEST"
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(sys.version_info < (3, 8))" 2>/dev/null; then PY="$c"; break; fi
  done
fi
[ -n "$PY" ] || { echo "Python 3 not found — set PYTHON=/path/to/python3"; exit 1; }
GENSEKI="https://github.com/ButTaiwan/genseki-font/releases/download/v2.100/GenSekiGothic2TW-otf.zip"
if [ ! -f "$DEST/GenSekiGothic2TW-B.otf" ]; then
  curl -sSL -o "$TMP/genseki.zip" "$GENSEKI"
  "$PY" -c "import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); [open(sys.argv[2]+'/'+n.split('/')[-1],'wb').write(z.read(n)) for n in z.namelist() if n.endswith(('GenSekiGothic2TW-B.otf','SIL_Open_Font_License_1.1.txt'))]" "$TMP/genseki.zip" "$DEST"
  [ -f "$DEST/SIL_Open_Font_License_1.1.txt" ] && mv "$DEST/SIL_Open_Font_License_1.1.txt" "$DEST/OFL-GenSekiGothic.txt"
fi
( cd "$TMP" && npm init -y >/dev/null 2>&1 && npm install --no-audit --no-fund \
    @fontsource/newsreader@5.2.8 @fontsource/dm-mono@5.2.7 @fontsource/hanken-grotesk@5.2.8 >/dev/null )
F="$TMP/node_modules/@fontsource"
cp "$F/newsreader/files/newsreader-latin-400-normal.woff2"       "$DEST/Newsreader-Regular.woff2"
cp "$F/newsreader/files/newsreader-latin-400-italic.woff2"       "$DEST/Newsreader-Italic.woff2"
cp "$F/dm-mono/files/dm-mono-latin-400-normal.woff2"             "$DEST/DMMono-Regular.woff2"
cp "$F/dm-mono/files/dm-mono-latin-500-normal.woff2"             "$DEST/DMMono-Medium.woff2"
for w in 400:Regular 500:Medium 600:SemiBold 700:Bold; do
  cp "$F/hanken-grotesk/files/hanken-grotesk-latin-${w%%:*}-normal.woff2" "$DEST/HankenGrotesk-${w##*:}.woff2"
done
GOOGLE="https://github.com/google/fonts/raw/main/ofl"
for pair in NotoSansTC-VF.ttf:notosanstc/NotoSansTC%5Bwght%5D.ttf NotoSerifTC-VF.ttf:notoseriftc/NotoSerifTC%5Bwght%5D.ttf; do
  name="${pair%%:*}"
  [ -f "$DEST/$name" ] && continue
  for dir in "/c/Windows/Fonts" "$HOME/.local/share/fonts" "/usr/share/fonts/truetype/noto" "/Library/Fonts" "$HOME/Library/Fonts"; do
    if [ -f "$dir/$name" ]; then cp "$dir/$name" "$DEST/"; break; fi
  done
  [ -f "$DEST/$name" ] || curl -sSfL -o "$DEST/$name" "$GOOGLE/${pair#*:}" || echo "! could not get $name — download Noto Sans/Serif TC from https://fonts.google.com/noto into $DEST"
done
rm -rf "$TMP"
ls "$DEST"
