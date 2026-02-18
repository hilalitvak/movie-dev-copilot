
# 🎬 Movie Development Copilot  
### Data-Driven Decision Support for Independent Film Producers

---

## 🚩 The Greenlight Problem

Film development decisions are high-risk and often intuition-driven.

Independent producers lack:
- Reliable budget benchmarks  
- Historical ROI validation  
- Structured comparable film analysis  
- Data-backed talent recommendations  

Creative vision exists.  
Production intelligence is missing.

---

## 💡 Our Solution

**Movie Development Copilot** is an autonomous AI agent that transforms a creative concept into structured production intelligence.

Input:
> Logline + Genre + Budget Constraints  

Output:
- 🎥 Comparable Films  
- 💰 Budget Feasibility Analysis  
- 📈 ROI Benchmarking  
- 🎬 Talent Shortlist  
- 📄 Structured Production Report  

---

# 🧠 System Architecture

The system follows a four-module architecture:

### 1️⃣ Intelligent Intent  
Extracts:
- Genre  
- Themes  
- Budget tier  
- Production signals  

### 2️⃣ Semantic Retrieval  
Uses Pinecone vector search to retrieve:
- 10–20 historically similar films  
- Genre-aligned comps  
- Budget-tier matches  

### 3️⃣ Predictive Core  
Deterministic code-based analysis:
- Budget validation  
- Revenue percentile analysis  
- ROI benchmarking  

### 4️⃣ Dynamic Synthesis  
LLM-based structured report generation.

---

# 📊 Data Foundation

Primary dataset:
**The Movies Dataset (Kaggle)**  
- Metadata  
- Cast & Crew  
- Genres & Keywords  
- Budget & Revenue  
- Ratings  

Infrastructure:
- Supabase  
- Pinecone  
- LLMod.ai  
- Render  

---

# 🔌 API Specification

## GET `/api/team_info`

Returns team metadata.

```json
{
  "group_batch_order_number": "3_9",
  "team_name": "Movie Development Copilot",
  "students": [
    { "name": "Student A", "email": "a@..." },
    { "name": "Student B", "email": "b@..." },
    { "name": "Student C", "email": "c@..." }
  ]
}
```

---

## GET `/api/agent_info`

Returns:
- description  
- purpose  
- prompt_template  
- prompt_examples  

---

## GET `/api/model_architecture`

Returns:
- Content-Type: image/png  
- PNG architecture diagram  
- Module names consistent with execution logs  

---

## POST `/api/execute`

Main execution endpoint.

### Request

```json
{
  "prompt": "Thriller about a detective repeating the same night to stop an attack. Budget: $12M."
}
```

### Success Response

```json
{
  "status": "ok",
  "error": null,
  "response": "Structured production intelligence report...",
  "steps": [
    {
      "module": "Intelligent Intent",
      "prompt": {},
      "response": {}
    },
    {
      "module": "Semantic Retrieval",
      "prompt": {},
      "response": {}
    },
    {
      "module": "Dynamic Synthesis",
      "prompt": {},
      "response": {}
    }
  ]
}
```

### Error Response

```json
{
  "status": "error",
  "error": "Human-readable error description",
  "response": null,
  "steps": []
}
```

---

# 🏗 Agent Design Principles

## Optimized LLM Usage

The system minimizes LLM calls:

- Financial calculations are deterministic  
- Percentiles are precomputed  
- Embeddings are stored  
- LLM is used only for reasoning and synthesis  

This ensures:
- Low latency  
- Budget efficiency  
- Controlled $13 LLMod.ai usage  

---

# 🧩 Prompt Template (Internal Format)

All user prompts are transformed into:

```
You are a film production intelligence agent.

User Concept:
{logline}

Genre:
{genre}

Budget:
{budget}

Tasks:
1. Extract production signals.
2. Retrieve comparable films.
3. Validate budget feasibility.
4. Estimate ROI benchmark.
5. Recommend aligned talent.
6. Generate structured report.
```

---

# 🔄 Execution Flow

When `/api/execute` is called:

1. Intent Parsing (LLM)
2. Vector Retrieval (Pinecone)
3. Financial Computation (Python logic)
4. Talent Filtering (Database queries)
5. Report Generation (LLM)

All LLM calls are logged in `steps`.

---

# 🖥 Frontend

Minimal web interface includes:
- Prompt textarea  
- Run Agent button  
- Final response display  
- Execution trace display  

---

# 🚀 Deployment

- Platform: Render  
- Database: Supabase  
- Vector DB: Pinecone  
- LLM Provider: LLMod.ai  

---

# 📈 Roadmap

Phase 1:
✔ Comparable analysis  
✔ Budget validation  

Phase 2:
Revenue prediction ML model  

Phase 3:
Full production intelligence platform  

---

# 📦 Submission

Render URL:  
{your_render_url}

GitHub Repo:  
{your_repo_url}

---

Built for the Autonomous AI Agents Course  
Instructor: Idan Hahn  
Deadline: 01/03/2026
