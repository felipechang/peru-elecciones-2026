# Peru Elecciones 2026 — Project Proposal

## Overview

**Peru Elecciones 2026** is a civic technology platform designed to help voters make informed decisions when selecting
candidates across all electoral categories: President, Vice President, Senator, Deputy, and Andean Parliament.

The platform aggregates official party documents, candidate data, and real-time news into a single, accessible
interface — giving citizens a clear, unbiased view of who is running, what they stand for, and what's being said about
them.

---

## Goals

- Reduce the information gap between voters and candidates.
- Surface structured, comparable data on political parties and their programs.
- Deliver up-to-date candidate news in a digestible format.
- Cover all electoral positions: President, Vice President, Senators, Deputies, and Andean Parliament.

---

## System Architecture

The platform is composed of two core subsystems: the **Generator** and the **Researcher**.

---

## 1. Generator

The Generator is responsible for ingesting official electoral documents and populating the database with structured,
enriched data.

### Data Pipeline

| Source                            | Output                                    |
|-----------------------------------|-------------------------------------------|
| Party folder names                | `parties` table (name, summary)           |
| Estatuto + Ideario (LLM-combined) | `party.summary` field                     |
| Listado de Candidatos             | `candidates` table                        |
| Plan de Gobierno (all parties)    | `topics` table + `party_sections` records |

### Key Processes

**PDF Text Extraction**

- All source documents (Estatuto, Ideario, Listado, Plan de Gobierno) are scanned PDFs processed with **Tesseract OCR**
  to extract raw text before any further processing.
- Extracted text is cleaned and normalized prior to ingestion.

**Party data is ingested once** at the start of the electoral cycle and treated as static — no updates are made after
the initial load.

- Reads party names from folder structure.
- Generates a unified party summary by feeding the OCR-extracted *Estatuto* and *Ideario* text into Ollama (
  `glm-4.7-flash:latest`) to produce a coherent, neutral description.

**Candidate Ingestion**

- Parses the *Listado* document for each party.
- Populates the `candidates` table with: name, position, electoral scope, and list order.

**Topic Extraction**

- Reads all *Plan de Gobierno* documents across parties.
- Extracts a shared `topics` table covering the main policy areas found.
- Splits each plan into topic-aligned sections and stores them as individual records linked to their respective party.

**Events**

- Creates an `events` table to associate news items and notable events with specific candidates.

### Database Schema (summary)

```
parties         — id, name, summary
candidates      — id, party_id, name, position, scope, list_order
topics          — id, name
party_sections  — id, party_id, topic_id, content
events          — id, candidate_id, title, summary, date, source
```

---

## 2. Researcher

The Researcher is an automated pipeline that monitors the web for news about each candidate and synthesizes updates into
concise event records.

### Pipeline

1. **Collect candidate names** from the `candidates` table.
2. **Search for news** using a self-hosted [SearXNG](https://searxng.github.io/searxng/) instance to query multiple
   search engines without third-party tracking.
3. **Summarize results** using Ollama (`granite4:latest`) to generate a short, neutral news-ticker-style summary.
4. **Store events** in the `events` table linked to the relevant candidate.

### Design Considerations

- SearXNG is used as the search backend to preserve user privacy and avoid API rate limits from commercial providers.
- Summaries are kept concise (news ticker format) to be suitable for display in the voter-facing interface.
- The pipeline runs on an **hourly schedule** to keep candidate news fresh throughout the campaign period.

---

## Tech Stack

| Layer               | Technology                                   |
|---------------------|----------------------------------------------|
| Database            | PostgreSQL                                   |
| OCR                 | Tesseract                                    |
| LLM — Generation    | Ollama · `glm-4.7-flash:latest`              |
| LLM — Summarization | Ollama · `granite4:latest`                   |
| Search Backend      | SearXNG (self-hosted)                        |
| Language            | Python (pipeline scripts)                    |
| Frontend            | SvelteKit (public website, desktop & mobile) |

---

## Milestones

| Phase | Deliverable                                             |
|-------|---------------------------------------------------------|
| 1     | Database schema design and setup                        |
| 2     | Generator — party and candidate ingestion               |
| 3     | Generator — topic extraction from Plan de Gobierno      |
| 4     | Researcher — news collection and summarization pipeline |
| 5     | Voter-facing frontend (search, compare, explore)        |
| 6     | Launch & QA before election cycle                       |

---

---

*Prepared for internal review — Peru Elecciones 2026 Initiative*