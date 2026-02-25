# 🦀 Claw Ops Board

Mobile-first full ops Kanban dashboard for monitoring Claw agent activity, task workflows, and service health.

**Port:** 3004  
**Status:** 🚧 In Development  
**PRD:** [docs/PRD.md](docs/PRD.md)  

## Quick Start

```bash
./run.sh
# → http://localhost:3004
```

## What It Does

- 📋 **Kanban Board** — TODO / In-Progress / Done / Blocked from TODO.md
- 🤖 **Sub-Agent Feed** — Live view of active OpenClaw sessions
- 🟢 **Service Health** — Status of all running services (3000, 3002, 3003, 8080...)
- 🦀 **Claw Status** — Last heartbeat, active sessions, today's summary
- 📱 **Mobile-First** — Built for phone, works on desktop

## Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Vanilla HTML/CSS/JS + Tailwind CSS
- **Data:** File reads (TODO.md, memory/) + HTTP health checks
