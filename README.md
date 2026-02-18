🎬 Movie Development Copilot

Data-Driven Decision Support for Independent Producers

📌 Overview

Movie Development Copilot is an autonomous AI agent designed to support independent film producers in high-stakes "greenlight" decisions.

The system transforms a creative idea (logline + genre + budget constraints) into actionable production intelligence:

Comparable films (comps)

Budget feasibility analysis

ROI benchmarking

Talent recommendations

Production-level insights

It bridges the gap between creative vision and economic reality.

🎯 The Problem

Film greenlighting decisions are:

High financial risk

Often intuition-driven

Based on scattered data

Lacking centralized intelligence

Producers struggle with:

No realistic budget benchmarks

No historical ROI guidance

Subjective talent selection

Unclear genre viability

💡 Our Solution

A modular AI agent that:

Analyzes semantic intent of the user idea

Retrieves historical comparable films

Performs budget validation

Recommends proven production talent

Synthesizes everything into a structured production report

🧠 System Architecture

The system follows a four-stage AI pipeline:

Intelligent Intent Module
Extracts genre, themes, constraints, and production signals from the prompt.

Semantic Retrieval Module
Retrieves historically similar films from vector database (Pinecone).

Predictive Core Module
Performs:

Budget sanity check

ROI estimation

Historical performance analysis

Dynamic Synthesis Module
Generates a structured, investor-ready production intelligence report.

All module names are consistent across:

Architecture diagram

/api/execute steps logging

Documentation

🗂 Data Sources

Primary dataset:

The Movies Dataset (Kaggle)

Metadata

Cast & crew

Keywords

Genres

Budget & revenue

Ratings

Database stack:

Supabase (primary relational storage)

Pinecone (vector search for semantic retrieval)

🚀 API Endpoints
1️⃣ GET /api/team_info

Returns team metadata.

{
  "group_batch_order_number": "3_9",
  "team_name": "Movie Development Copilot",
  "students": [
    { "name": "Student A", "email": "a@..." },
    { "name": "Student B", "email": "b@..." },
    { "name": "Student C", "email": "c@..." }
  ]
}

2️⃣ GET /api/agent_info

Returns agent metadata and usage instructions.

Includes:

Description

Purpose

Prompt template

Full example prompt + response

Full step trace example

3️⃣ GET /api/model_architecture

Returns a PNG architecture diagram.

Content-Type:

image/png


Modules displayed:

Intelligent Intent

Semantic Retrieval

Predictive Core

Dynamic Synthesis

4️⃣ POST /api/execute

Main execution endpoint.

Request
{
  "prompt": "Thriller about a detective repeating the same night to stop an attack. Budget: $12M."
}

Success Response
{
  "status": "ok",
  "error": null,
  "response": "...final structured report...",
  "steps": [
    {
      "module": "Intelligent Intent",
      "prompt": {...},
      "response": {...}
    },
    {
      "module": "Semantic Retrieval",
      "prompt": {...},
      "response": {...}
    }
  ]
}

Error Response
{
  "status": "error",
  "error": "Human-readable error description",
  "response": null,
  "steps": []
}

🔍 Step Logging (Required Traceability)

Each LLM call is logged with:

{
  "module": "Module Name",
  "prompt": {},
  "response": {}
}


This ensures:

Full transparency

Architectural consistency

Reproducibility

Debug capability

🖥 Frontend / GUI

Minimal web UI includes:

Textarea for user prompt

"Run Agent" button

Final structured response display

Full steps trace display

Optional:

Conversation memory

Follow-up prompts

The UI is focused on:

Clarity

Execution transparency

Step inspection

⚙️ Optimization Strategy

To meet the $13 LLMod.ai budget:

Avoid unnecessary LLM calls

Use pre-aggregated financial statistics

Perform numeric analysis in code (not LLM)

Use embeddings only for retrieval

Keep prompt context minimal

AI is used only for:

Semantic reasoning

Narrative synthesis

All calculations are deterministic and code-based.

📊 Core Capabilities
🎥 Comp Finder

Finds 10–20 historically similar films using:

Genre clustering

Keyword overlap

Semantic similarity

💰 Budget Sanity Check

Validates:

Historical budget range

Revenue distribution

ROI percentile

🎬 Talent Shortlist

Recommends:

Directors

Cinematographers

Editors

Based on:

Budget tier success

Genre alignment

Historical ROI performance

🧪 Demo Example

User Prompt:

Thriller about a detective repeating the same night to stop an attack. Budget: $12M.

Agent Output:

Comparable Films:

Source Code

Edge of Tomorrow

Budget Analysis:

Validated

Historical ROI ~150%

Talent Recommendations:

Mid-budget sci-fi experienced director

DoP with proven $10–15M success

🛠 Deployment

Platform:

Render

Database:

Supabase

Pinecone

LLM Provider:

LLMod.ai

Each group uses:

Shared group API key

Strict cost control

📈 Roadmap
Phase 1 (Current)

Intelligent comp analysis

Budget validation

Phase 2

Revenue prediction ML models

Phase 3

End-to-end production intelligence platform

📦 Submission

Render URL:
{your render url}

GitHub Repository:
{your repo url}

👩‍💻 Course Project

Built as part of:

Autonomous AI Agents Course
Instructor: Idan Hahn
Deadline: 01/03/2026