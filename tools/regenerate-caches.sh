#!/usr/bin/env bash
# Rebuild the three distribution caches from scratch. Run after any push to
# the main branch of a package repository (test_cache_refs_match_the_branch_heads
# fails until then). Needs a rosdistro that parses distribution file format 3
# (rep159-testing/rosdistro, branch rep159). --preclean stores each
# distribution file unmerged: parents are merged when the cache is loaded.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m rosdistro.cli.rosdistro_build_cache --preclean --include-source \
    index-v4.yaml upstream srcext binext
