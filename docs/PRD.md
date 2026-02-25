# PRD: Claw Ops Board
**Product Name:** Claw Ops Board  
**Version:** 1.0  
**Date:** 2026-02-25  
**Author:** Jay + Claw 🦀  
**Status:** Draft  
**Port:** 3004  

---

## 1. Problem Statement

Jay operates multiple AI agents, automation pipelines, and revenue-generating services from a single server. Currently:

- **No mobile visibility** — The existing Streamlit dashboard (port 8501) is desktop-only. Jay can't monitor or control ops from his phone.
- **Scattered context** — Tasks live in TODO.md, sub-agents run invisibly, service health is unknown unless you SSH in.
- **No unified workflow view** — There's no single place showing the full picture: what's running, what's queued, what's healthy.

---

## 2. Vision

A **mobile-first full ops Kanban board** that gives Jay complete situational awareness of the Claw system — from anywhere, on any device — and lets him take action without opening a terminal.

> *"Glance at my phone, know exactly what Claw is doing, and nudge it if needed."*

---

## 3. Goals

### Must Have (MVP)
- ✅ Mobile-first Kanban board (TODO → IN-PROGRESS → DONE)
- ✅ Live sub-agent activity feed
- ✅ Service health status (all running services with port/status)
- ✅ Heartbeat / last-seen indicator for Claw
- ✅ Task cards with metadata (age, model, status)
- ✅ Works on phone without zooming or horizontal scroll

### Should Have (V1.1)
- ⬜ Add/move/complete tasks from the board
- ⬜ Kill a running sub-agent from the UI
- ⬜ Telegram notification toggle per-task
- ⬜ Resource usage panel (tokens, cost per session)
- ⬜ Filter/search tasks by tag or status

### Nice to Have (Future)
- ⬜ PWA (installable on phone home screen)
- ⬜ Push notifications for task completions
- ⬜ Dark/light mode toggle
- ⬜ Multi-view: Kanban, list, timeline
- ⬜ Log viewer (tail logs in-browser)

### Out of Scope
- ❌ Multi-user / authentication (single-user, local network only)
- ❌ Replacing existing dashboard entirely (runs in parallel)
- ❌ External cloud hosting

---

## 4. Target User

**Jay** — running the system from phone while driving, commuting, or away from desk.

| Need | Priority |
|------|----------|
| See what's happening at a glance | Critical |
| Act on tasks from phone | High |
| Know if something broke | High |
| Detailed logs / debugging | Low (do that on desktop) |

---

## 5. Functional Requirements

### 5.1 Kanban Board

**Columns:**
| Column | Source | Meaning |
|--------|--------|---------|
| 📋 Todo | TODO.md `🔴 TODO` items | Tasks planned but not started |
| 🔄 In Progress | TODO.md `🟡 IN-PROGRESS` + active sub-agents | Currently executing |
| ✅ Done | TODO.md `🟢 DONE` (last 24h) | Recently completed |
| ⚠️ Blocked | TODO.md `⚠️ BLOCKED` | Stuck, needs attention |

**Card Data (per task):**
- Title
- Status badge
- Age (e.g., "2h ago")
- Model/agent ID (if sub-agent)
- Tags (if any)
- Tap-to-expand for description

**Interactions:**
- Swipe / drag card between columns (mobile-friendly)
- Tap to expand full card details
- Long-press or action button to: mark done, move to blocked, delete

### 5.2 Sub-Agent Activity Feed

Real-time panel showing active OpenClaw sub-agents:
- Session key / label
- Task description
- Status (spawning / running / done / failed)
- Elapsed time
- Model used
- Kill button (terminate session)

Data source: OpenClaw sessions API + sub-agent logs.

### 5.3 Service Health Monitor

Card-based status grid for all running services:

| Service | Port | Check Method |
|---------|------|-------------|
| Revenue API | 3000 | HTTP GET /health |
| QR Studio | 3002 | HTTP GET /health |
| PDF Studio | 3003 | HTTP GET /health |
| Claw Ops (self) | 3004 | - |
| Dashboard Legacy | 8501 | HTTP GET |
| Dashboard API | 8080 | HTTP GET /health |
| Quant System | varies | HTTP GET |

Status display: 🟢 Up / 🔴 Down / 🟡 Degraded + response time.

### 5.4 Claw Status Indicator

Shows Claw's presence and recent activity:
- Last heartbeat timestamp
- Current model in use
- Active session count
- Today's task summary (X done, Y in-progress)
- Quick "ping Claw" button (sends a Telegram message)

### 5.5 Data Sources (Backend Integration)

| Data | Source | Method |
|------|--------|--------|
| TODO tasks | `/root/.openclaw/workspace/TODO.md` | File read + parse |
| Sub-agents | OpenClaw API (`/sessions`) | HTTP poll |
| Service health | HTTP health checks | HTTP poll |
| Heartbeat | `memory/heartbeat-state.json` | File read |
| Daily memory | `memory/YYYY-MM-DD.md` | File read |
| Resource usage | OpenClaw session logs | File read / API |

---

## 6. Non-Functional Requirements

### 6.1 Mobile-First Design
- Minimum target: iPhone SE (375px width)
- No horizontal scroll on mobile
- Touch targets ≥ 44px
- Kanban columns stack vertically on mobile (horizontal scroll on tablet)
- Fast load: < 2s on mobile network

