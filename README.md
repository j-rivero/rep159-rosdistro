# rep159-rosdistro

Index and distribution files of a test harness for
[REP 159](https://github.com/openrobotics/reps/pull/32), the rosdistro
extension proposal. Three distributions:

| distribution | extends | method | packages |
|---|---|---|---|
| `upstream` | — | — | `upstream_a` ◄ `upstream_b` ◄ `upstream_c` |
| `srcext` | `upstream` (this index) | `source_rebuild` | `downstream_src_a` (needs `upstream_c`) |
| `binext` | `lyrical` (official ROS index) | `binary_import` | `downstream_bin_a` (needs `rcl`) |

Every package has a `source:` entry on `main` only; there are no releases
yet. Lyrical is never copied: `binext` reads the official index and cache.

Loading these files needs a rosdistro that parses distribution file format 3
and loads parents from `extends[].index_url`:
`rep159-testing/rosdistro`, branch `rep159`.

- `tools/regenerate-caches.sh`: rebuild the caches after a package push.
- `tools/check_workspaces.py`: the checkout each CI job resolves, through
  `rep159-testing/ros_buildfarm` (branch `rep159`).
- `test/`: structure, cache freshness and extension loading.
