# 🚀 AI CI/CD Failure Prediction Dashboard

A machine learning-powered Flask web application that predicts CI/CD pipeline failures before they happen. Get real-time insights into your pipeline health, receive actionable recommendations, and track prediction history.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [ML Models](#ml-models)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Testing](#testing)

---

## 📖 Overview

This project predicts whether a CI/CD pipeline will fail based on key metrics like error count, warning count, dependencies, and installation steps. It uses a trained Logistic Regression model (93.06% accuracy) to classify pipelines as safe or at-risk.

**Key Capabilities:**
- ✅ **Manual Predictions** – Input pipeline metrics to get instant failure probability
- ✅ **Why This Prediction?** – Human-readable explanation bullets + a computed root cause
- ✅ **GitHub Integration** – Analyze real workflow runs from any public GitHub repository
- ✅ **Interactive Dashboard** – View predictions, history, and model statistics
- ✅ **Smart Suggestions** – Get actionable recommendations based on risk factors
- ✅ **Prediction History** – Track all predictions in SQLite database

---

## ✨ Features

### 1. **Manual Prediction**
- Input raw pipeline metrics (errors, warnings, dependencies, install steps)
- Get instant failure probability with visual risk breakdown
- See **"Why this prediction?"** explanation bullets
- Get a **root cause** label (weighted priority across errors/warnings/deps/complexity)
- Receive context-aware suggestions (now includes recommended **action**)

### 2. **GitHub Integration**
- Fetch the latest 10 workflow runs from any GitHub repository
- Automatically map workflow conclusions to pipeline features
- Predict failure probability for each run
- Optional GitHub token (passed in request body / UI field) for higher API rate limits

### 3. **Dashboard**
- User authentication (simple username-based login)
- View recent predictions at a glance
- Access full prediction history with filtering
- View model performance metrics
- Real-time summary statistics

### 4. **Suggestions Engine**
Provides multi-level insights (each suggestion includes an `action` field):
- 🔴 **High** – Highest priority issues (e.g. critical errors)
- 🟠 **Medium** – Important issues (e.g. many warnings, moderate risk)
- 🟡 **Low** – Optimization / complexity concerns
- 🟢 **Success** – Healthy pipeline message

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend Framework | Flask 2.x |
| ML / Data Processing | scikit-learn, pandas, NumPy |
| Database | SQLite3 |
| Model Serialization | joblib |
| HTTP Client | requests |
| Frontend | HTML5, CSS3, vanilla JavaScript |

---

## 📁 Project Structure

```
AI-CICD-PREDICTION/
├── run.py                          # Entry point – starts Flask server
├── predictions.db                  # SQLite database (auto-created)
├── README.md                       # This file
│
├── app/
│   ├── __init__.py                 # Marks app as a Python package
│   ├── app.py                      # Flask routes and main logic
│   ├── database.py                 # Database initialization & queries
│   ├── static/
│   │   ├── style.css               # Dashboard styling
│   │   └── script.js               # Frontend interactivity
│   └── templates/
│       ├── index.html              # Main dashboard
│       └── login.html              # Login page
│
├── src/
│   ├── train_model.py              # ML model training pipeline
│   ├── predict.py                  # Prediction logic & suggestions
│   └── github_integration.py        # GitHub Actions API wrapper
│
├── data/
│   ├── generate_dataset.py          # Synthetic dataset generator
│   └── processed/
│       └── dataset.csv             # Training data (720 samples)
│
├── models/
│   ├── model.pkl                   # Trained model (joblib)
│   └── results.json                # Model metrics & accuracy
│
└── tests/
    └── test_model.py               # Multi-repo prediction tests
```

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Steps

1. **Clone the repository** (or navigate to the project directory)
   ```bash
   cd AI-CICD-PREDICTION
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate        # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask scikit-learn pandas numpy requests joblib
   ```

4. **Generate training dataset**
   ```bash
   python data/generate_dataset.py
   ```
   Expected output:
   ```
   ✅ Dataset saved: 720 records
   Label distribution:
   0    360
   1    360
   ```

5. **Train the ML model**
   ```bash
   python src/train_model.py
   ```
   Expected output:
   ```
   ✅ Best model : Logistic Regression  (Accuracy: 0.9306)
      Saved to   : models/model.pkl
      Metrics    : models/results.json
   ```

---

## 🚀 Quick Start

Start the Flask development server:

```bash
python run.py
```

Alternative (module run):

```bash
python -m app.app
```

Output:
```
==================================================
  🚀 AI CI/CD Failure Prediction Dashboard
  → http://127.0.0.1:5000
==================================================
```

Open your browser and visit: **http://127.0.0.1:5000**

1. **Login** with any username (no password required)
2. **Use the dashboard** to make predictions

---

## 💡 Usage

### Manual Prediction

1. Navigate to the **Prediction** tab
2. Enter pipeline metrics:
   - **Error Count** – Number of errors in the pipeline
   - **Warning Count** – Number of warnings
   - **Dependency Downloads** – Total dependencies
   - **Install Steps** – Number of installation steps
   - **Has Git Clone** – Whether the pipeline includes git clone
3. Click **Predict**
4. View results:
   - Failure probability (0–100%)
   - Risk breakdown by category
   - Actionable suggestions

### GitHub Prediction

1. Navigate to the **GitHub** tab
2. Enter a repository in format: `owner/repo` (e.g., `tensorflow/tensorflow`)
3. Click **Analyze**
4. View predictions for the latest 10 workflow runs

**Note:** Optional GitHub token increases API rate limits.

- In the UI: paste a token into the **Token** field.
- Via API: send `token` in the JSON body (see `/github_predict` below).

---

## 🔌 API Endpoints

### Authentication
- **`/login`** `[GET, POST]` – User login page

### Dashboard
- **`/`** `[GET]` – Main dashboard (requires login)
- **`/logout`** `[GET]` – Logout user

### Predictions
- **`/predict`** `[POST]` – Manual prediction
  ```json
  {
    "error_count": 2,
    "warning_count": 1,
    "dependency_downloads": 25,
    "install_steps": 1,
    "has_git_clone": 1
  }
  ```

   **Response (example):**
   ```json
   {
      "prediction": 1,
      "probability": 0.8423,
      "alert": "FAILURE RISK",
      "root_cause": "Warnings",
      "explanation": [
         "Too many warnings indicate unstable pipeline"
      ],
      "breakdown": {
         "error_risk": 33.3,
         "warning_risk": 75.0,
         "complexity_risk": 41.7,
         "history_risk": 84.2
      },
      "suggestions": [
         {
            "level": "medium",
            "icon": "🟠",
            "title": "Moderate Risk",
            "message": "84% failure probability.",
            "action": "Review warnings and dependencies"
         }
      ]
   }
   ```

- **`/github_predict`** `[POST]` – GitHub-based prediction
  ```json
  {
      "repo": "owner/repo",
      "token": "ghp_... (optional)"
  }
  ```

### History & Analytics
- **`/history`** `[GET]` – Recent 10 predictions
- **`/history/all`** `[GET]` – All predictions
- **`/summary`** `[GET]` – Summary statistics
- **`/model-stats`** `[GET]` – Model performance metrics

### Health Check
- **`/health`** `[GET]` – Server status

---

## 🤖 ML Models

### Model Comparison

| Model | Accuracy | Precision | Recall | F1 Score |
|-------|----------|-----------|--------|----------|
| **Logistic Regression** | 93.06% | 88.75% | 98.61% | 93.42% |
| Random Forest | 88.89% | 86.84% | 91.67% | 89.19% |
| Gradient Boosting | 89.58% | 88.0% | 91.67% | 89.8% |
| Decision Tree | 85.42% | 85.92% | 84.72% | 85.31% |

**Best Model:** Logistic Regression (selected for highest accuracy and recall)

### Features (9 total)

**Raw Features:**
1. `error_count` – Number of build errors
2. `warning_count` – Number of warnings
3. `dependency_downloads` – Total dependencies to download
4. `install_steps` – Number of installation steps
5. `has_git_clone` – Binary flag for git operations

**Engineered Features:**
6. `has_high_error` – Binary flag for error_count ≥ 3
7. `has_many_warnings` – Binary flag for warning_count ≥ 5
8. `error_warning_ratio` – Ratio of errors to warnings
9. `pipeline_complexity` – Product of dependencies × install steps

### Dataset

- **Size:** 720 balanced samples (360 pass, 360 fail)
- **Label Distribution:** 50% failure rate
- **Train/Test Split:** 80% / 20% (stratified)

---

## 🗄️ Database Schema

### `predictions` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK) | Auto-incrementing prediction ID |
| `error_count` | INTEGER | Error count from input |
| `warning_count` | INTEGER | Warning count from input |
| `dependency_downloads` | INTEGER | Dependencies from input |
| `install_steps` | INTEGER | Install steps from input |
| `has_git_clone` | INTEGER | Git clone flag (0 or 1) |
| `prediction` | INTEGER | Model output (0=safe, 1=failure) |
| `probability` | REAL | Failure probability (0.0–1.0) |
| `timestamp` | DATETIME | Creation time (auto-set) |

**Database File:** `predictions.db` (created automatically on first run)

---

## ⚙️ Configuration

### Risk Threshold

The failure risk alert is triggered when `probability >= 0.5`:
- Location: `app/app.py` line 17
- `THRESHOLD = 0.5`

### Suggestions Levels
Suggestion generation lives in `src/predict.py` and returns a list of objects with:
- `level` (`high`, `medium`, `low`, `success`)
- `title`, `message`, and `action`

Notes:
- “High Failure Risk” is intentionally gated to reduce duplication (only triggers when `probability > 0.85` **and** `error_count >= 5`).
- `probability` is returned with **4 decimal places** for smoother UI display.

### GitHub Integration

**Latest Workflow Runs:** Fetches last 10 runs from target repository

**Feature Mapping:** Maps GitHub workflow conclusions to synthetic features:
- `success` → 0 errors, 1 warning
- `failure` → 5 errors, 4 warnings
- `cancelled` → 2 errors, 3 warnings
- `skipped` → 0 errors, 0 warnings
- In-progress → 1 error, 1 warning

---

## 🧪 Testing

### Run Model Tests

Test the model on multiple repositories:

```bash
python tests/test_model.py
```

This script tests predictions on:
- User-created test repositories
- Public repositories (e.g., TensorFlow)

**Expected Output:**
```
🚀 STARTING MULTI-REPO TEST

🔍 Testing repo: ravishankarsah0001/AI-CI-CD-Test-Pipeline
🔮 Prediction Result:
[...]

📊 FINAL SUMMARY:
[...]
```

---

## 📊 Prediction Workflow

```
User Input (Pipeline Metrics)
         ↓
   Feature Engineering
   (9 engineered features)
         ↓
   Logistic Regression Model
         ↓
   Risk Breakdown + Probability
         ↓
   Suggestions Engine
         ↓
   Stored in SQLite
         ↓
   Dashboard Display
```

---

## 🐛 Troubleshooting

### Model Not Found
```
❌ Model not found at: models/model.pkl
   Please run: python src/train_model.py first.
```
**Solution:** Run the training script before starting the app.

### Dataset Not Found
```
❌ Dataset not found at: data/processed/dataset.csv
   Please run: python data/generate_dataset.py first.
```
**Solution:** Generate the dataset before training.

### GitHub API Rate Limit
```
Error: GitHub API rate limit exceeded
```
**Solution:** Set your GitHub token:
Use the GitHub tab **Token** input (recommended), or send `token` in the `/github_predict` request body.

---

## 🔐 Security Notes

- Never commit tokens / PATs to git.
- This repo’s `.gitignore` intentionally ignores `github_pat_*` and common token filename patterns.

### Port Already in Use
```
Address already in use
```
**Solution:** Change port in `run.py` or kill process using port 5000:
```bash
# On Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# On macOS/Linux
lsof -i :5000
kill -9 <PID>
```

---

## 📝 Notes

- **Login:** Simple username-based (no password) for demo purposes
- **Database:** SQLite file persists across sessions
- **Model:** Trained once and reused for all predictions
- **GitHub Token:** Optional; increases rate limits but not required for public repos

---

## 🤝 Contributing

To improve this project:

1. Retrain the model with new data: `python src/train_model.py`
2. Test on real workflows: `python tests/test_model.py`
3. Modify suggestions in `src/predict.py`
4. Update thresholds in `app/app.py`

---

## 📄 License

This project is provided as-is for educational and development purposes.

---

📫 Connect with Me:

📧 Email: shivshankarkumarsah23072004@gmail.com
💼 LinkedIn: https://www.linkedin.com/in/shiv-shankar-kumar-sah-64218a2a0/overlay/about-this-profile/
📊 GitHub : https://github.com/ssks23072004/ssks23072004/tree/main


**Happy pipeline predicting! 🚀**
