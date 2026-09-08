# Installation Guide

**For:** Nonceba Mdonsela  
**OS:** Pop!_OS / Ubuntu 22.04 (Linux)

Follow these steps **once** before running the pipeline.

---

## 1. What you need to install

### Required software

| Tool | Version | Purpose |
|------|---------|---------|
| **Docker** | Latest | Runs PostgreSQL database |
| **Docker Compose** | v2+ | Starts database with one command |
| **Python** | 3.11+ | Pipeline scripts, forecast, dashboard |
| **pip** | Latest | Installs Python packages |
| **Git** | Any | Version control & GitHub pushes |
| **make** | Any | Shortcut commands (`make pipeline`) |

### Python packages (installed automatically)

These are listed in `requirements.txt` and installed via `pip`:

| Package | Purpose |
|---------|---------|
| pandas | Data cleaning & transformation |
| psycopg2-binary | PostgreSQL connection |
| sqlalchemy | Database ORM |
| prophet | 7-day occupancy forecast |
| streamlit | Dashboard UI |
| plotly | Charts in dashboard |
| pytest | Unit tests |
| dbt-postgres | Warehouse modelling (Week 2) |

---

## 2. Check what's already installed

Run these commands in your terminal:

```bash
python3 --version    # Should show 3.11 or higher
git --version
docker --version     # May say "command not found" — install below
make --version       # May say "command not found" — install below
```

---

## 3. Install Docker (required)

If you see `Command 'docker' not found`, run:

```bash
sudo apt update
sudo apt install docker.io docker-compose-v2 -y
```

Enable Docker and add your user to the docker group:

```bash
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

**Important:** Log out and log back in, OR run:

```bash
newgrp docker
```

Verify Docker works:

```bash
docker --version
docker compose version
docker run hello-world
```

---

## 4. Install make (if missing)

```bash
sudo apt install make -y
```

---

## 5. Install Git (if missing)

```bash
sudo apt install git -y
```

---

## 6. Set up the Python environment

Go to the project folder:

```bash
cd ~/Downloads/data\ en\ cloud\ project/bed-occupancy-pipeline
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your terminal prompt should show `(.venv)` at the start.

Install all Python packages (may take 10–20 minutes on slow internet):

```bash
pip install --upgrade pip
pip install --default-timeout=1000 -r requirements.txt
```

**If download times out**, install in stages (recommended on slow connections):

```bash
pip install --upgrade pip
pip install --default-timeout=1000 -r requirements-core.txt      # Week 1 — ~2 min
pip install --default-timeout=1000 -r requirements-dbt.txt       # Week 2 — ~3 min
pip install --default-timeout=1000 -r requirements-dashboard.txt # Week 3 — ~10 min (pyarrow is large)
```

After `requirements-core.txt` you can already run:

```bash
make pipeline
make test
```

---

## 7. Start the database

Make sure Docker is running, then:

```bash
cd ~/Downloads/data\ en\ cloud\ project/bed-occupancy-pipeline
docker compose up -d
```

Check the database is running:

```bash
docker compose ps
```

Expected output:

```
NAME                    STATUS    PORTS
bed_occupancy_postgres  running   0.0.0.0:5433->5432/tcp
```

---

## 8. Run the pipeline

With `.venv` activated:

```bash
make pipeline      # Step 1: generate data, ingest, aggregate
make forecast      # Step 2: 7-day forecast (optional)
make dashboard     # Step 3: open web dashboard (optional)
make test          # Run unit tests
```

---

## 9. dbt setup (Week 2)

When you reach Week 2 of the commit plan:

```bash
cp dbt/profiles.yml.example dbt/profiles.yml
make dbt-run
make dbt-test
```

> **Note:** `dbt/profiles.yml` contains passwords — never commit it to GitHub.

---

## 10. Full command reference

```bash
# --- ONE-TIME SETUP ---
sudo apt update
sudo apt install docker.io docker-compose-v2 make git -y
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker

cd ~/Downloads/data\ en\ cloud\ project/bed-occupancy-pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d

# --- EVERY TIME YOU WORK ---
cd ~/Downloads/data\ en\ cloud\ project/bed-occupancy-pipeline
source .venv/bin/activate
docker compose up -d          # if not already running
make pipeline
make dashboard
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Command 'docker' not found` | Docker not installed | Follow Section 3 above |
| `permission denied` on docker | User not in docker group | `sudo usermod -aG docker $USER` then log out/in |
| `Cannot connect to Postgres` | Database not running | `docker compose up -d` |
| `pip install` times out on pyarrow | Slow internet — pyarrow is 50MB | Use staged install — see below |
| `ReadTimeoutError` from pip | Network timeout | `pip install --default-timeout=1000 -r requirements-core.txt` |
| `make: command not found` | make not installed | `sudo apt install make -y` |
| Port 5433 already in use | Another service using port | Stop other service or change port in `docker-compose.yml` |
| Dashboard shows error | Pipeline not run yet | Run `make pipeline` first |
| `ModuleNotFoundError` | venv not activated | `source .venv/bin/activate` |

---

## Alternative: PostgreSQL without Docker

If Docker cannot be installed, use local PostgreSQL:

```bash
sudo apt install postgresql postgresql-contrib -y
sudo -u postgres psql -c "CREATE USER de_user WITH PASSWORD 'de_password';"
sudo -u postgres psql -c "CREATE DATABASE hospital_dw OWNER de_user;"
sudo -u postgres psql -d hospital_dw -f sql/init.sql
```

Then change port in `ingest/db_config.py` from `5433` to `5432`.

---

## Verification checklist

Before starting Week 1 commits, confirm:

- [ ] `docker --version` works
- [ ] `docker compose up -d` starts postgres
- [ ] `python3 --version` shows 3.11+
- [ ] `.venv` created and activated
- [ ] `pip install -r requirements.txt` completed without errors
- [ ] `make pipeline` runs successfully
- [ ] `make test` passes
- [ ] `make dashboard` opens in browser

---

**Next step:** Follow [4_WEEK_COMMIT_PLAN.md](4_WEEK_COMMIT_PLAN.md) for GitHub commits. Read [STUDY_NOTES.md](STUDY_NOTES.md) to understand the pipeline flow.
