import os
import joblib
import pandas as pd

from src.github_integration import get_latest_workflow_runs, extract_features_from_runs


# -----------------------------
# LOAD MODEL
# -----------------------------
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"\n\n❌ Model not found at: {MODEL_PATH}"
        f"\n   Run: python src/train_model.py\n"
    )

model = joblib.load(MODEL_PATH)


# -----------------------------
# FEATURE ORDER
# -----------------------------
FEATURE_COLUMNS = [
    "error_count",
    "warning_count",
    "dependency_downloads",
    "install_steps",
    "has_git_clone",
    "has_high_error",
    "has_many_warnings",
    "error_warning_ratio",
    "pipeline_complexity"
]


# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
def build_features(error_count, warning_count, dependency_downloads,
                   install_steps, has_git_clone):

    return {
        "error_count":          error_count,
        "warning_count":        warning_count,
        "dependency_downloads": dependency_downloads,
        "install_steps":        install_steps,
        "has_git_clone":        has_git_clone,
        "has_high_error":       1 if error_count >= 3 else 0,
        "has_many_warnings":    1 if warning_count >= 5 else 0,
        "error_warning_ratio":  error_count / (warning_count + 1),
        "pipeline_complexity":  dependency_downloads * install_steps
    }


# -----------------------------
# CORE PREDICTION
# -----------------------------
def predict_failure(error_count, warning_count, dependency_downloads,
                    install_steps, has_git_clone):

    features = build_features(
        error_count, warning_count,
        dependency_downloads, install_steps, has_git_clone
    )

    data = pd.DataFrame([features])[FEATURE_COLUMNS]

    pred = model.predict(data)[0]
    prob = float(model.predict_proba(data)[0][1])
    

    # -----------------------------
    # 🎯 CALIBRATED RISK SCALING
    # -----------------------------
    ERROR_CRITICAL = 6
    WARNING_CRITICAL = 8

    e = error_count
    w = warning_count

    # 🔥 1. EXTREME (above critical)
    if e > ERROR_CRITICAL or w > WARNING_CRITICAL:
        prob = 0.995 + min(0.004, 0.001 * (e + w))

    # ⚠️ 2. EXACT CRITICAL
    elif e == ERROR_CRITICAL or w == WARNING_CRITICAL:
        prob = 0.95

    # 🧠 3. BELOW CRITICAL → CONTROLLED CURVE
    else:
        risk_score = (
            (e / ERROR_CRITICAL) * 0.6 +
            (w / WARNING_CRITICAL) * 0.4
        )

        # calibrated curve
        if risk_score < 0.4:
            calibrated = 0.4 + risk_score * 0.3
        elif risk_score < 0.7:
            calibrated = 0.55 + (risk_score - 0.4) * 0.5
        else:
            calibrated = 0.7 + (risk_score - 0.7) * 0.8

        # 🔥 FINAL FIX → blend ML + calibration
        prob = 0.6 * prob + 0.4 * calibrated
        prob = max(0.0, min(prob, 0.999))

    # -----------------------------
    # 🔍 EXPLAINABILITY (NEW)
    # -----------------------------
    explanation = []

    if error_count >= 4:
        explanation.append("High error count increases failure risk")

    if warning_count >= 5:
        explanation.append("Too many warnings indicate unstable pipeline")

    if dependency_downloads > 40:
        explanation.append("Heavy dependencies increase complexity")

    if install_steps >= 2:
        explanation.append("Multiple install steps increase failure chance")

    if prob > 0.8:
        explanation.append("Overall risk is high due to combined factors")

    # -----------------------------
    # 🎯 ROOT CAUSE ANALYSIS
    # -----------------------------
    # weighted importance
    error_weight   = error_count * 1.2
    warning_weight = warning_count * 1.0
    dep_weight     = dependency_downloads / 10
    install_weight = install_steps * 2

    weights = {
        "Error Count": error_weight,
        "Warnings": warning_weight,
        "Dependencies": dep_weight,
        "Pipeline Complexity": install_weight
    }

    root_cause = max(weights, key=weights.get)

    return {
        "prediction": int(pred),
        "probability": round(prob, 4),
        "explanation": explanation,
        "root_cause": root_cause
    }


