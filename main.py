from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime, timezone
import json
import traceback

app = Flask(__name__)

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]
collection = db["users"]

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/webhook', methods=['POST'])
def github_webhook():
    content_type = request.headers.get('Content-Type')

    if content_type != 'application/json':
        print("❌ Unsupported Content-Type:", content_type)
        return jsonify({"error": "Unsupported Media Type"}), 415

    try:
        data = request.get_json(force=True)
        if not data:
            print("❌ No data in request")
            return jsonify({"error": "No JSON payload received"}), 400

        print("📦 Payload received:")
        print(json.dumps(data, indent=2))

        action_type = request.headers.get("X-GitHub-Event", "").upper()
        print("📌 Event Type:", action_type)

        if action_type == "PUSH":
            pusher = data.get("pusher", {})
            head_commit = data.get("head_commit", {})

            author = pusher.get("name", "Unknown")
            to_branch = data.get("ref", "").split("/")[-1]
            request_id = head_commit.get("id", "N/A")
            from_branch = None

            print("👤 Author:", author)
            print("🌿 Branch:", to_branch)
            print("🪪 Commit ID:", request_id)

        elif action_type == "PULL_REQUEST":
            pr = data.get("pull_request", {})
            author = pr.get("user", {}).get("login", "Unknown")
            from_branch = pr.get("head", {}).get("ref", "unknown")
            to_branch = pr.get("base", {}).get("ref", "unknown")
            request_id = str(pr.get("id", "N/A"))

            print("👤 Author:", author)
            print("🔄 From:", from_branch, "➡️ To:", to_branch)
            print("🪪 Pull Request ID:", request_id)

        elif action_type == "MERGE":
            print("ℹ️ MERGE event received - skipping.")
            return jsonify({"message": "MERGE event handling skipped"}), 200

        else:
            print(f"ℹ️ Ignored event type: {action_type}")
            return jsonify({"message": f"Ignored event type: {action_type}"}), 200

        document = {
            "request_id": request_id,
            "author": author,
            "action": action_type,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        result = collection.insert_one(document)
        document["_id"] = str(result.inserted_id)  # Convert ObjectId to string
        print("✅ Stored in DB:", document)
        return jsonify({"message": "✅ Data stored successfully", "data": document}), 200

    except Exception as e:
        print("❌ Exception occurred while handling webhook:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/actions', methods=['GET'])
def fetch_actions():
    data = list(collection.find().sort("timestamp", -1).limit(10))
    for doc in data:
        doc["_id"] = str(doc["_id"])
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
