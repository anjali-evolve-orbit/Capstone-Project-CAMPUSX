# CAMPUSX — Discover People Behind the Work System

CAMPUSX is a campus-focused academic and research discovery platform designed to help students, faculty, and scholars discover researchers, academic contributions, papers, research areas, communities, and collaboration networks across institutions.

---

## 🏛️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│        Python CustomTkinter Desktop Client (Frontend)         │
│  (Landing, Login, Register, Dashboard, Directory, Network)   │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP / JSON REST Calls
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    API Client (requests)                     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 FastAPI Backend Service                      │
│     (/api/auth, /api/ecosystem, /api/researchers,            │
│      /api/papers, /api/network, /api/recommendations)        │
└───────────────┬──────────────────────────────┬───────────────┘
                │                              │
                ▼                              ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│    Data Structures Layer     │ │     Python Service Layer    │
│  • Graph ADT (Adjacency List)│ │  • Ecosystem Service        │
│  • BFS (Shortest Path Finding│ │  • Auth Service             │
│  • DFS (Cluster Detection)   │ │  • Research Service         │
│  • Categorized Search Index  │ │  • Network Service          │
│  • Jaccard Overlap Recommender│ └──────────────┬──────────────┘
└──────────────────────────────┘                │
                                                ▼
                                 ┌─────────────────────────────┐
                                 │   MySQL Relational Database │
                                 │  • Normalized Relational DDL│
                                 │  • Connection Pooling       │
                                 └─────────────────────────────┘
```

---

## 🎨 Brand Identity & Design System

- **Project Name**: `CAMPUSX`
- **Tagline**: `Discover People Behind the Work System`
- **Design Palette**:
  - Deep Navy: `#0B1F33`
  - Academic Blue: `#1E4E8C`
  - Bright Blue: `#3B82F6`
  - Purple: `#6C5CE7`
  - Cyan: `#22C7E8`
  - Soft Background: `#F6F8FC`
  - Card Background: `#FFFFFF`
  - Dark Text: `#0F172A`
  - Secondary Text: `#64748B`
  - Border: `#E2E8F0`

---

## 🧠 Data Structures & Algorithms

| Module | Data Structure / Algorithm | Technical Role in CAMPUSX |
| :--- | :--- | :--- |
| `data_structures/graph.py` | **CollaborationGraph (Adjacency List)** | Stores researchers as nodes and academic co-authorship relationships as weighted edges. |
| `data_structures/bfs.py` | **Breadth-First Search (BFS)** | Calculates minimum degrees-of-separation paths between any two campus scholars with step-by-step collaboration justifications. |
| `data_structures/dfs.py` | **Depth-First Search (DFS)** | Explores alternative collaborative routes and identifies connected research clusters across campus departments. |
| `data_structures/search.py` | **Categorized Search Index** | Performs multi-token relevance scoring categorized into Researchers, Papers, Research Areas, and Communities. |
| `data_structures/recommendation.py` | **Jaccard & Area Overlap Similarity** | Computes affinity scores between user interests and researcher publications, generating clear natural-language explanations. |

---

## 🗄️ Normalized MySQL Database Schema

The database follows a normalized relational structure:
- `campuses`: Campus entity (St. John Technical & Educational Campus, etc.)
- `institutions`: Academic institutions (SJCEM, SJIPR, SJCHS, Other)
- `departments`: Academic programs & branches linked to institutions
- `users`: Authenticated user accounts with role (`Student`, `Researcher`, `Faculty`, `Other`)
- `researchers`: Academic scholar profiles with citations, h-index, and affiliations
- `research_areas`: Research topics and disciplines
- `researcher_areas`: Many-to-many relationship mapping scholars to research areas
- `papers`: Research publication metadata (title, abstract, year, venue, citations)
- `paper_authors`: Many-to-many relationship mapping papers to researcher authors
- `paper_areas`: Many-to-many relationship mapping papers to research disciplines
- `communities`: Academic laboratories, research groups, and technical societies
- `community_members`: Membership mapping scholars to communities
- `collaborations`: Explicit co-authorship collaboration graph edges

---

## 🚀 Setup & Execution Guide

### 1. Requirements
Ensure Python 3.10+ and MySQL 8.0+ are installed and the MySQL service is running.

### 2. Configure Environment (`.env`)
Configure your MySQL credentials in `.env`:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=campusx_db

API_HOST=127.0.0.1
API_PORT=8000
API_BASE_URL=http://127.0.0.1:8000
```

### 3. Initialize & Seed MySQL Database
Run the setup script:
```bash
python setup_db.py
```
This automatically creates `campusx_db`, builds all normalized tables via `database/schema.sql`, and inserts realistic seed data via `database/seed.sql`.

### 4. Launch Desktop Application
Run:
```bash
python main.py
```
`main.py` automatically initializes the FastAPI backend and opens the CustomTkinter desktop interface.

### 5. Run Automated Tests
```bash
python -m unittest tests/test_campusx.py
```

---

## 🔑 Default Demo Accounts

| Role | Email | Password |
| :--- | :--- | :--- |
| **Student** | `student@campusx.edu` | `CampusX@2026` |
| **Faculty / Lead Scholar** | `nilesh.patil@campusx.edu` | `CampusX@2026` |
| **Researcher** | `sneha.more@campusx.edu` | `CampusX@2026` |
