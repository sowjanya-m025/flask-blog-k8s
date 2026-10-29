from flask import Flask, render_template, request, jsonify
import os
import socket
import random
import time
import threading

app = Flask(__name__)

# ─── Simulated Pod Registry ────────────────────────────────────────────────────
# In a real cluster each replica runs its own copy; here we simulate 3 pods in
# a single process so the UI can show realistic load-balancer decisions.

PODS = {
    "pod-alpha": {"label": "Pod Alpha 🟢", "cpu": 45, "memory": 90,  "blogs": []},
    "pod-beta":  {"label": "Pod Beta  🔵", "cpu": 50, "memory": 95,  "blogs": []},
    "pod-gamma": {"label": "Pod Gamma 🔴", "cpu": 48, "memory": 92,  "blogs": []},
}

# Background thread that randomly drifts the simulated metrics so the UI always
# shows live, changing numbers and the LB decision can flip over time.
# Large drift range (±20 CPU, ±15 MEM) means pods regularly overtake each other.
def _drift_metrics():
    while True:
        time.sleep(3)
        for pod in PODS.values():
            pod["cpu"]    = max(10, min(90, pod["cpu"]    + random.randint(-20, 20)))
            pod["memory"] = max(30, min(180, pod["memory"] + random.randint(-15, 15)))

threading.Thread(target=_drift_metrics, daemon=True).start()


# ─── Load-balancer logic ───────────────────────────────────────────────────────

def _score(pod):
    """Weighted score: lower = better (less loaded)."""
    return round(pod["cpu"] * 0.6 + pod["memory"] * 0.4, 2)

def choose_best_pod():
    scored = []
    for name, pod in PODS.items():
        scored.append({
            "id":     name,
            "label":  pod["label"],
            "cpu":    pod["cpu"],
            "memory": pod["memory"],
            "score":  _score(pod),
            "blogs":  pod["blogs"],
        })
    scored.sort(key=lambda p: p["score"])
    best     = scored[0]
    rejected = [
        {"label": p["label"], "cpu": p["cpu"],
         "memory": p["memory"], "score": p["score"],
         "reason": "Higher CPU / Memory score"}
        for p in scored[1:]
    ]
    return best, rejected, scored


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    current_real_pod = socket.gethostname()
    decision = None
    best, rejected, all_pods = choose_best_pod()

    if request.method == "POST":
        title   = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if title and content:
            entry = {
                "title":        title,
                "content":      content,
                "processed_by": best["label"],
                "pod_id":       best["id"],
                "timestamp":    time.strftime("%H:%M:%S"),
            }
            PODS[best["id"]]["blogs"].append(entry)

            decision = {
                "selected":  best["label"],
                "score":     best["score"],
                "cpu":       best["cpu"],
                "memory":    best["memory"],
                "rejected":  rejected,
            }

        # Re-fetch after write so scores reflect any tiny drift
        best, rejected, all_pods = choose_best_pod()

    # Flatten all blogs (newest first) for the feed
    all_blogs = []
    for pod in PODS.values():
        all_blogs.extend(pod["blogs"])
    all_blogs.sort(key=lambda b: b["timestamp"], reverse=True)

    return render_template(
        "index.html",
        pods=all_pods,
        current_real_pod=current_real_pod,
        decision=decision,
        all_blogs=all_blogs,
        best_pod=best,
    )


@app.route("/api/metrics")
def api_metrics():
    """Live JSON endpoint polled by the frontend every 3 s."""
    best, rejected, all_pods = choose_best_pod()
    return jsonify(pods=all_pods, best_id=best["id"])


@app.route("/api/simulate-load/<pod_id>", methods=["POST"])
def simulate_load(pod_id):
    """Spike the CPU of a specific pod so viewers can watch the LB react."""
    if pod_id in PODS:
        PODS[pod_id]["cpu"] = random.randint(75, 95)
        PODS[pod_id]["memory"] = random.randint(140, 190)
        return jsonify(ok=True, pod=pod_id)
    return jsonify(ok=False), 404


if __name__ == "__main__":
    # Debug mode exposes the Werkzeug debugger, so it is opt-in:
    #   FLASK_DEBUG=1 python app.py
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5001)),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
