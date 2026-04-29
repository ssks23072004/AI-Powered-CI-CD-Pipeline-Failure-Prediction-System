import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from src.predict import predict_failure, predict_from_github, get_suggestions
from app.database import (
    init_db, insert_prediction, get_predictions,
    get_all_predictions, get_summary_stats
)

app = Flask(__name__)
app.secret_key = "cicd_secret_key_2024"

THRESHOLD = 0.5

init_db()


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            return render_template("login.html", error="Please enter a username")
        session["user"] = username
        return redirect(url_for("home"))
    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["user"])


# ---------------- MANUAL PREDICTION ----------------
@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.json or {}

        error_count          = int(data.get("error_count",          0))
        warning_count        = int(data.get("warning_count",        0))
        dependency_downloads = int(data.get("dependency_downloads", 0))
        install_steps        = int(data.get("install_steps",        1))
        has_git_clone        = int(data.get("has_git_clone",        1))

        result = predict_failure(
            error_count, warning_count,
            dependency_downloads, install_steps, has_git_clone
        )

        prob  = result["probability"]
        pred  = result["prediction"]
        alert = "FAILURE RISK" if prob > THRESHOLD else "SAFE"

        suggestions = get_suggestions(
            error_count, warning_count,
            dependency_downloads, install_steps, has_git_clone, prob
        )

        insert_prediction(
            error_count, warning_count, dependency_downloads,
            install_steps, has_git_clone, pred, prob
        )

        return jsonify({
            "prediction":   pred,
            "probability":  prob,
            "alert":        alert,
            "explanation":  result.get("explanation", []),
            "root_cause":   result.get("root_cause", "Unknown"),
            "breakdown": {
                "error_risk":       round(min(error_count / 6, 1) * 100, 1),
                "warning_risk":     round(min(warning_count / 8, 1) * 100, 1),
                "complexity_risk":  round(min((dependency_downloads * install_steps) / 120, 1) * 100, 1),
                "history_risk":     round(prob * 100, 1),
            },
            "suggestions": suggestions
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- 🔥 GITHUB PREDICTION (UPDATED WITH TOKEN) ----------------
@app.route("/github_predict", methods=["POST"])
def github_predict():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = request.json or {}

        repo  = data.get("repo", "").strip()
        token = (data.get("token") or "").strip()  # 🔥 NEW

        if not repo:
            return jsonify({"error": "Repository not provided"}), 400

        if "/" not in repo:
            return jsonify({"error": "Format must be owner/repo (e.g. tensorflow/tensorflow)"}), 400

        # 🔥 PASS TOKEN TO PREDICTION
        results = predict_from_github(repo, token=token if token else None)

        if isinstance(results, dict) and "error" in results:
            return jsonify(results), 400

        return jsonify({
            "repo": repo,
            "results": results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        rows = get_predictions()
        return jsonify([{
            "id":           r[0],
            "error_count":          r[1],
            "warning_count":        r[2],
            "dependency_downloads": r[3],
            "install_steps":        r[4],
            "has_git_clone":        r[5],
            "prediction":           r[6],
            "probability":          r[7],
            "timestamp":            r[8],
        } for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- FULL HISTORY ----------------
@app.route("/history/all")
def history_all():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        rows = get_all_predictions()
        return jsonify([{
            "id":                   r[0],
            "error_count":          r[1],
            "warning_count":        r[2],
            "dependency_downloads": r[3],
            "install_steps":        r[4],
            "has_git_clone":        r[5],
            "prediction":           r[6],
            "probability":          r[7],
            "timestamp":            r[8],
        } for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- SUMMARY ----------------
@app.route("/summary")
def summary():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        return jsonify(get_summary_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- MODEL STATS ----------------
@app.route("/model-stats")
def model_stats():
    try:
        result_path = os.path.join(BASE_DIR, "models", "results.json")
        if not os.path.exists(result_path):
            return jsonify({"error": "Model stats not found. Run train_model.py first."}), 404
        with open(result_path) as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- HEALTH ----------------
@app.route("/health")
def health():
    return jsonify({"status": "running", "user": session.get("user", "not logged in")})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)