
import os
import sys
import time
import asyncio
from typing import Optional, List, Dict, Any

# High-level FastMCP layer
from mcp.server.fastmcp import FastMCP

# ============================
# Server metadata
# ============================
SERVER_NAME = "cmd"
SERVER_VERSION = "0.2.0"

# ============================
# Generic configuration (edit via env)
# ============================
# WORKING_DIR: base directory where all file ops & commands run
# CMD_TIMEOUT: max seconds to wait for a command before killing it
# CMD_MAX_OUTPUT_BYTES: truncate stdout/stderr capture to this many bytes
ROOT_DIR = os.path.abspath(os.environ.get("WORKING_DIR", os.getcwd()))
CMD_TIMEOUT = float(os.environ.get("CMD_TIMEOUT", "30"))
MAX_BYTES = int(os.environ.get("CMD_MAX_OUTPUT_BYTES", "65536"))

mcp = FastMCP(SERVER_NAME)
try:
    mcp.settings.server_version = SERVER_VERSION
except Exception:
    pass

# ============================
# Utilities
# ============================
def _ensure_cwd() -> str:
    """Make sure the working directory exists and return it."""
    if not os.path.isdir(ROOT_DIR):
        os.makedirs(ROOT_DIR, exist_ok=True)
    return ROOT_DIR

def _truncate_bytes(data: bytes, limit: int) -> (bytes, bool):
    if len(data) <= limit:
        return data, False
    return data[:limit], True

async def _run_shell_command(command: str, timeout: float, cwd: str) -> Dict[str, Any]:
    """Run a shell command (cross-platform)."""
    start = time.time()
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )

    timed_out = False
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        timed_out = True
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        stdout, stderr = await proc.communicate()

    code = proc.returncode if proc.returncode is not None else -1

    stdout_trunc, out_trunc = _truncate_bytes(stdout or b"", MAX_BYTES)
    stderr_trunc, err_trunc = _truncate_bytes(stderr or b"", MAX_BYTES)

    return {
        "command": command,
        "cwd": cwd,
        "exit_code": code,
        "timed_out": timed_out,
        "duration_sec": round(time.time() - start, 3),
        "stdout": stdout_trunc.decode(errors="replace"),
        "stderr": stderr_trunc.decode(errors="replace"),
        "stdout_truncated": out_trunc,
        "stderr_truncated": err_trunc,
        "stdout_bytes": len(stdout or b""),
        "stderr_bytes": len(stderr or b""),
        "stdout_limit": MAX_BYTES,
        "stderr_limit": MAX_BYTES,
    }

