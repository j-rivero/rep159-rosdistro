# rep159-rosdistro

Index and distribution files of a test harness for
[REP 159](https://github.com/openrobotics/reps/pull/32), the rosdistro
extension proposal, independent of any ROS distribution. Three
distributions:

| distribution | extends | method | packages |
|---|---|---|---|
| `upstream` | — | — | `upstream_a` ◄ `upstream_b` ◄ `upstream_c`; `ament_package` ◄ `ament_cmake_core` ◄ `ros_workspace` |
| `srcext` | `upstream` (this index) | `source_rebuild` | `downstream_src_a` (needs `upstream_c`) |
| `binext` | `upstream` (this index) | `binary_import` | `downstream_bin_a` (needs `upstream_c`) |

`downstream_src_a` and `downstream_bin_a` are the same code: only the way
their distribution extends `upstream` differs. `srcext` rebuilds the upstream
chain from source; `binext` uses the binaries `upstream` releases, installed
under `/opt/ros/upstream`.

`ament_package`, `ament_cmake_core` and `ros_workspace` are copies of the
Lyrical sources ([ament_package](https://github.com/ament/ament_package)
0.18.3, `ament_cmake_core` extracted from
[ament_cmake](https://github.com/ament/ament_cmake) 2.8.8,
[ros_workspace](https://github.com/ros2/ros_workspace) 1.0.3). `upstream`
is `distribution_type: ros2`, so bloom makes each of its other packages
depend on `ros-upstream-ros-workspace`, which installs
`/opt/ros/upstream/setup.sh`.

Every package has a `source:` entry on `main` only; there are no releases
yet, so `binext` cannot be built by a CI job until `upstream` releases
binaries.

Loading these files needs a rosdistro that parses distribution file format 3
and resolves `extends` (from `extends[].index_url` when an entry has one):
`rep159-testing/rosdistro`, branch `rep159`.

- `tools/regenerate-caches.sh`: rebuild the caches after a package push.
- `tools/check_workspaces.py`: the checkout each CI job resolves, through
  `rep159-testing/ros_buildfarm` (branch `rep159`).
- `test/`: structure, cache freshness and extension loading.