# -----------------------------
# SUGGESTIONS ENGINE
# -----------------------------
def get_suggestions(error_count, warning_count, dependency_downloads,
                    install_steps, has_git_clone, probability):

    suggestions = []

    # -----------------------------
    # 🔴 PRIMARY ISSUE (highest impact)
    # -----------------------------
    if error_count >= 5:
        suggestions.append({
            "level": "high",
            "icon": "🔴",
            "title": "Critical Error Count",
            "message": f"{error_count} errors detected.",
            "action": "Fix failing steps immediately (check logs/tests)"
        })

    # -----------------------------
    # 🟠 WARNINGS
    # -----------------------------
    if warning_count >= 5:
        suggestions.append({
            "level": "medium",
            "icon": "🟠",
            "title": "Too Many Warnings",
            "message": f"{warning_count} warnings detected.",
            "action": "Clean warnings to improve pipeline stability"
        })

    # -----------------------------
    # 🟡 DEPENDENCY COMPLEXITY
    # -----------------------------
    if dependency_downloads > 40:
        suggestions.append({
            "level": "low",
            "icon": "🟡",
            "title": "Heavy Dependency Load",
            "message": f"{dependency_downloads} dependencies used.",
            "action": "Use caching / reduce dependencies"
        })

    # -----------------------------
    # 🟡 INSTALL COMPLEXITY
    # -----------------------------
    if install_steps >= 2:
        suggestions.append({
            "level": "low",
            "icon": "🟡",
            "title": "Complex Pipeline",
            "message": f"{install_steps} install steps detected.",
            "action": "Simplify pipeline steps"
        })

    # -----------------------------
    # 🧠 OVERALL RISK PRIORITY
    # -----------------------------
    if probability > 0.85 and error_count >= 5:
        suggestions.insert(0, {
            "level": "high",
            "icon": "🔴",
            "title": "High Failure Risk",
            "message": f"{round(probability*100)}% failure probability.",
            "action": "Prioritize fixing errors immediately"
        })

    elif probability > 0.6:
        suggestions.insert(0, {
            "level": "medium",
            "icon": "🟠",
            "title": "Moderate Risk",
            "message": f"{round(probability*100)}% failure probability.",
            "action": "Review warnings and dependencies"
        })

    # -----------------------------
    # 🟢 SAFE CASE
    # -----------------------------
    if not suggestions:
        suggestions.append({
            "level": "success",
            "icon": "🟢",
            "title": "Pipeline Healthy",
            "message": "Stable pipeline. No immediate risks detected.",
            "action": "No action required"
        })

    return suggestions


# -----------------------------
# GITHUB PREDICTION (FINAL)
# -----------------------------
def predict_from_github(repo, token=None):

    runs = get_latest_workflow_runs(repo, token=token)

    if isinstance(runs, dict) and "error" in runs:
        return runs

    extracted = extract_features_from_runs(runs, repo, token)

    results = []

    for item in extracted:

        result = predict_failure(
            error_count=item.get("error_count", 0),
            warning_count=item.get("warning_count", 0),
            dependency_downloads=item.get("dependency_downloads", 20),
            install_steps=item.get("install_steps", 1),
            has_git_clone=item.get("has_git_clone", 1),
        )

        conclusion = item.get("conclusion", "unknown")
        status     = item.get("status", "unknown")

        # -----------------------------
        # 🚀 RUNNING STATE (NEW FIX)
        # -----------------------------
        if conclusion == "unknown" or status in ["in_progress", "queued"]:
            result["prediction"] = 0
            result["probability"] = 0.2
            result["risk_level"] = "RUNNING"
            result["root_cause"] = "Pending"

            result["suggestions"] = [{
                "level": "info",
                "icon": "🔵",
                "title": "Pipeline Running",
                "message": "Workflow is still running. Final result not available yet."
            }]

        else:
            # -----------------------------
            # REALITY ALIGNMENT
            # -----------------------------
            if conclusion == "success":
                result["probability"] = min(result["probability"], 0.4)
                result["prediction"] = 0
                result["root_cause"] = "None"

            elif conclusion == "failure":
                result["probability"] = max(result["probability"], 0.6)
                result["prediction"] = 1

            # -----------------------------
            # RISK LEVEL
            # -----------------------------
            if result["probability"] < 0.3:
                risk = "LOW"
            elif result["probability"] < 0.6:
                risk = "MEDIUM"
            else:
                risk = "HIGH"

            result["risk_level"] = risk

            # -----------------------------
            # SUGGESTIONS
            # -----------------------------
            if conclusion == "success":
                result["suggestions"] = [{
                    "level": "success",
                    "icon": "🟢",
                    "title": "Pipeline Successful",
                    "message": "Pipeline completed successfully."
                }]
            else:
                result["suggestions"] = get_suggestions(
                    item.get("error_count", 0),
                    item.get("warning_count", 0),
                    item.get("dependency_downloads", 20),
                    item.get("install_steps", 1),
                    item.get("has_git_clone", 1),
                    result["probability"]
                )

        # -----------------------------
        # METADATA
        # -----------------------------
        result["status"]     = status
        result["run_name"]   = item.get("run_name", "Workflow Run")
        result["conclusion"] = conclusion

        results.append(result)

    return results