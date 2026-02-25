"""
Claw Ops Dashboard - FastAPI Backend
Real-time agent activity from OpenClaw
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Configuration
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


def get_sessions() -> list[dict[str, Any]]:
    """Read sessions directly from OpenClaw's session file."""
    sessions_file = Path("/root/.openclaw/agents/main/sessions/sessions.json")
    if not sessions_file.exists():
        return []
    
    try:
        data = json.loads(sessions_file.read_text())
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Error reading sessions: {e}")
        return {}


def parse_session_key(key: str) -> dict[str, str]:
    """Parse session key to get type and info."""
    parts = key.split(":")
    
    if len(parts) >= 3:
        if parts[0] == "agent":
            if parts[2] == "cron":
                return {"type": "cron", "name": key, "label": "Cron Job"}
            elif parts[2] == "subagent":
                return {"type": "subagent", "name": key, "label": "Sub-Agent"}
            else:
                return {"type": "agent", "name": key, "label": "Agent"}
        elif parts[0] == "telegram":
            return {"type": "telegram", "name": key, "label": f"Telegram ({parts[1]})"}
    
    return {"type": "other", "name": key, "label": key}


@app.get("/api/tasks")
def get_tasks() -> dict[str, list[dict[str, Any]]]:
    """
    Get tasks from real agent activity.
    - in_progress: active sessions (updated within last 5 minutes)
    - done: recently completed (no recent activity but had activity today)
    - todo: cron jobs that are scheduled
    """
    sessions = get_sessions()
    now = datetime.now()
    five_min_ago = now - timedelta(minutes=5)
    one_hour_ago = now - timedelta(hours=1)
    
    in_progress = []
    done = []
    
    for key, session in sessions.items():
        info = parse_session_key(key)
        updated_at = session.get("updatedAt", 0)
        
        # Convert timestamp (it's in milliseconds)
        if updated_at:
            try:
                session_time = datetime.fromtimestamp(updated_at / 1000)
            except:
                session_time = now
        else:
            session_time = now
        
        # Get task info - prefer origin label, then label, then model, then key
        origin = session.get("origin", {})
        origin_label = origin.get("label", "") if isinstance(origin, dict) else ""
        
        if origin_label:
            title = origin_label[:60]
        elif session.get("label"):
            title = session.get("label")[:60]
        else:
            title = info["label"] or key.split(":")[-1][:60]
        
        # Calculate age
        age_delta = now - session_time
        if age_delta.total_seconds() < 60:
            age = f"{int(age_delta.total_seconds())}s ago"
        elif age_delta.total_seconds() < 3600:
            age = f"{int(age_delta.total_seconds() / 60)}m ago"
        else:
            age = f"{int(age_delta.total_seconds() / 3600)}h ago"
        
        session_data = {
            "id": session.get("sessionId", key[:16]),
            "title": title[:60],
            "model": session.get("model", session.get("modelProvider", "unknown")),
            "age": age,
            "type": info["type"],
            "key": key,
            "tokens": session.get("totalTokens", 0),
            "channel": session.get("lastChannel", session.get("chatType", "unknown")),
            "user": session.get("origin", {}).get("label", session.get("origin", {}).get("from", ""))[:40],
        }
        
        # Active if updated in last 5 minutes
        if session_time > five_min_ago:
            in_progress.append(session_data)
        elif session_time > one_hour_ago:
            # Could be done or idle
            if info["type"] in ["cron", "subagent"]:
                done.append(session_data)
    
    # Scheduled = cron jobs that are configured (not necessarily running)
    # Todo = tasks queued for agents (could be from a queue system in future)
    scheduled = [
        {"id": "cron-market-am", "title": "Asian Markets Morning Update", "model": "cron", "type": "scheduled"},
        {"id": "cron-market-pm", "title": "Asian Markets Evening Update", "model": "cron", "type": "scheduled"},
    ]
    todo = []
    
    return {
        "in_progress": in_progress,
        "scheduled": scheduled,
        "todo": todo,
        "done": done,
        "blocked": []
    }


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
def get_status() -> dict[str, Any]:
    """Get OpenClaw status - active sessions and system info."""
    sessions = get_sessions()
    now = datetime.now()
    five_min_ago = now - timedelta(minutes=5)
    
    active_count = 0
    for key, session in sessions.items():
        updated_at = session.get("updatedAt", 0)
        if updated_at:
            try:
                session_time = datetime.fromtimestamp(updated_at / 1000)
                if session_time > five_min_ago:
                    active_count += 1
            except:
                pass
    
    return {
        "active_sessions": active_count,
        "total_sessions": len(sessions),
        "last_updated": now.isoformat()
    }


@app.get("/api/agents")
def get_agents() -> list[dict[str, Any]]:
    """Get all active agents/sessions with more details."""
    sessions = get_sessions()
    now = datetime.now()
    five_min_ago = now - timedelta(minutes=5)
    
    active = []
    for key, session in sessions.items():
        info = parse_session_key(key)
        updated_at = session.get("updatedAt", 0)
        
        if updated_at:
            try:
                session_time = datetime.fromtimestamp(updated_at / 1000)
                is_active = session_time > five_min_ago
            except:
                is_active = False
        else:
            is_active = False
        
        if is_active:
            origin = session.get("origin", {})
            origin_label = origin.get("label", "") if isinstance(origin, dict) else ""
            
            active.append({
                "id": session.get("sessionId", key[:16]),
                "key": key,
                "model": session.get("model", "unknown"),
                "label": origin_label or session.get("label", info["label"]),
                "type": info["type"],
                "updatedAt": updated_at,
                "tokens": session.get("totalTokens", 0),
                "inputTokens": session.get("inputTokens", 0),
                "outputTokens": session.get("outputTokens", 0),
                "channel": session.get("lastChannel", session.get("chatType", "unknown")),
            })
    
    return active


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
