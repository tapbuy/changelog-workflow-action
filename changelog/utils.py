# --- changelog/utils.py ---
import subprocess
import json
import sys
import requests

def get_repo_info():
    try:
        repo_data = json.loads(subprocess.check_output(["gh", "repo", "view", "--json", "name,owner"]))
        return repo_data["owner"]["login"], repo_data["name"]
    except Exception as e:
        print("❌ Failed to get repo info via GitHub CLI:", e)
        sys.exit(1)

def fetch_pr_metadata(owner, repo, pr_number, headers):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    r = requests.get(url, headers=headers)
    if not r.ok or "application/json" not in r.headers.get("Content-Type", ""):
        print(f"❌ Failed to fetch PR metadata ({r.status_code}):")
        print(r.text)
        sys.exit(1)
    return r.json()

def get_tags():
    subprocess.run(["git", "fetch", "--tags"], check=True)
    tags = subprocess.check_output(["git", "tag", "--sort=-creatordate"]).decode().split()

    if not tags:
        print("❌ No tags found in repository.")
        sys.exit(1)

    return tags[0]  # juste latest_tag


def patch_pr_body(owner, repo, pr_number, body, headers):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    patch = {"body": body}
    r = requests.patch(url, headers=headers, data=json.dumps(patch))
    if r.status_code != 200:
        print("❌ Failed to update PR body:", r.status_code)
        print(r.text)
        sys.exit(1)
    print("✅ PR body updated.")