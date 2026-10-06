#!/usr/bin/env bash
# Rebuild the three distribution caches from scratch. CI runs this on every
# push and pull request, and commits the result to main (.github/workflows/
# ci.yaml), so a change to a distribution file or a push to a package
# repository's main only needs a CI run. Needs a rosdistro that parses
# distribution file format 3 (rep159-testing/rosdistro, branch rep159).
# --preclean stores each distribution file unmerged: parents are merged when
# the cache is loaded.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m rosdistro.cli.rosdistro_build_cache --preclean --include-source \
    index-v4.yaml upstream srcext binext
# rosdistro_build_cache stamps the current time in the gzip header; recompress
# without it so an unchanged cache gives an unchanged .gz.
for name in upstream srcext binext; do
    gzip -n -9 -c "$name-cache.yaml" > "$name-cache.yaml.gz"
done
