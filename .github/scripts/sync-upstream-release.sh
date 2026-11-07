#!/usr/bin/env bash
set -euo pipefail

MINIMUM_RELEASE="1.30.0"
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git fetch origin ignis-main:refs/remotes/origin/ignis-main
git fetch --force https://github.com/GStreamer/gstreamer.git "+refs/tags/*:refs/tags/upstream/*"
RELEASE="$(git for-each-ref --format='%(refname:strip=3)' refs/tags/upstream/ |
  awk -F '[.]' '$0 ~ /^[0-9]+\.[0-9]+\.[0-9]+$/ && $2 % 2 == 0' | sort -V | tail -n 1)"
if [ -z "$RELEASE" ] || [ "$(printf '%s\n%s\n' "$MINIMUM_RELEASE" "$RELEASE" | sort -V | head -n 1)" != "$MINIMUM_RELEASE" ]; then
  echo "No supported stable release found"
  exit 0
fi
TAG_REF="refs/tags/upstream/$RELEASE"
if git merge-base --is-ancestor "$TAG_REF" origin/ignis-main; then
  echo "GStreamer $RELEASE is already included in ignis-main"
  exit 0
fi
BASE_SHA="$(git rev-parse origin/ignis-main)"
BRANCH="automation/sync-upstream-$RELEASE"
echo "release=$RELEASE" >> "$GITHUB_OUTPUT"
echo "base_sha=$BASE_SHA" >> "$GITHUB_OUTPUT"

# Publish the upstream head before trying the merge, so conflicts still have a PR.
# Reuse an existing branch to preserve any resolutions made by a maintainer.
EXISTING="$(git ls-remote --heads origin "$BRANCH")"
if [ -n "$EXISTING" ]; then
  git fetch origin "$BRANCH"
  git switch -C "$BRANCH" FETCH_HEAD
else
  git switch -c "$BRANCH" "$TAG_REF"
  git push -u origin "$BRANCH"
fi
PR="$(gh pr list --repo "$GITHUB_REPOSITORY" --state open --head "$BRANCH" --base ignis-main --json url --jq '.[0].url // empty')"
if [ -z "$PR" ]; then
  PR="$(gh pr create --repo "$GITHUB_REPOSITORY" --base ignis-main --head "$BRANCH" \
    --title "Sync upstream GStreamer $RELEASE" \
    --body "Validates upstream GStreamer $RELEASE with the Ignis MPEG-TS changes before automatic merging.")"
fi
echo "pr=$PR" >> "$GITHUB_OUTPUT"
echo "sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"
if ! git merge --no-ff -m "Merge ignis-main into GStreamer $RELEASE candidate" "$BASE_SHA"; then
  git diff --name-only --diff-filter=U > "$RUNNER_TEMP/gstreamer-conflicts.txt"
  cat "$RUNNER_TEMP/gstreamer-conflicts.txt"
  echo "conflicts=$(paste -sd , "$RUNNER_TEMP/gstreamer-conflicts.txt")" >> "$GITHUB_OUTPUT"
  git merge --abort
  exit 1
fi
git push origin "$BRANCH"
echo "sha=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"
gh api --method POST "repos/$GITHUB_REPOSITORY/statuses/$(git rev-parse HEAD)" \
  -f context=ignis-gstreamer-regressions -f state=pending \
  -f target_url="$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID"
echo "changed=true" >> "$GITHUB_OUTPUT"
