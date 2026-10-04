#!/usr/bin/env bash
# We share one Mac, so each person saves under their own name (that's how GitHub credits them).
#
#   ./sync.sh                          get the latest from GitHub
#   ./sync.sh ravi "what I changed"    save + upload YOUR folder's changes, credited to you
#
# Names: amathziah | murali | ravi | pugal
set -e
cd "$(dirname "$0")"

if [ -z "$1" ]; then
  git pull --rebase --autostash
  echo "✅ Up to date."
  exit 0
fi

who="$1"; msg="$2"
case "$who" in
  amathziah) name="Amathziah J";     email="$(git config user.email)";                     paths=(.) ;;
  murali)    name="Murali Madhav C"; email="149486486+HackHeroic@users.noreply.github.com";  paths=(notebooks src) ;;
  ravi)      name="Ravi Yadav";      email="151433762+RAVIYADAV6522@users.noreply.github.com"; paths=(slides) ;;
  pugal)     name="Pugazhendhi J";   email="151515448+pugazhjs9@users.noreply.github.com";   paths=(docs README.md) ;;
  *) echo "Unknown name '$who'. Use: amathziah, murali, ravi or pugal"; exit 1 ;;
esac
if [ -z "$msg" ]; then echo "Add a short note:  ./sync.sh $who \"what you changed\""; exit 1; fi

git add -A -- "${paths[@]}"
if git diff --cached --quiet; then
  echo "Nothing new to save in: ${paths[*]}"
else
  GIT_COMMITTER_NAME="$name" GIT_COMMITTER_EMAIL="$email" \
    git commit -q --author="$name <$email>" -m "$msg"
  echo "Saved as $name: $msg"
fi

if ! git pull --rebase --autostash; then
  git rebase --abort 2>/dev/null || true
  echo "⚠️  GitHub has a conflicting change to the same file. Nothing was uploaded; your work is safe. Tell amathziah."
  exit 1
fi
git push -q
echo "✅ Uploaded."

left="$(git status --short)"
if [ -n "$left" ]; then
  echo
  echo "Not uploaded (other people's folders; they save these under their own name):"
  echo "$left"
fi
