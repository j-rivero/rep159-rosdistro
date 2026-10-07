"""Load the harness distributions the way ros_buildfarm does.

Needs a rosdistro that parses distribution file format 3 and loads parent
caches from extends[].index_url (rep159-testing/rosdistro, branch rep159).
"""

import copy
import os

import pytest
from rosdistro import get_cached_distribution
from rosdistro import get_index
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_URL = 'file://' + os.path.join(ROOT, 'index-v4.yaml')
UPSTREAM = ('ament_cmake_core', 'ament_package', 'ros_workspace',
            'upstream_a', 'upstream_b', 'upstream_c')


def load(path):
    with open(os.path.join(ROOT, path)) as f:
        return yaml.safe_load(f)


def releases(name):
    return {repo_name for repo_name, repo
            in load('%s/distribution.yaml' % name)['repositories'].items()
            if 'release' in repo}


def upstream_releases():
    return releases('upstream')


def test_srcext_rebuilds_upstream_under_its_own_name():
    dist = get_cached_distribution(get_index(INDEX_URL), 'srcext')
    assert set(dist.source_packages) == set(UPSTREAM) | {'downstream_src_a'}
    assert set(dist.release_packages) == upstream_releases() | releases('srcext')
    upstream = get_cached_distribution(get_index(INDEX_URL), 'upstream')
    for repo_name in UPSTREAM:
        repo = dist.repositories[repo_name]
        assert repo.origin_distro == 'srcext'
        assert repo.source_repository.url == \
            upstream.repositories[repo_name].source_repository.url
        if repo_name in releases('srcext'):
            # Released into srcext with bloom: srcext's own stanza replaces
            # upstream's, and the fork then reports the repository as
            # srcext's own (no extension_method).
            assert repo.extension_method is None
            assert repo.release_repository.tags == {
                'release': 'release/srcext/{package}/{version}'}
        else:
            # Not released into srcext yet: upstream's stanza comes along
            # unchanged, release/upstream/ tags included, while rosdep
            # already names the package ros-srcext-*.
            assert repo.extension_method == 'source_rebuild'


def test_binext_imports_upstream_as_binaries():
    dist = get_cached_distribution(get_index(INDEX_URL), 'binext')
    assert set(dist.source_packages) == set(UPSTREAM) | {'downstream_bin_a'}
    # binext releases only what it owns: overriding a binary_import parent is
    # refused by the fork.
    assert not releases('binext') & set(UPSTREAM)
    assert set(dist.release_packages) == upstream_releases() | releases('binext')
    for repo_name in UPSTREAM:
        repo = dist.repositories[repo_name]
        assert repo.origin_distro == 'upstream'
        assert repo.extension_method == 'binary_import'
    own = dist.repositories['downstream_bin_a']
    assert own.origin_distro == 'binext'
    if 'downstream_bin_a' in releases('binext'):
        assert own.extension_method is None
        assert own.release_repository.tags == {
            'release': 'release/binext/{package}/{version}'}


def _write_index(tmp_path, distributions):
    """Write an index of `{name: (distribution_file, cache)}` in tmp_path."""
    index = {'type': 'index', 'version': 4, 'distributions': {}}
    for name, (dist_data, cache_data) in distributions.items():
        (tmp_path / name).mkdir()
        with open(str(tmp_path / name / 'distribution.yaml'), 'w') as f:
            yaml.safe_dump(dist_data, f)
        with open(str(tmp_path / ('%s-cache.yaml' % name)), 'w') as f:
            yaml.safe_dump(cache_data, f)
        index['distributions'][name] = {
            'distribution': ['%s/distribution.yaml' % name],
            'distribution_cache': '%s-cache.yaml' % name,
            'distribution_status': 'active',
            'distribution_type': 'ros2',
            'python_version': 3,
        }
    with open(str(tmp_path / 'index-v4.yaml'), 'w') as f:
        yaml.safe_dump(index, f)
    return get_index('file://%s' % (tmp_path / 'index-v4.yaml'))


def _files(name):
    return load('%s/distribution.yaml' % name), load('%s-cache.yaml' % name)


def test_unreachable_parent_index_fails_the_load(tmp_path):
    # A parent in another index (extends[].index_url) that cannot be read.
    dist_data, cache_data = copy.deepcopy(_files('binext'))
    bad_url = 'file://%s' % (tmp_path / 'missing' / 'index-v4.yaml')
    dist_data['extends'][0]['index_url'] = bad_url
    cache_data['distribution_file'][0]['extends'][0]['index_url'] = bad_url
    index = _write_index(tmp_path, {'binext': (dist_data, cache_data)})
    with pytest.raises(RuntimeError, match="'upstream', which 'binext' extends"):
        get_cached_distribution(index, 'binext')


@pytest.mark.parametrize('name', ('srcext', 'binext'))
def test_missing_upstream_fails_the_load(tmp_path, name):
    index = _write_index(tmp_path, {name: _files(name)})
    with pytest.raises(
            RuntimeError, match="'upstream', which '%s' extends" % name):
        get_cached_distribution(index, name)
