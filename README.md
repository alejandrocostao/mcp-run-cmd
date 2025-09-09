!!!In the latest update of LM Studio 0.3.25 this no longer works fully.!!!
# MCP RunCmd (Template)

A ready-to-publish **MCP (Model Context Protocol)** server for **LM Studio** to run shell commands and Python code.
This template uses **generic, editable settings** via environment variables so users can easily adapt it to their system.

## ✨ What’s inside
- `runCmd.py` — MCP server (fully working) with clear config knobs.
- `mcp.json` — Example LM Studio config with placeholders you can edit.
- `requirements.txt` — Python deps.
- `.env.example` — Example environment configuration.
- `.gitignore` — Sensible defaults.
- `LICENSE` — MIT.

## ⚙️ Quick start
```bash
# 1) Create and activate a virtualenv (optional but recommended)
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Copy the example env and edit to your needs
cp .env.example .env
# Edit .env to set WORKING_DIR, timeouts, etc.

# 4) Run
modify or add mcp.json LM Studio
```

## 🔩 Configuration (env vars)
- `WORKING_DIR` — Base folder where commands/files operate (default: current directory).
- `CMD_TIMEOUT` — Per-command timeout in seconds (default: 30).
- `CMD_MAX_OUTPUT_BYTES` — Max bytes captured for stdout/stderr (default: 65536).

You can set these in the shell or via `.env` (if you use something like `python-dotenv` yourself). This template **does not** auto-load `.env` to stay dependency-light.

## 🖥️ LM Studio (mcp.json)
Place `mcp.json` next to `runCmd.py` (or point to it in your LM Studio config). Example file is included with placeholders:
```json
{
  "name": "MCP RunCmd",
  "description": "MCP server to run shell commands and Python scripts",
  "binary": "python",                   // or absolute path to python
  "args": ["runCmd.py"],
  "env": {
    "WORKING_DIR": "/ABS/PATH/TO/WORKDIR",
    "CMD_TIMEOUT": "30",
    "CMD_MAX_OUTPUT_BYTES": "65536"
  },
  "autoStart": true
}
```
Edit `WORKING_DIR` to any folder the user should be allowed to operate in.

## 📦 Publish to GitHub
```bash
git init
git add .
git commit -m "Initial release: MCP RunCmd template"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/mcp-run-cmd.git
git push -u origin main
```

## 🔒 Safety notes
This server can execute shell commands. Keep `WORKING_DIR` scoped to a safe directory and consider running under a restricted user.

## 📜 License
MIT
