# Claw Ops Board — PRD
**v1.0 · 2026-02-25 · Port 3004**

---

## Problem
No mobile visibility into Claw's operations. Existing Streamlit dashboard (8501) is desktop-only. Tasks, agents, and service health are scattered.

## Goal
Single mobile-first dashboard: see what's running, what's queued, what's broken — and act on it from a phone.

---

## Features

### MVP
| Feature | Description |
|---------|-------------|
| Kanban Board | 4 columns from TODO.md: Todo / In Progress / Done / Blocked |
| Sub-Agent Feed | Live list of active OpenClaw sessions + kill button |
| Service Health | HTTP ping grid for all running services |
| Claw Status | Last heartbeat, active session count, today's summary |
| Auto-refresh | Every 10s, no manual reload needed |

### V1.1
- Move/complete tasks from UI (writes back to TODO.md)
- Resource usage panel (tokens + cost per session)
- Filter/search tasks by tag or status
- PWA manifest (installable on phone)

---

## Data Sources
| Data | Source |
|------|--------|
| Tasks | `TODO.md` — parsed into kanban columns |
| Sub-agents | OpenClaw sessions API |
| Service health | HTTP health checks (3000, 3002, 3003, 8080…) |
| Heartbeat | `memory/heartbeat-state.json` |

---

## Tech Stack
| Layer | Choice | Reason |
|-------|--------|--------|
| Backend | FastAPI | Consistent with other projects |
| Frontend | Vanilla JS + Tailwind CSS | No build step, fast, mobile-friendly |
| Data | File reads + HTTP polling | No new DB needed |
| Deploy | Systemd service | Auto-restart |

---

## Services to Monitor
| Service | Port |
|---------|------|
| Revenue API | 3000 |
| QR Studio | 3002 |
| PDF Studio | 3003 |
| Claw Ops (self) | 3004 |
| Dashboard API | 8080 |
| Legacy Dashboard | 8501 |

---

## Design
- **Mobile-first:** 375px min-width, no horizontal scroll, 44px touch targets
- **Theme:** Dark by default (`#0f1117` bg, `#1a1d27` cards)
- **Status colors:** Todo=red, In Progress=amber, Done=green, Blocked=purple

---

## API Endpoints
```
GET  /api/tasks           → Parsed TODO.md
GET  /api/agents          → Active sub-agents
GET  /api/health          → All service statuses
GET  /api/status          → Claw heartbeat + session count
POST /api/tasks/{id}/move → Move task to new column
POST /api/agents/{id}/kill → Terminate sub-agent
```

---

## File Structure
```
claw-ops-dashboard/
├── backend/
│   ├── main.py       ← FastAPI app
│   ├── tasks.py      ← TODO.md parser
│   ├── agents.py     ← OpenClaw integration
│   └── health.py     ← Service health checks
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/PRD.md
├── run.sh
└── README.md
```

---

## Milestones
| Phase | Deliverables |
|-------|-------------|
| 1 — Foundation | FastAPI backend + TODO.md parser + health checks + basic mobile UI live on 3004 |
| 2 — Ops Features | Sub-agent feed, Claw status panel, task move/complete, auto-refresh |
| 3 — Polish | Kill sub-agent from UI, PWA manifest, Nginx exposure |

---

## Open Questions
1. Task moves — write to TODO.md or separate state DB?
2. Quant system port — include in health monitor?
3. Nginx — public with basic auth, or internal-only?

---

## Done When
- Board loads on phone in < 3s
- No horizontal scroll at 375px
- Tasks moveable from mobile
- Auto-updates without refresh
