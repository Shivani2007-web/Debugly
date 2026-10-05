# Debugly

> **Don't just fix the bug. Understand it.**
> An AI tutor that finds the misconception *behind* the mistake.

Debugly is an AI-powered coding-learning environment that analyzes how a student
codes and debugs, identifies the **conceptual misconception** behind repeated
mistakes, guides the learner toward understanding with a **Socratic tutor**
(instead of handing over the answer), and adapts future practice to the concepts
each learner needs most.

Debugly is **not** a generic AI coding assistant. Its core principle:

> *Understand why the student is making the mistake, then teach the student how to think through it.*

---

## Table of contents

- [Why Debugly](#why-debugly)
- [Feature overview](#feature-overview)
- [How it works](#how-it-works)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Running the app](#running-the-app)
- [Key API endpoints](#key-api-endpoints)
- [The Debugly Mastery Indicator](#the-debugly-mastery-indicator)
- [Testing](#testing)
- [Security notes](#security-notes)
- [Roadmap / build phases](#roadmap--build-phases)
- [License](#license)

---

## Why Debugly

Most tools tell a student *what* to change. Debugly asks *why they got it wrong*
and helps them reason it out, so the understanding transfers to the next problem.

| A typical assistant says… | Debugly says… |
| --- | --- |
| "Change `range(len(x)+1)` to `range(len(x))`." | "If a list has 3 items, what's the index of the last one? And what does `range(len(list))` give you?" |
| Fixes the line for you. | Detects a recurring **off-by-one** gap, tracks whether the intervention actually helped, and generates a *different* problem that tests the same concept. |

The differentiator, end to end:

```
Repeated mistake
   ↓
Misconception detected   (deterministic analysis — not the LLM guessing)
   ↓
Socratic intervention    (progressive hints, grounded in the detected misconception)
   ↓
Personalized challenge   (concept + difficulty chosen deterministically)
   ↓
Independent success
   ↓
Mastery improves
```

---

## Feature overview

- **VS Code-inspired IDE** — Monaco editor, task panel, run/submit, test results, terminal output.
- **Sandboxed Python execution** — isolated subprocess with timeout, output caps, memory limits, and filesystem/network restrictions.
- **Deterministic misconception engine** — AST + error-pattern + behavioral analysis across ~10 common Python misconceptions, each verdict backed by weighted evidence.
- **Socratic AI tutor (Gemini)** — four progressive hint levels (Question → Direction → Concept → Strong guidance), server-tracked so hints never repeat, with a graceful deterministic fallback when the API is unavailable.
- **Interactive robot companion** — seven emotional states (idle, thinking, concerned, encouraging, happy, celebrating, sad) animated with Framer Motion; it's the visual face of the tutoring interaction.
- **Learner profile + behavior tracking** — meaningful learning events (not keystrokes) aggregated into per-concept stats, with repeated-misconception and intervention-outcome detection.
- **Personalized micro-challenges** — concept and difficulty selected deterministically from the learner profile; Gemini only fills in content under strict constraints; hidden answers never leave the server.
- **Student dashboard** — Debugly Mastery Indicator, concept progress, focus areas, activity timeline, and a knowledge-graph preview.
- **Learner knowledge graph** — an interactive, evidence-derived view: Student → Concept → Misconception → Evidence → Intervention → Challenge → Outcome.
- **Teacher dashboard** — class-level analytics: average mastery, most-common misconceptions, weakest concepts, and students needing attention.
- **Smart Reuse** — classifies pasted code against a task's reuse zones; boilerplate is free to reuse, learning-critical regions are flagged (never blocked), and reuse behavior is recorded.

---

## How it works

The system is a **hybrid**: deterministic program/behavior analysis does the
diagnosis; the LLM only phrases the teaching.

```
Student code
   ↓
Python AST analysis  +  Sandboxed execution  →  compiler / runtime output
   ↓
Feature extraction  (code evidence · error evidence · behavioral evidence)
   ↓
Misconception detection  (weighted rules → DetectedMisconception)
   ↓
Learner state  (deterministic mastery, trends, persistent-gap detection)
   ↓
Gemini tutor  (Socratic hint / explanation / challenge — grounded, never inventing)
   ↓
Student attempts again  →  learner profile updated
```

**Three sources of evidence** feed every misconception verdict, so a diagnosis
is never based on a single weak signal:

- **Code evidence** — AST structure, operators, loops, conditions, indexing, recursion.
- **Error evidence** — exception types, tracebacks, failing tests, expected vs actual.
- **Behavioral evidence** — attempts, repeated errors, hints requested, corrections, progression over time.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js Frontend (App Router · TS · Tailwind · Monaco · FM) │
│  Landing · IDE · Robot tutor · Dashboards · Knowledge graph   │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTPS (centralized typed API client)
┌───────────────▼─────────────────────────────────────────────┐
│  FastAPI Backend (Python · Pydantic)                          │
│                                                               │
│  Execution (sandbox) → Analysis (AST + error + behavior)      │
│      → Misconception engine (deterministic rule registry)     │
│      → Tutor (Gemini behind a provider abstraction + fallback)│
│      → Mastery (deterministic) → Challenges → Knowledge graph │
│      → Teacher analytics                                      │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
        ┌───────▼───────┐            ┌────────▼────────┐
        │   MongoDB     │            │   Gemini API    │
        └───────────────┘            └─────────────────┘
```

Design principles:

- **The LLM never diagnoses.** The deterministic engine owns misconception
  detection; Gemini is given the verdict and may only phrase the intervention.
- **The LLM never computes mastery or picks difficulty.** Those are deterministic.
- **The frontend is a presentation layer.** Every displayed metric comes from a backend endpoint.
- **Everything degrades gracefully** — if Gemini is unavailable or rate-limited, a deterministic fallback keeps the tutoring and challenges working.

---

## Tech stack

| Layer    | Technology |
| -------- | ---------- |
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS, Monaco Editor, Framer Motion |
| Backend  | Python, FastAPI, Pydantic, Motor (async MongoDB driver) |
| Database | MongoDB |
| AI       | Google Gemini (`google-genai`) behind a provider abstraction |
| Testing  | pytest (backend), Vitest + Testing Library (frontend) |

---

## Project structure

```
Debugly/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory + router wiring
│   │   ├── config.py               # Pydantic settings (.env resolved absolutely)
│   │   ├── core/validation.py      # shared input-validation guards
│   │   ├── db/                      # Mongo client + repositories (memory + mongo)
│   │   ├── models/                  # Pydantic domain models
│   │   ├── api/routes/              # execution, analysis, tutor, behavior,
│   │   │                            #   profile, challenges, learner, teacher,
│   │   │                            #   reuse, demo, health
│   │   ├── services/
│   │   │   ├── execution/           # sandbox + runner
│   │   │   ├── analysis/            # AST + error + feature extraction
│   │   │   ├── misconception/       # rule registry + engine + 10 rules
│   │   │   ├── ai/                  # provider abstraction (Gemini + fallback)
│   │   │   ├── tutor/               # Socratic orchestration + hint state
│   │   │   ├── behavior/            # tracker + mastery + profile service
│   │   │   ├── challenge/           # selector + difficulty + generator
│   │   │   ├── learner/             # dashboard + knowledge-graph services
│   │   │   ├── teacher/             # class-level aggregation
│   │   │   ├── reuse/               # Smart Reuse classification
│   │   │   └── demo/                # demo-class seeding
│   │   └── seed/                    # seed tasks
│   ├── tests/                       # pytest suite
│   └── requirements.txt
└── frontend/
    ├── app/                         # routes: /, /dev/health, /ide/[sessionId],
    │                                #   /dashboard/[userId](/knowledge-graph), /teacher
    ├── components/                  # ide, tutor, dashboard, graph, teacher, landing, ui
    ├── lib/                         # api client + pure helpers
    ├── types/                       # TS types mirroring backend models
    └── package.json
```

---

## Getting started

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.11+**
- A running **MongoDB** instance (local `mongodb://localhost:27017` or Atlas)
- A **Gemini API key** (optional — the tutor falls back to deterministic hints without one)

### Backend setup

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\Activate.ps1
# Unix:     source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit values (add your Gemini key)
```

### Frontend setup

```bash
cd frontend
npm install
cp .env.example .env.local    # then edit if your API base differs
```

---

## Environment variables

`backend/.env` (never commit this file — it is gitignored):

| Variable | Purpose | Default |
| --- | --- | --- |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Database name | `debugly` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:3000` |
| `GEMINI_API_KEY` | Gemini key (backend only, **never** exposed to the frontend) | *(empty)* |
| `GEMINI_MODEL` | Gemini model id | `gemini-flash-latest` |

`frontend/.env.local`:

| Variable | Purpose | Default |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the FastAPI backend | `http://localhost:8000/api` |

> The Gemini key lives **only** in the backend. The frontend talks to FastAPI;
> FastAPI talks to Gemini.

---

## Running the app

**Backend** (from `backend/`, with the venv active and MongoDB running):

```bash
uvicorn app.main:app --reload --port 8000
```

**Frontend** (from `frontend/`):

```bash
npm run dev
```

Then open:

| Page | URL |
| --- | --- |
| Product landing | http://localhost:3000 |
| Coding IDE | http://localhost:3000/ide/sum-list |
| Student dashboard | http://localhost:3000/dashboard/demo-ava |
| Knowledge graph | http://localhost:3000/dashboard/demo-ava/knowledge-graph |
| Teacher dashboard | http://localhost:3000/teacher |
| Developer health check | http://localhost:3000/dev/health |
| API docs (Swagger) | http://localhost:8000/docs |

**Demo data:** to populate a sample class for the dashboards, POST to the demo
seed endpoint (or use the "Load demo class" button on the teacher page):

```bash
curl -X POST http://localhost:8000/api/demo/seed
```

---

## Key API endpoints

| Method & path | Purpose |
| --- | --- |
| `GET  /api/health` | Service + database health |
| `GET  /api/tasks` · `GET /api/tasks/{id}` | Task catalog |
| `POST /api/execution/run` | Run code (no grading) |
| `POST /api/execution/submit` | Run code against assertion tests |
| `POST /api/analysis/diagnose` | Deterministic misconception diagnosis |
| `POST /api/tutor/hint` · `/explain` · `/feedback` | Socratic tutor (grounded, progressive) |
| `POST /api/behavior/event` · `/events` | Record meaningful learning events |
| `GET  /api/profile/{userId}/...` | Learner summary, mastery, misconceptions, trend |
| `POST /api/challenges/generate` · `GET /{id}` · `POST /{id}/submit` | Personalized challenges |
| `GET  /api/learner/dashboard` · `/knowledge-graph` | Student analytics |
| `GET  /api/teacher/overview` · `/students` · `/student/{id}` | Class analytics |
| `POST /api/reuse/check` | Smart Reuse classification |
| `POST /api/demo/seed` | Seed a demo class |

Full interactive docs are served at `/docs`.

---

## The Debugly Mastery Indicator

Mastery is a **deterministic 0–100 indicator**, computed from measurable signals:
success rate, self-correction, unaided improvement after a correction, difficulty
progression, repeated-misconception penalty (which decays as the learner
recovers), and hint dependency.

> It is deliberately labeled an **indicator of demonstrated understanding**, not a
> scientifically validated measure of ability. Gemini is never asked to assign it.

---

## Testing

**Backend:**

```bash
cd backend
.venv\Scripts\python.exe -m pytest -q      # Windows
# or: pytest -q
```

**Frontend:**

```bash
cd frontend
npm test            # Vitest
npm run build       # production build
```

Current status: **156 backend tests** and **56 frontend tests** passing, with a
clean production build. Tests run fully offline — the AI path is covered with
stub providers and the deterministic fallback.

---

## Security notes

- The Gemini API key is backend-only and read from `backend/.env` (gitignored).
  It is never shipped to the browser and never placed in `.env.example`.
- Student code runs in an **isolated subprocess sandbox** — isolated-mode
  interpreter, throwaway temp directory, stripped environment, wall-clock
  timeout with process-tree kill, output caps, a script-size limit, blocked
  network, blocked filesystem writes, and a memory cap (POSIX `rlimit`; Windows
  Job Object, best-effort).
- All API inputs are validated (code length, text length, test-case count, NUL rejection).
- If you fork this repo, **rotate any key** that was ever placed in a shared file.

> **MVP sandbox note:** the subprocess sandbox is strong for a local/dev setup.
> For production-grade isolation, swap the sandbox module for a Docker-per-execution
> runner — the execution service is isolated behind a single function to make that clean.

---

## Roadmap / build phases

Debugly was built incrementally, each phase verified before the next:

1. Project setup + connection chain
2. Coding IDE · Monaco · Python execution + results
3. AST analysis · error analysis · misconception engine (10 rules)
4. Gemini integration · Socratic hints · robot companion
5. Behavior tracking · learner profile · deterministic mastery
6. Personalized micro-challenges · adaptive difficulty
7. Student mastery dashboard · learner knowledge graph
8. Smart Reuse · security hardening (folded into the final pass)
9. Final hardening · teacher dashboard · UI/UX product polish

Future directions: real authentication/roles, a Docker-based execution runner,
additional languages, and an ML-assisted misconception classifier layered on top
of the existing deterministic rules.

---

## License

No license has been specified yet. Add one (e.g. MIT) before public distribution.
