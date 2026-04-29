import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.predict import predict_from_github

# -----------------------------
# MULTIPLE REPOS TO TEST
# -----------------------------
repos = [
    "ravishankarsah0001/AI-CI-CD-Test-Pipeline",
    "ssks23072004/AI-CI-CD-Test-Pipeline"  ,
    "tensorflow/tensorflow"            # 🌍 public repo
]

print("\n🚀 STARTING MULTI-REPO TEST\n")

all_results = {}

for repo in repos:
    print(f"\n🔍 Testing repo: {repo}")

    try:
        result = predict_from_github(repo)

        if isinstance(result, dict) and "error" in result:
            print("❌ Error:", result["error"])
        else:
            print("🔮 Prediction Result:")
            print(result)

        all_results[repo] = result

    except Exception as e:
        print("❌ Exception:", str(e))
        all_results[repo] = {"error": str(e)}

# -----------------------------
# FINAL SUMMARY
# -----------------------------
print("\n📊 FINAL SUMMARY:\n")

for repo, result in all_results.items():
    print(f"\n👉 {repo}")
    print(result)