async def _run_subprocess(argv: List[str], timeout: float, cwd: str, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Run a binary without shell (safer for Python)."""
    start = time.time()
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env or os.environ.copy(),
    )

    timed_out = False
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        timed_out = True
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        stdout, stderr = await proc.communicate()

    code = proc.returncode if proc.returncode is not None else -1

    stdout_trunc, out_trunc = _truncate_bytes(stdout or b"", MAX_BYTES)
    stderr_trunc, err_trunc = _truncate_bytes(stderr or b"", MAX_BYTES)

    return {
        "argv": argv,
        "cwd": cwd,
        "exit_code": code,
        "timed_out": timed_out,
        "duration_sec": round(time.time() - start, 3),
        "stdout": stdout_trunc.decode(errors="replace"),
        "stderr": stderr_trunc.decode(errors="replace"),
        "stdout_truncated": out_trunc,
        "stderr_truncated": err_trunc,
        "stdout_bytes": len(stdout or b""),
        "stderr_bytes": len(stderr or b""),
        "stdout_limit": MAX_BYTES,
        "stderr_limit": MAX_BYTES,
    }

def _resolve_path_in_workdir(path: str) -> str:
    base = _ensure_cwd()
    return os.path.abspath(os.path.join(base, path)) if not os.path.isabs(path) else os.path.abspath(path)

# ============================
# MCP tools
# ============================
@mcp.tool()
async def run_cmd(command: str) -> Dict[str, Any]:
    """Execute a shell command inside WORKING_DIR (uses system shell)."""
    cwd = _ensure_cwd()
    return await _run_shell_command(command, CMD_TIMEOUT, cwd)

@mcp.tool()
def list_dir(path: Optional[str] = None, recursive: bool = False) -> Dict[str, Any]:
    """List files under WORKING_DIR or under the provided path (absolute or relative)."""
    base = _ensure_cwd()
    full = _resolve_path_in_workdir(path) if path else base

    entries: List[Dict[str, Any]] = []
    if recursive:
        for root, dirs, files in os.walk(full):
            for d in dirs:
                p = os.path.join(root, d)
                entries.append({"name": d, "path": p, "is_dir": True, "size": 0})
            for f in files:
                p = os.path.join(root, f)
                try:
                    size = os.path.getsize(p)
                except Exception:
                    size = None
                entries.append({"name": f, "path": p, "is_dir": False, "size": size})
    else:
        with os.scandir(full) as it:
            for entry in it:
                try:
                    size = os.path.getsize(entry.path) if entry.is_file() else 0
                except Exception:
                    size = None
                entries.append(
                    {"name": entry.name, "path": entry.path, "is_dir": entry.is_dir(), "size": size}
                )
    return {"base": base, "requested": path or ".", "recursive": recursive, "count": len(entries), "entries": entries}

@mcp.tool()
def read_text(path: str, max_chars: int = 65536, encoding: str = "utf-8") -> Dict[str, Any]:
    """Read a text file from WORKING_DIR-scoped path."""
    base = _ensure_cwd()
    full = _resolve_path_in_workdir(path)

    info: Dict[str, Any] = {
        "base": base,
        "path": full,
        "exists": os.path.exists(full),
        "is_file": False,
        "encoding": encoding,
        "truncated": False,
        "length": 0,
        "content": "",
        "max_chars": max_chars,
    }

    if not os.path.exists(full) or not os.path.isfile(full):
        return info

    info["is_file"] = True
    try:
        with open(full, "r", encoding=encoding, errors="replace") as f:
            data = f.read()
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
        return info

    info["length"] = len(data)
    if len(data) > max_chars:
        info["content"] = data[:max_chars]
        info["truncated"] = True
    else:
        info["content"] = data
    return info

@mcp.tool()
def write_text(path: str, content: str, mode: str = "w", encoding: str = "utf-8") -> Dict[str, Any]:
    """Write a text file under WORKING_DIR."""
    base = _ensure_cwd()
    full = _resolve_path_in_workdir(path)

    info: Dict[str, Any] = {
        "base": base,
        "path": full,
        "mode": mode,
        "encoding": encoding,
        "success": False,
        "bytes_written": 0,
    }

    try:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, mode, encoding=encoding, errors="replace") as f:
            f.write(content)
        info["success"] = True
        info["bytes_written"] = len(content.encode(encoding, errors="replace"))
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"

    return info

@mcp.tool()
async def run_python_file(path: str, args: Optional[List[str]] = None, python_exe: Optional[str] = None) -> Dict[str, Any]:
    """Execute an existing Python script."""
    cwd = _ensure_cwd()
    script = _resolve_path_in_workdir(path)
    py = python_exe or (sys.executable or "python")
    argv = [py, script] + (args or [])
    return await _run_subprocess(argv, CMD_TIMEOUT, cwd)

@mcp.tool()
async def run_python(code: str, filename: str = "inline_script.py", python_exe: Optional[str] = None) -> Dict[str, Any]:
    """Execute inline Python code by saving it to a temp file under WORKING_DIR/temp."""
    cwd = _ensure_cwd()
    tmp_dir = os.path.join(cwd, "temp")
    os.makedirs(tmp_dir, exist_ok=True)

    safe_name = os.path.basename(filename) or "inline_script.py"
    if not safe_name.endswith(".py"):
        safe_name += ".py"
    full_path = os.path.abspath(os.path.join(tmp_dir, safe_name))

    try:
        with open(full_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(code)
    except Exception as e:
        return {"error": f"Failed to write temp script: {type(e).__name__}: {e}", "path": full_path}

    py = python_exe or (sys.executable or "python")
    argv = [py, full_path]
    result = await _run_subprocess(argv, CMD_TIMEOUT, cwd)
    result["path"] = full_path
    return result

# ============================
# Entrypoint
# ============================
if __name__ == "__main__":
    # FastMCP uses STDIO by default
    mcp.run()
