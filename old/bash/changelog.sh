#!/usr/bin/env bash
set -euo pipefail

# Inputs
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
PR_NUMBER="${PR_NUMBER:-}"
REPO_OWNER="${REPO_OWNER:-$(gh repo view --json owner -q '.owner.login')}"
REPO_NAME="${REPO_NAME:-$(gh repo view --json name -q '.name')}"

if [[ -z "$GITHUB_TOKEN" || -z "$PR_NUMBER" ]]; then
  echo "GITHUB_TOKEN and PR_NUMBER are required"
  exit 1
fi

# Get PR metadata
pr_json=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/pulls/$PR_NUMBER")

head_branch=$(echo "$pr_json" | jq -r '.head.ref')
base_branch=$(echo "$pr_json" | jq -r '.base.ref')
pr_title=$(echo "$pr_json" | jq -r '.title')

if [[ "$head_branch" =~ ^(release|hotfix)/ ]] && [[ "$base_branch" =~ ^(main|master)$ ]]; then
  echo "Matched pattern: $head_branch -> $base_branch"
else
  echo "Branch $head_branch -> $base_branch does not match, skipping"
  exit 0
fi

# Git changelog
git fetch --tags
latest_tag=$(git tag --sort=-creatordate | tail -n 2 | head -n 1)
current_tag=$(git tag --sort=-creatordate | tail -n 1)

if [[ -z "$latest_tag" || -z "$current_tag" ]]; then
  echo "Missing tags, cannot compute changelog"
  exit 0
fi

commit_lines=$(git log --pretty=format:'- %s – %an (@%an)' "$latest_tag..$current_tag")

# Markdown body generation
if [[ "$head_branch" =~ ^hotfix/ ]]; then
  version=$(basename "$head_branch")
  body="Full Changelog: $latest_tag...$current_tag

## Hotfix $version

### Hotfix Commit(s):
$commit_lines"
else
  version=$(basename "$head_branch")
  body="## What's Changed

$commit_lines

## Full Changelog: $latest_tag...$current_tag

## Release $version"
fi

# Update PR body
updated_body=$(jq -n --arg body "$body" '{"body": $body}')
curl -s -X PATCH -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$updated_body" \
  "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/pulls/$PR_NUMBER"
