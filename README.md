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
- Talent Alignment Suggestions  
- Structured Production Report  

---

## 🧠 Agent Architecture  

The system follows a four-stage reasoning pipeline:

1. **Intelligent Intent**  
   LLM extracts production signals such as genre, themes, narrative scope, and budget tier.

2. **Semantic Retrieval (RAG)**  
   Pinecone vector search retrieves historically similar films and genre-aligned comparables.

3. **Predictive Core**  
   Deterministic financial analytics validate budget feasibility and estimate ROI benchmarks.

4. **Dynamic Synthesis**  
   LLM generates a concise structured production intelligence report.

---

## 📊 Data Foundation  

Primary dataset: **The Movies Dataset (Kaggle)**  

Includes metadata, cast & crew, genres, keywords, budget, revenue, ratings, and popularity signals.

---

## 🏗 Infrastructure  

- **Supabase** — agent execution logging and structured storage  
- **Pinecone** — semantic vector retrieval  
- **LLMod.ai** — embeddings and reasoning LLM  
- **Render** — backend deployment  

---

## 🔌 API Endpoints  

- `GET /api/team_info` — returns team metadata  
- `GET /api/agent_info` — returns agent description and usage  
- `GET /api/model_architecture` — returns architecture diagram (PNG)  
- `POST /api/execute` — main agent execution endpoint  

---

## ⚙️ Running Locally  

To run the project locally, configure the required environment variables for external services (database, vector search, and LLM provider), then install dependencies:
- pip install -r requirements.txt
Run the backend:
- uvicorn backend.app.main:app --reload


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