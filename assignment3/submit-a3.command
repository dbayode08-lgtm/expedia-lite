#!/bin/bash
# Double-click AFTER you've checked the app runs. Commits assignment3/ on a new
# branch "assignment3", pushes it to GitHub, writes the commit hash into the three
# reports, and pushes that too. Same flow as A1/A2 ("Add commit hash to report").
cd "$(dirname "$0")/.." || exit 1
set -e
git checkout -b assignment3 2>/dev/null || git checkout assignment3
git add assignment3 README.md handoffs/current.md prompts/a3.md
git commit -m "A3: Steady skills prototype (3.1 design, 3.2 app + safety, 3.3 evaluation)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WiAiqJCDs4aj8jCMBTZ4gp"
HASH=$(git rev-parse --short HEAD)
sed -i '' "s/COMMIT_HASH/$HASH/" assignment3/reports/report-3.1.md assignment3/reports/report-3.2.md assignment3/reports/report-3.3.md
git add assignment3/reports
git commit -m "Add commit hash to A3 reports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WiAiqJCDs4aj8jCMBTZ4gp"
git push -u origin assignment3
rm -f "$HOME/Documents/steady-a3.tar.gz"
echo
echo "Done. Submitted commit: $HASH"
echo "Upload reports/report-3.1.md, report-3.2.md, report-3.3.md to Canvas (each as report.md)."
open assignment3/reports
