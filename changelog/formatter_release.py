# --- changelog/formatter_release.py ---
import subprocess
import re
import requests

def format_release_changelog(owner, repo, latest_tag, current_tag, version, compare_url, headers):
    raw_log = subprocess.check_output([
        "git", "log", f"{latest_tag}..{current_tag}", "--merges", "--pretty=format:%H|%s"
    ]).decode().strip().splitlines()

    log_lines = []
    for entry in raw_log:
        if "|" not in entry:
            continue
        _, message = entry.split("|", 1)
        pr_match = re.search(r"Merge pull request #(\d+)", message)
        if pr_match:
            pr_num = pr_match.group(1)
            try:
                r = requests.get(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}",
                    headers=headers
                )
                r.raise_for_status()
                pr_data = r.json()
                title = pr_data.get("title", "").strip()
                pr_url = pr_data.get("html_url", "")
                author = pr_data.get("user", {}).get("login", "unknown")
                log_lines.append(f"- [#{pr_num}]({pr_url}) {title} – @{author}")
            except Exception as e:
                print(f"⚠️ Failed to enrich PR #{pr_num}: {e}")
                log_lines.append(f"- #{pr_num} – failed to load details")

    return f"""## What's Changed

{chr(10).join(log_lines)}

## Full Changelog: [{latest_tag}...{version}]({compare_url})

## Release {version}"""
