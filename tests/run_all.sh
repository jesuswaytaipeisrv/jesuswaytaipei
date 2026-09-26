#!/usr/bin/env bash
# 跑完整測試套件。不需要網路、不需要 yt-dlp、不會發任何 Telegram、不碰真實 repo 的 git 狀態。
#   bash tests/run_all.sh
set -u
cd "$(dirname "$0")/.."
fail=0
for t in tests/test_heartbeat.py tests/test_git_commit.py tests/test_last_run_state.py; do
  echo "═══ $t ═══"
  if python3 "$t"; then :; else fail=1; fi
  echo
done
if [ "$fail" -eq 0 ]; then
  echo "全部套件通過"
else
  echo "有套件失敗"
fi
exit "$fail"
