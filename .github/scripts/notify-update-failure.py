#!/usr/bin/env python3
"""Report a failed update once per revision and failing stage."""
import html
import json
import os
import subprocess
import urllib.request


def gh(*args, data=None):
    command = ["gh", "api", *args]
    if data is not None:
        command += ["--method", "POST", "--input", "-"]
    result = subprocess.run(command, input=json.dumps(data) if data is not None else None,
                            text=True, check=True, capture_output=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    pr = os.environ.get("UPDATE_PR", "")
    stage = os.environ.get("FAILED_STAGE", "update")
    revision = os.environ.get("UPDATE_SHA") or os.environ.get("UPDATE_BASE") or os.environ["GITHUB_SHA"]
    release = os.environ.get("UPDATE_RELEASE", "unknown")
    base = os.environ.get("UPDATE_BASE", "unknown")
    run = f"{os.environ['GITHUB_SERVER_URL']}/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    marker = f"<!-- gstreamer-update-failure:{release}:{base}:{revision}:{stage} -->"
    status_context = os.environ.get("FAILED_STATUS_CONTEXT", "")
    if status_context and os.environ.get("UPDATE_SHA"):
        try:
            gh(f"repos/{repo}/statuses/{revision}", data={
                "context": status_context, "state": "failure", "target_url": run})
        except subprocess.CalledProcessError:
            print("Could not mark the validation check failed; continuing with Slack delivery")
    comments_path = None
    if pr:
        number = pr.rstrip("/").rsplit("/", 1)[1]
        comments_path = f"repos/{repo}/issues/{number}/comments"
        try:
            pages = gh(comments_path, "--paginate", "--slurp")
        except subprocess.CalledProcessError:
            print("Could not check earlier notifications; continuing with Slack delivery")
            pages = []
        if any(marker in item.get("body", "") for page in pages for item in page):
            print("This failure has already been reported")
            return
    text = f"GStreamer update blocked during {stage} ({release}).\n"
    if pr:
        text += f"PR: {pr}\n"
    conflicts = os.environ.get("UPDATE_CONFLICTS", "")
    if conflicts:
        text += f"Conflicting files: {conflicts}\n"
    text += f"Logs: {run}"
    payload = {"channel": os.environ.get("SLACK_CHANNEL", "C09V4N95Y4Q"),
               "text": html.escape(text, quote=False),
               "unfurl_links": False, "unfurl_media": False}
    request = urllib.request.Request("https://slack.com/api/chat.postMessage",
        data=json.dumps(payload).encode(), headers={
            "Authorization": "Bearer " + os.environ["SLACK_BOT_TOKEN"],
            "Content-Type": "application/json; charset=utf-8"}, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError("Slack notification failed: " + result.get("error", "unknown"))
    if comments_path:
        gh(comments_path, data={"body": marker + "\n" + text})


if __name__ == "__main__":
    main()
