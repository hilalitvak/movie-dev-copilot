# 🎬 Movie Development Copilot  
### Autonomous AI Agent for Film Production Intelligence  

---

## 🚩 The Greenlight Problem  

Early film development decisions are high-risk and often rely on intuition rather than structured data.

Independent producers typically lack:

- Reliable budget feasibility benchmarks  
- Historical ROI validation  
- Structured comparable film discovery  
- Data-driven talent alignment  

Creative vision exists.  
Production intelligence is missing.  

---

## 💡 Our Solution  

**Movie Development Copilot** is an autonomous AI agent that transforms a creative concept into structured production intelligence.

### Input  

- Logline  
- Genre  
- Budget Constraints  

### Output  

- Comparable Films Analysis  
- Budget Feasibility Validation  
- ROI Benchmark Estimation  
- Structured Production Report  

---

## 🧠 Agent Architecture  

The system follows a three-stage execution pipeline:

1. **retrieval_local_comps**  
   Retrieves local comparable film statistics and summarizes available ROI coverage.

2. **rag_pinecone**  
   Uses Pinecone vector search to retrieve semantically similar comparable films based on story mechanics, genre, tone, and budget cues.

3. **llm_synthesis**  
   Generates a concise production-style report using retrieved comparable films and historical ROI benchmarks.

These module names are identical to the execution trace returned by the API.

---

## 📊 Data Foundation  

Primary dataset: **The Movies Dataset (Kaggle)**  

Includes:

- metadata  
- cast & crew  
- genres and keywords  
- budget and revenue  
- ratings and popularity signals  

---

## 🏗 Infrastructure  

- **Supabase** — agent execution logging and structured storage  
- **Pinecone** — semantic vector retrieval  
- **LLMod.ai** — embeddings and reasoning LLM  
- **Render** — backend deployment  

---

## 🔌 API Endpoints  

- `GET /api/team_info` — returns team metadata  
- `GET /api/agent_info` — returns agent description, purpose, prompt template, and example execution  
- `GET /api/model_architecture` — returns architecture diagram (PNG)  
- `POST /api/execute` — main agent execution endpoint  

---

## ⚙️ Running Locally  

To run the project locally, configure the required environment variables for external services, then install dependencies:

```bash
pip install -r requirements.txt

Run the backend:
uvicorn backend.app.main:app --reload


---

## 🖥 Frontend  

A minimal web interface enables:

- entering a prompt  
- running the agent  
- viewing the final response  
- inspecting execution steps  

---

## 🚀 Deployment  

Render URL: `https://movie-dev-copilot.onrender.com/`  

GitHub Repository: `https://github.com/hilalitvak/movie-dev-copilot`  

---

Built for the **Autonomous AI Agents Course**