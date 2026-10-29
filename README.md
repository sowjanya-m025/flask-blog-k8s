# Distributed Flask Blog on Kubernetes

A small Flask app that **simulates how a load balancer picks a pod**. Three simulated pods
(Alpha, Beta, Gamma) have CPU and memory values that drift every 3 seconds. When you publish a
blog post, the app scores each pod, sends the post to the least-loaded one, and shows the decision
and the pods it rejected. The dashboard polls live metrics, and you can spike a pod's load to
watch the decision change.

Score = `CPU × 0.6 + Memory × 0.4` (lower is better).

It also ships with a `Dockerfile` and Kubernetes manifests (3 replicas behind a `LoadBalancer`
service), so it doubles as a hands-on Kubernetes demo.

## Project structure

| Path | Purpose |
| ---- | ------- |
| `app.py` | Flask app: pod simulation, scoring, routes |
| `templates/index.html` | Dashboard UI (self-contained; loads Google Fonts) |
| `Dockerfile` | Container image (Python 3.11 slim, port 5001) |
| `k8s/deployment.yaml` | Deployment: 3 replicas, CPU/memory requests and limits |
| `k8s/service.yaml` | `LoadBalancer` service, port 80 → 5001 |
| `tests/test_app.py` | Unit tests |

## Routes

| Route | Method | Description |
| ----- | ------ | ----------- |
| `/` | GET, POST | Dashboard; POST `title` + `content` publishes a blog |
| `/api/metrics` | GET | JSON with all pods and the current best pod |
| `/api/simulate-load/<pod_id>` | POST | Spikes CPU/memory of `pod-alpha`, `pod-beta` or `pod-gamma` |

## Run locally

```sh
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                        # http://localhost:5001
```

Optional: `FLASK_DEBUG=1 python app.py` enables debug mode, and `PORT=8080` changes the port.

## Tests

```sh
python -m unittest discover -s tests -v
```

## Docker

```sh
docker build -t <your-dockerhub-user>/flask-blog-k8s:latest .
docker run --rm -p 5001:5001 <your-dockerhub-user>/flask-blog-k8s:latest
```

## Kubernetes

`k8s/deployment.yaml` points at the image `sowjanya2510/flask-blog-k8s:latest`. Push your image
under that name, or change the `image:` line to your own, then:

```sh
docker push <your-dockerhub-user>/flask-blog-k8s:latest
kubectl apply -f k8s/
kubectl get pods,svc
```

With Minikube, run `minikube tunnel` (or `minikube service flask-blog-service`) to reach the service.
Clean up with `kubectl delete -f k8s/`.

## Verification status

Checked in an offline sandbox:

- 8 unit tests pass (home page, metrics, scoring, posting, empty input, HTML escaping, load spike, 404).
- The real server started on port 5001 with debug off, and `/`, `/api/metrics` and a POST returned HTTP 200 over the network.
- Both YAML manifests parse as valid Kubernetes `Deployment` and `Service` objects.
- **Not run here:** `docker build` and `kubectl apply` (no Docker or cluster in the sandbox).

## Changes made during review

- `Dockerfile`: `EXPOSE` said 5000 but the app and manifests use 5001. It now says 5001. Added `PYTHONUNBUFFERED=1` so logs show up in `kubectl logs`.
- `app.py`: it ran with `debug=True` on `0.0.0.0`, which exposes the Werkzeug debugger to the network inside a container. Debug is now off unless `FLASK_DEBUG=1`, and the port can be set with `PORT`.
- Added `.gitignore`, `.dockerignore`, tests and this README. The `venv/` folder from the upload (about 15 MB) was left out.

## Known limitations

- Blog posts and metrics live in memory inside each process. With 3 replicas, each real pod simulates its own three pods, so posts disappear on restart and you may see different feeds depending on which replica answers a refresh. A shared store such as Redis would fix this.
- Metrics are random simulated values, not real pod CPU or memory.
- `python app.py` uses Flask's development server. For production, run it with gunicorn.
- `deployment.yaml` has no readiness or liveness probes; `/api/metrics` would work well as one.
- The feed sorts by `HH:MM:SS` text, so ordering can be wrong across midnight.
