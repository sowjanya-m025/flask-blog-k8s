# Commit messages for flask-blog-k8s

Run these inside the project folder. The first block makes sure your commits are
credited to the right GitHub account.

```sh
git init -b main
git config user.name "sowjanya-m025"
git config user.email "sowjanyamurgesh04@gmail.com"
```

## Commits

```sh
git add .gitignore .dockerignore
git commit -m "chore: add gitignore and dockerignore"

git add requirements.txt app.py templates
git commit -m "feat: add Flask blog app with simulated pod load balancer" \
           -m "Debug mode is opt-in via FLASK_DEBUG and the port is configurable via PORT."

git add Dockerfile
git commit -m "feat(docker): add Dockerfile exposing port 5001"

git add k8s
git commit -m "feat(k8s): add deployment with 3 replicas and LoadBalancer service"

git add tests
git commit -m "test: add unit tests for routes, scoring and input escaping"

git add README.md COMMIT_MESSAGES.md
git commit -m "docs: add README and commit message guide"
```

## Push

Create an empty repo on GitHub first, then:

```sh
git remote add origin https://sowjanya-m025@github.com/sowjanya-m025/<repo-name>.git
git push -u origin main
```

Use a Personal Access Token as the password.
