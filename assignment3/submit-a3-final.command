#!/bin/bash
# Double-click to push the Part 3.3 update (demo video + report) and put the new commit hash in report-3.3.md.
cd "$(dirname "$0")/.." || exit 1
set -e
git checkout assignment3
git add assignment3
git commit -m "A3 Part 3.3: demo video, report links, AI-use update

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WiAiqJCDs4aj8jCMBTZ4gp"
HASH=$(git rev-parse --short HEAD)
sed -i '' "s/COMMIT_HASH/$HASH/" assignment3/reports/report-3.3.md
git add assignment3/reports/report-3.3.md
git commit -m "Add commit hash to A3 Part 3.3 report

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01WiAiqJCDs4aj8jCMBTZ4gp"
git push
echo
echo "Done. Part 3.3 commit: $HASH"
echo "Upload assignment3/reports/report-3.3.md to Canvas as report.md."
open assignment3/reports
