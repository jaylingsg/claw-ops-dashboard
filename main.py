"""
Claw Ops Dashboard - FastAPI Backend
Phase 1: Tasks, Health, Status, Agents endpoints
"""
import asyncio
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Configuration
TASKS_DIR = Path(__file__).parent / "tasks"
PORT = 3004
SERVICES = {
    "Revenue API": "http://localhost:3000",
    "QR Studio": "http://localhost:3002",
    "Documint": "http://localhost:3003",
    "Claw Ops": "http://localhost:3004",
    "Dashboard API": "http://localhost:8080",
    "Legacy Dashboard": "http://localhost:8501",
}

app = FastAPI(title="Claw Ops Dashboard")

# Mount frontend static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent), name="static")


def parse_task_file(filepath: Path) -> list[str]:
    """Parse a task markdown file and return list of tasks."""
    if not filepath.exists():
        return []

    content = filepath.read_text()
    tasks = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            task = line[2:].strip()
            if task:
                tasks.append(task)
    return tasks


@app.get("/api/tasks")
def get_tasks() -> dict[str, list[dict[str, str]]]:
    """Get all tasks from tasks/*.md files."""
    columns = {
        "todo": TASKS_DIR / "todo.md",
        "in_progress": TASKS_DIR / "in-progress.md",
        "done": TASKS_DIR / "done.md",
        "blocked": TASKS_DIR / "blocked.md",
    }

    result = {}
    for key, path in columns.items():
        tasks = parse_task_file(path)
        result[key] = [{"id": f"{key}_{i}", "title": task} for i, task in enumerate(tasks)]

    return result


@app.get("/api/health")
async def get_health() -> dict[str, dict[str, Any]]:
    """Ping all services and return their health status."""
    results = {}

    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in SERVICES.items():
            try:
                response = await client.get(url)
                results[name] = {
                    "status": "up" if response.status_code < 500 else "down",
                    "status_code": response.status_code,
                    "url": url,
                }
            except httpx.ConnectError:
                results[name] = {"status": "down", "status_code": None, "url": url, "error": "connection refused"}
            except httpx.TimeoutException:
                results[name] = {"status": "down", "status_code": None, "url": url, "error": "timeout"}
            except Exception as e:
                results[name] = {"status": "down", "status_code": None, "url": url, "error": str(e)}

    return results


@app.get("/api/status")
async def get_status() -> dict[str, Any]:
    """Get active session count."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8080/api/sessions_list")
            if response.status_code == 200:
                sessions = response.json()
                return {
                    "active_sessions": len(sessions) if isinstance(sessions, list) else 0,
                    "source": "dashboard_api",
                }
    except Exception:
        pass

    return {"active_sessions": 0, "source": "unavailable"}


@app.get("/api/agents")
async def get_agents() -> list[dict[str, Any]]:
    """Get active sub-agents from OpenClaw sessions API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8080/api/sessions_list")
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass

    return []


@app.get("/")
async def root() -> HTMLResponse:
    """Serve the frontend."""
    index_path = Path(__file__).parent / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return HTMLResponse(content="<h1>Claw Ops Dashboard</h1><p>index.html not found</p>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
