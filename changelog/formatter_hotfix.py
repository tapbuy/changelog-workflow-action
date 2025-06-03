import os
import sys
import requests

def format_hotfix_changelog(latest_tag, current_tag, version, compare_url):
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    PR_NUMBER = os.environ.get("PR_NUMBER")
    REPO_OWNER = os.environ.get("REPO_OWNER")
    REPO_NAME = os.environ.get("REPO_NAME")

    if not GITHUB_TOKEN or not PR_NUMBER:
        print("Missing GITHUB_TOKEN or PR_NUMBER")
        sys.exit(1)

    if not REPO_OWNER or not REPO_NAME:
        print("Missing REPO_OWNER or REPO_NAME")
        sys.exit(1)

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    commit_api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{PR_NUMBER}/commits"
    try:
        commit_resp = requests.get(commit_api_url, headers=headers)
        commit_resp.raise_for_status()
        commits_data = commit_resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching commits: {e}")
        sys.exit(1)

    log_lines = []
    for c in commits_data:
        # Correction du double backslash
        msg = c["commit"]["message"].split("\n")[0]
        
        # Amélioration de la gestion des auteurs
        author = c.get("author", {})
        if author and "login" in author:
            author_name = f"@{author['login']}"
        else:
            # Utilisation du nom de l'auteur du commit comme fallback
            author_name = c["commit"]["author"]["name"]
        
        line = f"- {msg} – {author_name}"
        log_lines.append(line)

    return f"""Full Changelog: [{latest_tag}...{version}]({compare_url})

## Hotfix {version}

### Hotfix Commit(s):
{chr(10).join(log_lines)}"""