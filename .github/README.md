# Ignis GStreamer updates

The weekly workflow opens an upstream-release PR before attempting a merge into
its candidate branch. Conflicts leave that PR open. A clean candidate builds the
real muxer and runs `test_id3_metadata_alignment` and
`test_klv_metadata_alignment`. Only a passing candidate can be merged into
`ignis-main`. If the base moves during validation, the workflow stops for a rerun.

The tests check successive metadata access units, including buffers spanning many
transport packets. They assert PES alignment, payload integrity, and timestamp
spacing in both ordinary and constant-bitrate output. The tests were verified to fail when either Ignis muxer fix was removed.
Run locally with Meson, Ninja, a C compiler, Flex/Bison, and GLib development files:

```sh
bash .github/scripts/test-metadata-regressions.sh
```

After merging, the workflow dispatches `update-gstreamer-submodule.yaml` in
`IgnisTechnologies/ignis-livestream`. That workflow builds the full matching base,
runs the muxer and KLV plugin regressions, and merges the submodule PR only on
success. Production continues to use its existing release-tag trigger.

## Activation

- Make `IGNISBOT_GH_ACCESS_TOKEN` available to this repository. Its automation
  identity needs contents, pull-request, and commit-status write access here, plus
  Actions write access to dispatch the livestream workflow. Use this token for
  checkout as well as `gh` so bot-authored updates trigger downstream workflows.
  A classic PAT also needs the `repo` and `workflow` scopes.
- Make `CODEXPOO_SLACK_BOT_TOKEN` available here, with `chat:write` and access to
  `#el-platform` (`C09V4N95Y4Q`).
- Require `ignis-gstreamer-regressions` on `ignis-main` with strict/up-to-date
  status checks. The merge step deliberately stops if this rule is absent.
- Organization ruleset **327630** currently requires an approving review and
  approval after the last push. An organization administrator must arrange a
  scoped review exception for the automation identity while keeping the strict
  regression check enforced. The workflow does not bypass rules or approve its
  own PR. Repository-local settings cannot weaken the inherited organization rule.

Failures post the PR and workflow links to `#el-platform`; merge conflicts also
include the file list. A PR comment records the notification marker, suppressing
repeat Slack alerts for the same release, candidate, base, and failed stage.
If Slack delivery fails, no marker is written so a rerun can retry delivery.
Build/test logs and conflict details are retained as workflow artifacts.

## Rollout order

Land these fork changes first. Use the existing livestream submodule updater to
move its pointer to the revision containing the regression tests and runner.
Then land the livestream image/workflow changes. The new Dockerfile requires
that runner and intentionally fails if the fork regression tests are absent.
Configure the secrets and merge rules before enabling unattended merging.
