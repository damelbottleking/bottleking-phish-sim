#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null; then
  echo "Install GitHub CLI: brew install gh && gh auth login"
  exit 1
fi

if [[ ! -d .git ]]; then
  git init -b main
fi

git add .gitignore docs/ templates/ scripts/ data/staff-import-template.csv README.md
git add templates/email-bottleking-update.html templates/landing-page.html
git status

if ! git diff --cached --quiet; then
  git commit -m "$(cat <<'EOF'
Add BottleKing partnership email template and GitHub Pages landing form.

EOF
)"
fi

REPO_NAME="bottleking-phish-sim"
if ! gh repo view "$REPO_NAME" >/dev/null 2>&1; then
  gh repo create "$REPO_NAME" --private --source=. --remote=origin --push
else
  git remote add origin "https://github.com/$(gh api user -q .login)/${REPO_NAME}.git" 2>/dev/null || true
  git push -u origin main
fi

USER=$(gh api user -q .login)
PAGES_URL="https://${USER}.github.io/${REPO_NAME}"

echo ""
echo "Enable GitHub Pages:"
echo "  Repo -> Settings -> Pages -> Build from branch -> main -> /docs"
echo ""
echo "Live form URL will be:"
echo "  ${PAGES_URL}/?rid=USER_ID"
echo ""
echo "Then update .env PHISH_PUBLIC_URL=${PAGES_URL}"
