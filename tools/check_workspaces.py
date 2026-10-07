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
# The binext walk of downstream_bin_a's dependencies is no ci-build file:
# binext's parent comes as binaries (binary_import), so even that walk must not
# check out the upstream repositories. Neither are the last three: they pin the
# release tags of ament_package, which srcext releases itself (release/srcext/)
# while binext keeps upstream's (release/upstream/).
UPSTREAM = ['ament_cmake_core', 'ament_package', 'ros_workspace',
            'upstream_a', 'upstream_b', 'upstream_c']
EXPECTED = [
    # upstream/ci-nightly-release.yaml
    ('upstream',
     {'repository_names': ['upstream_a', 'upstream_b', 'upstream_c'],
      'package_names': [], 'package_dependencies': False},
     ['upstream_a', 'upstream_b', 'upstream_c']),
    # upstream/ci-source-branches.yaml: every repository from main
    ('upstream',
     {'repository_names': UPSTREAM, 'package_names': [],
      'package_dependencies': False},
     UPSTREAM),
    # upstream/ci-release-branches.yaml: the walk from the two leaves reaches
    # every package, each at its release/upstream/ tag
    ('upstream',
     {'repository_names': [], 'package_names': ['upstream_c', 'ros_workspace'],
      'package_dependencies': True},
     UPSTREAM),
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
] + [
    (distro,
     {'repository_names': [], 'package_names': ['ament_package'],
      'package_dependencies': False},
     ['ament_package'])
    for distro in ('upstream', 'srcext', 'binext')
]


def source_checkout(name):
    return {
        'type': 'git',
        'url': 'https://github.com/rep159-testing/%s.git' % name,
        'version': 'main'}


# The release stanza bloom writes for a track named after the distribution.
# srcext (source_rebuild) inherits upstream's stanza, release/upstream/ tags
# included, until it releases the repository itself.
def release_checkout(dist, distro, name):
    repo = dist.repositories[name]
    tag_distro = distro if getattr(repo, 'extension_method', None) is None \
        else 'upstream'
    return {
        'type': 'git',
        'url': 'https://github.com/rep159-testing/%s-release.git' % name,
        'version': 'release/%s/%s/%s' % (
            tag_distro, name, repo.release_repository.version)}


def main(index_url):
    index = get_index(index_url)
    for distro, selection, expected in EXPECTED:
        dist = get_cached_distribution(index, distro)
        data = get_repositories_data(dist, **selection)
        assert sorted(data) == expected, \
            '%s resolves %s, expected %s' % (distro, sorted(data), expected)
        # A named repository comes from its source entry. A walked package
        # comes from its release, if it has one. Every repository holds one
        # package of the same name.
        for name, repo in data.items():
            if name in selection['repository_names'] or \
                    name not in dist.release_packages:
                want = source_checkout(name)
            else:
                want = release_checkout(dist, distro, name)
            assert repo == want, '%s: %s checks out %s, expected %s' % (
                distro, name, repo, want)
        print('%s: %s' % (distro, ', '.join(expected)))
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
