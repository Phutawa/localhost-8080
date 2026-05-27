# AIOS Git Submodule Shared Runtime Guide

This guide explains how to use **Git Submodules** to share the AIOS core engine (`AI Agentic` folder) as a central component across multiple project workspaces, allowing automatic updates.

---

## 1. Concept: Central Core & Scoped Workspaces

Using submodules allows you to keep a single central repository for the AIOS engine (the "Core") and pull it into various projects (the "Workspaces") as a read-only dependency, yet still editable locally if needed.

```text
       ┌───────────┐ (Your central Git Repository)
       │ aios-core │ (e.g. https://github.com/username/aios-core)
       └─────┬─────┘
             │
     ┌───────┼───────┐ (Registered as a Submodule)
     ▼               ▼
┌─────────┐     ┌─────────┐
│ Project │     │ Project │ (Independent Workspaces)
│ Website │     │ Database│
└─────────┘     └─────────┘
```

---

## 2. Step-by-Step Implementation

### Step 2.1: Turn the Core Engine into a Git Repository
You must first initialize Git in the `AI Agentic` directory and push it to a remote Git hosting service (e.g. GitHub, GitLab):

1. **Initialize Git & Commit Files:**
   ```bash
   cd "/Users/phutawanmueangma/Documents/Project/AI Agentic"
   git init
   git add .
   git commit -m "feat: initial commit of AIOS core engine"
   ```
2. **Push to GitHub/GitLab:**
   Create a new blank repository on your account (let's say named `aios-core`). Then, run:
   ```bash
   git remote add origin https://github.com/<your-username>/aios-core.git
   git branch -M main
   git push -u origin main
   ```

---

### Step 2.2: Add Submodule to a Project Workspace
Once the core repository is online, you can link it to any of your projects. Let's do it for `/Users/phutawanmueangma/Documents/Project/TarotCardReading`:

1. **Go to the project directory and initialize git:**
   ```bash
   cd "/Users/phutawanmueangma/Documents/Project/TarotCardReading"
   git init
   ```
2. **Add the Submodule:**
   This command downloads your core engine into a folder named `aios-core` inside the project:
   ```bash
   git submodule add https://github.com/<your-username>/aios-core.git aios-core
   git commit -m "chore: add aios-core submodule"
   ```

---

### Step 2.3: Install and Use inside the Project Workspace
Once the submodule is added:

1. **Activate your project virtual environment and install the package:**
   ```bash
   cd "/Users/phutawanmueangma/Documents/Project/TarotCardReading"
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e aios-core/
   ```
2. **Execute workflows using the local files:**
   Since the core files are now in the `aios-core` folder:
   ```bash
   aios -w bug_fix_pipeline.yaml -s . --agents-dir aios-core/agents
   ```

---

## 3. How to Update Submodules

### Scenario A: You updated the Core Engine code
If you edit agent profiles or runtime code in the central `aios-core` repository:
1. Commit and push changes inside the core repository.
2. In any project workspace using the submodule, run:
   ```bash
   git submodule update --remote --merge
   ```
   This will automatically pull the newest agent profiles and runtime improvements into your project workspace!

### Scenario B: Cloning a Project from scratch
If you clone a project workspace that already has a submodule configured, you must initialize the submodule after cloning:
```bash
git clone https://github.com/username/my-project-workspace.git
cd my-project-workspace
git submodule update --init --recursive
```
This fetches the core engine files automatically!
