Docker files for hsim repo

Files created in this folder:
- `Dockerfile` - production-oriented Dockerfile that installs `requirements.txt` from the repo root and runs the Flask app with Gunicorn (adjust module path if needed).
- `docker-compose.yml` - development compose config that builds using the repo root as build context and mounts the source into the container for rapid iteration.

Build & run (from repository root):

# Build image using Dockerfile in /docker
docker build -f docker/Dockerfile -t hsim-app:latest .

# Run container
docker run -e PORT=8000 -p 8000:8000 --rm hsim-app:latest

# Using docker-compose (from repo root)
docker-compose -f docker/docker-compose.yml up --build

Notes
- Put a `.dockerignore` file at the repo root to avoid sending large files into the build context. Typical entries:
  __pycache__\n  *.pyc\n  env\n  venv\n  .git\n  data/

- If you don't have `requirements.txt`, create one at repo root (e.g. `pip freeze > requirements.txt`) or list needed deps manually.
- If your app entry point is different from `hsim.GSOM.flask.app:app`, update `CMD` in the Dockerfile accordingly.
