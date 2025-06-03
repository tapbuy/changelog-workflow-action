import { getOctokit, context } from "@actions/github";
import * as core from "@actions/core";

async function run() {
  const token = core.getInput("github_token", { required: true });
  const octokit = getOctokit(token);

  const pr = context.payload.pull_request;
  if (!pr) {
    core.setFailed("No pull request found in context");
    return;
  }

  const headRef = pr.head.ref;
  const prNumber = pr.number;

  const repo = {
    owner: context.repo.owner,
    repo: context.repo.repo,
  };

  const releaseMatch = headRef.match(/^release\/(.+)$/);
  const hotfixMatch = headRef.match(/^hotfix\/(.+)$/);

  let version: string;
  let description: string;
  let isHotfix = false;

  if (releaseMatch) {
    version = releaseMatch[1];
    description = `Release ${version}`;
  } else if (hotfixMatch) {
    version = hotfixMatch[1];
    description = `Hotfix ${version}`;
    isHotfix = true;
  } else {
    core.info("Not a release or hotfix PR. Skipping.");
    return;
  }

  const oldBody = pr.body?.trim();
  if (oldBody && oldBody.length > 0) {
    core.info("PR body already set. Skipping.");
    return;
  }

  const { data: latestRelease } = await octokit.rest.repos
    .getLatestRelease(repo)
    .catch(() => ({ data: null }));
  const previous_tag_name = latestRelease?.tag_name;

  const { data: releaseNotes } = await octokit.rest.repos.generateReleaseNotes({
    ...repo,
    tag_name: version,
    target_commitish: headRef,
    previous_tag_name,
  });

  let body = `${releaseNotes.body.trim()}

---

## ${description}`;

  if (isHotfix && previous_tag_name) {
    const { data: comparison } = await octokit.rest.repos.compareCommits({
      ...repo,
      base: previous_tag_name,
      head: headRef,
    });

    const { data: mainComparison } = await octokit.rest.repos.compareCommits({
      ...repo,
      base: previous_tag_name,
      head: "main",
    });

    const mainShas = new Set(mainComparison.commits.map((c) => c.sha));
    const newCommits = comparison.commits.filter(c => !mainShas.has(c.sha));

    if (newCommits.length > 0) {
      body += "\n\n---\n\n## Hotfix Commit(s):\n";
      for (const commit of newCommits) {
        const message = commit.commit.message.split("\n")[0];
        const authorName = commit.commit.author?.name ?? "Unknown";
        const authorLogin = commit.author?.login
          ? `(@${commit.author.login})`
          : "";

        body += `- ${message} – ${authorName} ${authorLogin}\n`;
      }
    }
  }

  await octokit.rest.pulls.update({
    ...repo,
    pull_number: prNumber,
    body,
  });

  core.info(`PR #${prNumber} body updated with changelog and description.`);
}

run().catch((err) => core.setFailed(err.message));
