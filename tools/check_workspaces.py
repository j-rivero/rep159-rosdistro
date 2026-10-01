#!/usr/bin/env python3
"""Assert the checkout each CI job resolves from this index.

Runs ros_buildfarm's create_workspace selection (rep159-testing/ros_buildfarm,
branch rep159, on PYTHONPATH) with the rosdistro fork, without cloning.

Usage: check_workspaces.py INDEX_URL
"""

import sys

from ros_buildfarm.scripts.ci.create_workspace import get_repositories_data
from rosdistro import get_cached_distribution
from rosdistro import get_index

# The selection each ci-build file makes, and the repositories it must yield.
# The last one is no ci-build file: binext's parent comes as binaries
# (binary_import), so even a walk of downstream_bin_a's dependencies must not
# check out the upstream repositories.
EXPECTED = [
    ('upstream',
     {'repository_names': ['upstream_a', 'upstream_b', 'upstream_c'],
      'package_names': [], 'package_dependencies': False},
     ['upstream_a', 'upstream_b', 'upstream_c']),
    ('srcext',
     {'repository_names': [], 'package_names': ['downstream_src_a'],
      'package_dependencies': True},
     ['downstream_src_a', 'upstream_a', 'upstream_b', 'upstream_c']),
    ('binext',
     {'repository_names': ['downstream_bin_a'], 'package_names': [],
      'package_dependencies': False},
     ['downstream_bin_a']),
    ('binext',
     {'repository_names': [], 'package_names': ['downstream_bin_a'],
      'package_dependencies': True},
     ['downstream_bin_a']),
]


def main(index_url):
    index = get_index(index_url)
    for distro, selection, expected in EXPECTED:
        data = get_repositories_data(
            get_cached_distribution(index, distro), **selection)
        assert sorted(data) == expected, \
            '%s resolves %s, expected %s' % (distro, sorted(data), expected)
        for name, repo in data.items():
            assert repo == {
                'type': 'git',
                'url': 'https://github.com/rep159-testing/%s.git' % name,
                'version': 'main'}, repo
        print('%s: %s' % (distro, ', '.join(expected)))
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