### 6.2 Performance
- Auto-refresh every 10 seconds (configurable)
- No heavy JS frameworks (vanilla JS or Preact max)
- Backend: FastAPI (consistent with other projects)
- Sub-50ms API response for task data

### 6.3 Reliability
- If backend is down, frontend shows last-known state with stale indicator
- Service runs as systemd service (auto-restart)
- Graceful degradation: each panel independent (one failure doesn't kill page)

### 6.4 Security
- Local network only (10.240.1.x range)
- No authentication required (trusted network)
- No external API calls from frontend (all via backend proxy)

---

## 7. Technical Architecture

### 7.1 Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Frontend | Vanilla HTML/CSS/JS | No build step, fast, mobile-friendly, easy to iterate |
| CSS Framework | Tailwind CSS (CDN) | Utility-first, great mobile classes |
| Backend | FastAPI (Python) | Consistent with other projects |
| Data | File reads + HTTP health checks | No new DB needed |
| Realtime | Polling every 10s | Simple and reliable (no WebSocket complexity) |
| Process | Systemd service | Auto-start, auto-restart |

### 7.2 API Endpoints (New Backend)

```
GET  /api/tasks          → Parsed TODO.md as JSON
GET  /api/agents         → Active sub-agents from OpenClaw
GET  /api/health         → All service health checks
GET  /api/status         → Claw status (heartbeat, session count)
POST /api/tasks/{id}/move → Move task to new column
POST /api/tasks/{id}/done → Mark task done
POST /api/agents/{id}/kill → Terminate sub-agent session
GET  /api/stream         → SSE stream for real-time updates (future)
```

### 7.3 File Structure

```
projects/claw-ops/
├── docs/
│   ├── PRD.md              ← This file
│   └── IMPLEMENTATION.md   ← Build plan
├── backend/
│   ├── main.py             ← FastAPI app
│   ├── tasks.py            ← TODO.md parser
│   ├── agents.py           ← OpenClaw agent integration
│   ├── health.py           ← Service health checks
│   └── requirements.txt
├── frontend/
│   ├── index.html          ← Main Kanban view
│   ├── app.js              ← UI logic
│   └── style.css           ← Custom styles (supplement Tailwind)
├── run.sh                  ← Start script
└── README.md
```

---

## 8. UX / Design

### 8.1 Mobile Layout (Primary)

```
┌─────────────────────┐
│  🦀 Claw Ops Board  │
│  ● Active · 2 tasks │
├─────────────────────┤
│  SERVICE HEALTH     │
│  [●3000][●3002][●3003]│
├─────────────────────┤
│  ── TODO ──────────│
│  [Task Card]        │
│  [Task Card]        │
├─────────────────────┤
│  ── IN PROGRESS ───│
│  [Task Card] 🔄     │
├─────────────────────┤
│  ── DONE (today) ──│
│  [Task Card] ✅     │
└─────────────────────┘
```

### 8.2 Task Card (Mobile)

```
┌───────────────────────┐
│ 🔴 Expose via Nginx   │
│ In backlog · 1d ago   │
│ [tags: infra, nginx]  │
│          [→ Move ▼]   │
└───────────────────────┘
```

### 8.3 Color Palette
- Background: `#0f1117` (dark, easy on eyes)
- Card: `#1a1d27`
- Todo: `#e74c3c` (red)
- In Progress: `#f39c12` (amber)
- Done: `#27ae60` (green)
- Blocked: `#8e44ad` (purple)
- Accent: Claw orange `#ff6b35`

### 8.4 Theme
- Dark mode by default (phone-friendly, OLED-friendly)
- Light mode toggle (future)

---

## 9. Milestones

### Phase 1: Foundation (Day 1)
- [ ] Backend: FastAPI with TODO.md parser + health checks
- [ ] Frontend: Mobile Kanban layout with static data
- [ ] Integration: Live data flowing to frontend
- [ ] Deploy: Running on port 3004 as systemd service

### Phase 2: Ops Features (Day 2-3)
- [ ] Sub-agent activity feed
- [ ] Claw status indicator
- [ ] Task move/complete from UI
- [ ] 10s auto-refresh

### Phase 3: Polish (Day 4+)
- [ ] Kill sub-agent from UI
- [ ] PWA manifest (installable)
- [ ] Nginx public exposure (with Phase 1 TODO task)
- [ ] Notification integration

---

## 10. Open Questions

1. **Should moves in the UI write back to TODO.md?** Or maintain a separate state DB?
   - *Leaning toward: write back to TODO.md* — single source of truth
2. **OpenClaw sub-agent API** — What endpoint lists active sessions? Need to verify.
3. **Quant system port** — What port is the quant dashboard on? Include in health monitor.
4. **Nginx exposure** — Public access with basic auth, or internal only forever?

---

## 11. Success Criteria

The project is complete when:
- [ ] Jay can open the board on his phone and see current task/agent state in < 3s
- [ ] No horizontal scroll required on a 375px screen
- [ ] Service health is visible at a glance
- [ ] Tasks can be moved/completed from mobile
- [ ] Board auto-updates without manual refresh

---

## Sign-off

| Role | Name | Date |
|------|------|------|
| Product Owner | Jay | 2026-02-25 |
| Developer | Claw 🦀 | 2026-02-25 |

---
*v1.0 — Initial draft. Living document.*
