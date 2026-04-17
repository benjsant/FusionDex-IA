# 🧬 FusionAI Dex - Claude Context

## 🎯 Project Goal

FusionAI Dex is an intelligent Pokédex for Pokémon Infinite Fusion.

The goal is to progressively build a complete data-driven application that demonstrates:

- data engineering (ETL)
- backend API development
- database design
- optional AI integration

This is a long-term project and does NOT require a full MVP immediately.

---

## 🧠 Development Philosophy

This project is developed progressively.

Focus on:
- clean architecture
- incremental progress
- learning and experimentation
- visible GitHub activity

Do NOT rush to complete everything.

---

## 🧱 Tech Stack (STRICT)

Backend:
- FastAPI (Python)

Database:
- PostgreSQL

Frontend:
- Next.js

Data pipeline:
- Python ETL scripts

Orchestration:
- Prefect (optional, later stage)

Automation:
- n8n (optional, later stage)

AI:
- optional (simple implementation)

Dependencies:
- uv (Python package manager)

---

## 🐳 Docker Requirements

The project should be containerized using Docker Compose.

Services:

- backend → FastAPI
- db → PostgreSQL
- frontend → Next.js
- etl → Python scripts

Optional later:
- prefect
- n8n

Keep Docker setup simple at first.

---

## ⚠️ Priorities (in order)

1. Basic ETL pipeline
2. PostgreSQL schema
3. Simple API
4. Basic frontend
5. Optional AI features

---

## ❌ What NOT to do

- Do NOT implement full fusion system
- Do NOT overengineer architecture
- Do NOT create unnecessary microservices
- Do NOT optimize performance prematurely
- Do NOT add complex AI systems

---

## 🧬 Data Source Strategy

Primary:
- Game files (preferred)

Secondary:
- MediaWiki API

Avoid heavy scraping unless necessary.

---

## 🗄️ Database Schema (Initial)

Table: pokemon

Fields:
- id (int)
- name (string)
- type1 (string)
- type2 (string, optional)
- hp (int)
- attack (int)
- defense (int)
- sp_attack (int)
- sp_defense (int)
- speed (int)
- sprite_path (string)

This schema can evolve over time.

---

## 🔄 ETL Requirements

Start simple.

Steps:
1. Extract Pokémon data
2. Transform into structured JSON
3. Load into PostgreSQL

Prefer clarity over complexity.

---

## 🌐 API Requirements

Initial endpoints:

- GET /pokemon
- GET /pokemon/{id}
- GET /search?name=

Can be extended later.

---

## 🖥️ Frontend Requirements

Minimal interface:

- list Pokémon
- search
- detail page

No complex UI required.

---

## 🤖 AI Feature (Optional)

Simple natural language search.

Example:
"fast fire pokemon"

Translate to database query.

No complex ML required.

---

## 🧪 Code Guidelines

- Keep code simple and readable
- Use type hints
- Avoid unnecessary abstraction
- Prefer small modules
- Write maintainable code

---

## 📁 Project Structure

/backend
/etl
/frontend
/data
/docker

---

## 🧠 How Claude Should Work

When helping:

1. First analyze existing code
2. Explain current structure
3. Propose improvements
4. Implement step by step

Do NOT:
- rewrite everything at once
- introduce unnecessary complexity

---

## 🚀 Development Strategy

Build incrementally:

1. ETL (basic extraction)
2. Database (schema + insert)
3. API (basic endpoints)
4. Frontend (minimal UI)
5. Enhancements (AI, automation)

---

## 🎯 Success Criteria

- Continuous progress
- Clean and understandable code
- Functional components (even partial)
- Good project structure

---

## 💬 Important

This is a learning and portfolio project.

Prioritize:
- clarity
- simplicity
- consistency
- progress over perfection