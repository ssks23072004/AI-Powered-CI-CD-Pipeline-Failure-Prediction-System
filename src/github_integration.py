import os
import requests
import zipfile
import io

GITHUB_API = "https://api.github.com"

# -----------------------------
# MULTI TOKEN SUPPORT (UPDATED)
# -----------------------------
TOKEN_MAP = {
    "ravishankarsah0001": os.getenv("GITHUB_TOKEN_1"),
    "ssks23072004": os.getenv("GITHUB_TOKEN_2"),   # ✅ NEW ACCOUNT ADDED
}


# -----------------------------
# TOKEN SELECTOR
# -----------------------------
def get_token_for_repo(repo):
    owner = repo.split("/")[0]
    return TOKEN_MAP.get(owner)


# -----------------------------
# HEADERS (HYBRID)
# -----------------------------
def _headers(repo=None, token=None):
    token = token or get_token_for_repo(repo)

    # 🔍 DEBUG LOG (ADD HERE)
    print(f"[DEBUG] Repo: {repo} | Token: {'YES' if token else 'NO'}")

    # Private repo → use token
    if token:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}"
        }

    # Public repo → no token
    return {
        "Accept": "application/vnd.github+json"
    }


# -----------------------------
# FETCH WORKFLOW RUNS
# -----------------------------
def get_latest_workflow_runs(repo, token=None):
    try:
        headers = _headers(repo, token)

        url = f"{GITHUB_API}/repos/{repo}/actions/runs?per_page=20"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 401:
            return {"error": "Unauthorized access. Private repo requires valid token."}
        if response.status_code == 403:
            return {"error": "Rate limit exceeded or access forbidden."}
        if response.status_code == 404:
            return {"error": f"Repository '{repo}' not found."}
        if response.status_code != 200:
            return {"error": f"GitHub API returned {response.status_code}"}

        runs = response.json().get("workflow_runs", [])

        if not runs:
            return {"error": "No workflow runs found"}

        return runs[:20]

    except Exception as e:
        return {"error": str(e)}


# -----------------------------
# FETCH LOGS
# -----------------------------
def get_workflow_logs(repo, run_id, token=None):
    try:
        headers = _headers(repo, token)

        url = f"{GITHUB_API}/repos/{repo}/actions/runs/{run_id}/logs"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        return response.content

    except:
        return None


# -----------------------------
# EXTRACT LOG TEXT
# -----------------------------
def extract_log_text(zip_bytes):
    try:
        z = zipfile.ZipFile(io.BytesIO(zip_bytes))
        logs = ""

        for file in z.namelist():
            with z.open(file) as f:
                logs += f.read().decode("utf-8", errors="ignore") + "\n"

        return logs.lower()

    except:
        return ""


# -----------------------------
# ROOT CAUSE DETECTION
# -----------------------------
def detect_root_cause(log):
    if not log:
        return "Unknown"

    if "npm err" in log or "pip error" in log:
        return "Dependency Failure"
    if "test failed" in log:
        return "Test Failure"
    if "segmentation fault" in log:
        return "Runtime Crash"
    if "permission denied" in log:
        return "Permission Issue"
    if "timeout" in log:
        return "Timeout"
    if "error" in log:
        return "Build Error"

    return "None"


# -----------------------------
# PARSE LOGS → FEATURES
# -----------------------------
def parse_logs(log):
    if not log:
        return None

    error_count = log.count("error")
    warning_count = log.count("warning")

    install_failures = (
        log.count("npm err") +
        log.count("pip error") +
        log.count("installation failed")
    )

    has_git_clone = 1 if "cloning into" in log else 0

    return {
        "error_count": min(error_count, 10),
        "warning_count": min(warning_count, 10),
        "dependency_downloads": 20 + install_failures * 5,
        "install_steps": 2 if install_failures > 0 else 1,
        "has_git_clone": has_git_clone,
        "root_cause": detect_root_cause(log)
    }


# -----------------------------
# FEATURE EXTRACTION
# -----------------------------
def extract_features_from_runs(runs, repo, token=None):
    results = []

    failure_ratio = sum(
        1 for r in runs if r.get("conclusion") == "failure"
    ) / max(len(runs), 1)

    for i, run in enumerate(runs[:5]):

        run_id = run.get("id")
        conclusion = run.get("conclusion")
        status = run.get("status")
        run_name = run.get("name", "Workflow Run")
        run_number = run.get("run_number", 0)

        log_text = ""

        # Smart sampling
        if conclusion in ["failure", "timed_out", "cancelled"]:
            log_zip = get_workflow_logs(repo, run_id, token)
            log_text = extract_log_text(log_zip) if log_zip else ""

        elif i < 3:
            log_zip = get_workflow_logs(repo, run_id, token)
            log_text = extract_log_text(log_zip) if log_zip else ""

        parsed = parse_logs(log_text)

        if not parsed:
            if conclusion == "failure":
                parsed = {
                    "error_count": 4 + i,
                    "warning_count": 3 + i,
                    "dependency_downloads": 30 + i * 3,
                    "install_steps": 2,
                    "has_git_clone": 1,
                    "root_cause": "Failure (Estimated)"
                }
            else:
                parsed = {
                    "error_count": (i % 3) + int(failure_ratio * 2),
                    "warning_count": (i % 4) + 1,
                    "dependency_downloads": 15 + (i * 3),
                    "install_steps": 1 + (i % 2),
                    "has_git_clone": 1,
                    "root_cause": "None"
                }

        parsed["error_count"] += int(failure_ratio * 3)
        parsed["warning_count"] += int(failure_ratio * 2)

        parsed["status"] = conclusion or status or "unknown"
        parsed["conclusion"] = conclusion or "unknown"
        parsed["run_name"] = f"#{run_number} {run_name}"

        results.append(parsed)

    return results