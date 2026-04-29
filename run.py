"""
Entry point — always run this from the project root:
    python run.py
"""
import sys
import os

# Ensure project root is on the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.app import app

if __name__ == "__main__":
    print("=" * 50)
    print("  🚀 AI CI/CD Failure Prediction Dashboard")
    print("  → http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)