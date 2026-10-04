#!/usr/bin/env bash
# Usage:
#   ./sync.sh                                     get the latest from GitHub
#   ./sync.sh "what changed"                      save + upload
#   ./sync.sh "what changed" murali ravi          same, crediting the people who worked on it with you
#
# Names for co-authors: murali | ravi | pugal
set -e
cd "$(dirname "$0")"

if [ -z "$1" ]; then
  git pull --rebase --autostash
  echo "✅ Up to date."
  exit 0
fi

msg="$1"; title="$1"; shift
trailers=""
for who in "$@"; do
  case "$who" in
    murali) trailers+=$'\nCo-authored-by: Murali Madhav C <149486486+HackHeroic@users.noreply.github.com>' ;;
    ravi)   trailers+=$'\nCo-authored-by: Ravi Yadav <151433762+RAVIYADAV6522@users.noreply.github.com>' ;;
    pugal)  trailers+=$'\nCo-authored-by: Pugazhendhi J <151515448+pugazhjs9@users.noreply.github.com>' ;;
    *) echo "Unknown name '$who'. Use: murali, ravi or pugal"; exit 1 ;;
  esac
done
[ -n "$trailers" ] && msg="$msg"$'\n'"$trailers"

git add -A
if git diff --cached --quiet; then
  echo "Nothing new to save."
else
  git commit -q -m "$msg"
  echo "Saved: $title"
fi

if ! git pull --rebase --autostash; then
  git rebase --abort 2>/dev/null || true
  echo "⚠️  GitHub has a conflicting change. Nothing was uploaded; your work is safe."
  exit 1
fi
git push -q
echo "✅ Uploaded."
