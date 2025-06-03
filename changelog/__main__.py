import os
import sys
import requests
from .utils import get_repo_info, fetch_pr_metadata, get_tags, patch_pr_body
from .formatter_hotfix import format_hotfix_changelog
from .formatter_release import format_release_changelog

def run():
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    PR_NUMBER = os.environ.get("PR_NUMBER")
    REPO_OWNER = os.environ.get("REPO_OWNER")
    REPO_NAME = os.environ.get("REPO_NAME")

    if not GITHUB_TOKEN or not PR_NUMBER:
        print("❌ Missing GITHUB_TOKEN or PR_NUMBER")
        sys.exit(1)

    if not REPO_OWNER or not REPO_NAME:
        REPO_OWNER, REPO_NAME = get_repo_info()

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    pr = fetch_pr_metadata(REPO_OWNER, REPO_NAME, PR_NUMBER, headers)
    head_branch = pr.get("head", {}).get("ref")
    base_branch = pr.get("base", {}).get("ref")

    if not head_branch or not base_branch:
        print("❌ Invalid PR metadata")
        sys.exit(1)

    if not head_branch.startswith(("release/", "hotfix/")) or base_branch not in ["main", "master"]:
        print(f"ℹ️ Branch {head_branch} -> {base_branch} does not match expected patterns. Skipping.")
        sys.exit(0)

    latest_tag = get_tags()
    current_tag = "HEAD"
    compare_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/compare/{latest_tag}...{current_tag}"
    version = head_branch.split("/")[-1]

    if head_branch.startswith("hotfix/"):
        print(f"🛠 Running hotfix changelog formatter for branch: {head_branch}")
        print("📄 Using: formatter_hotfix.py")
        body = format_hotfix_changelog(latest_tag, "HEAD", version, compare_url)
    else:
        print(f"🚀 Running release changelog formatter for branch: {head_branch}")
        print("📄 Using: formatter_release.py")
        body = format_release_changelog(REPO_OWNER, REPO_NAME, latest_tag, "HEAD", version, compare_url, headers)

    patch_pr_body(REPO_OWNER, REPO_NAME, PR_NUMBER, body, headers)
