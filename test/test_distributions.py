"""Structure and cache checks on the REP-159 harness distributions.

Reads the YAML files directly; needs no rosdistro library. The ref check
needs network access to GitHub.
"""

import gzip
import os
import subprocess

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISTROS = ('upstream', 'srcext', 'binext')
REPOSITORIES = {
    'upstream': {'upstream_a', 'upstream_b', 'upstream_c'},
    'srcext': {'downstream_src_a'},
    'binext': {'downstream_bin_a'},
}
EXTENDS = {
    'upstream': [],
    # No index_url: REP 159 then looks in this same index.
    'srcext': [
        {'distro_name': 'upstream', 'extension_method': 'source_rebuild'}],
    'binext': [
        {'distro_name': 'upstream', 'extension_method': 'binary_import'}],
}


def load(path):
    with open(os.path.join(ROOT, path)) as f:
        return yaml.safe_load(f)


def distribution_file(name):
    return load(os.path.join(name, 'distribution.yaml'))


def cache(name):
    with gzip.open(os.path.join(ROOT, name + '-cache.yaml.gz'), 'rt') as f:
        return yaml.safe_load(f)


def test_index_lists_exactly_the_three_distributions():
    index = load('index-v4.yaml')
    assert index['version'] == 4
    assert set(index['distributions']) == set(DISTROS)
    for name, entry in index['distributions'].items():
        assert entry['distribution'] == ['%s/distribution.yaml' % name]
        assert entry['distribution_cache'] == '%s-cache.yaml.gz' % name


@pytest.mark.parametrize('name', DISTROS)
def test_repositories_are_source_only_on_main(name):
    repositories = distribution_file(name)['repositories']
    assert set(repositories) == REPOSITORIES[name]
    for repo_name, repo in repositories.items():
        assert repo == {'source': {
            'type': 'git',
            'url': 'https://github.com/rep159-testing/%s.git' % repo_name,
            'version': 'main'}}


@pytest.mark.parametrize('name', DISTROS)
def test_extends(name):
    assert distribution_file(name).get('extends', []) == EXTENDS[name]


@pytest.mark.parametrize('name', DISTROS)
def test_format_and_platforms(name):
    data = distribution_file(name)
    assert (data['type'], data['version']) == ('distribution', 3)
    assert data['release_platforms'] == {'ubuntu': ['resolute']}


@pytest.mark.parametrize('name', DISTROS)
def test_cache_embeds_the_unmerged_distribution_file(name):
    # Index format 3+ lists distribution files, so the cache holds a list.
    assert cache(name)['distribution_file'] == [distribution_file(name)]


@pytest.mark.parametrize('name', DISTROS)
def test_cache_holds_every_source_package_and_no_release(name):
    data = cache(name)
    assert set(data['source_repo_package_xmls']) == REPOSITORIES[name]
    assert data['release_package_xmls'] == {}


@pytest.mark.parametrize('name', DISTROS)
def test_compressed_cache_matches_the_plain_cache(name):
    with open(os.path.join(ROOT, name + '-cache.yaml'), 'rb') as f:
        plain = f.read()
    with gzip.open(os.path.join(ROOT, name + '-cache.yaml.gz'), 'rb') as f:
        assert f.read() == plain


@pytest.mark.parametrize('name', DISTROS)
def test_cache_refs_match_the_branch_heads(name):
    # A push to a package's main without regenerating the caches leaves
    # stale package.xml files behind; regenerate with
    # tools/regenerate-caches.sh.
    for repo_name, data in cache(name)['source_repo_package_xmls'].items():
        url = 'https://github.com/rep159-testing/%s.git' % repo_name
        head = subprocess.check_output(
            ['git', 'ls-remote', url, 'refs/heads/main'], text=True).split()[0]
        assert data['_ref'] == head, \
            '%s cache is at %s, main is at %s' % (repo_name, data['_ref'], head)
