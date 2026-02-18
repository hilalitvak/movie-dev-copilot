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
- 🎥 Comparable Films (Comps)  
- 💰 Budget Feasibility Analysis  
- 📈 ROI Probability Benchmarking  
- 🎬 Talent Shortlist Recommendations  
- 📄 Structured Production Report  

---

# 🧠 System Architecture

The agent follows a four-module architecture:

### 1️⃣ Intelligent Intent  
Extracts:
- Genre  
- Themes  
- Budget tier  
- Production signals  

---

### 2️⃣ Semantic Retrieval  
Uses Pinecone vector search to retrieve:
- 10–20 historically similar films  
- Genre-aligned comps  
- Budget-tier matches  

---

### 3️⃣ Predictive Core  
Performs deterministic analysis (code-based, not LLM):

- Budget validation vs historical distribution  
- Revenue percentile analysis  
- ROI benchmarking  

---

### 4️⃣ Dynamic Synthesis  
Generates a structured, investor-ready production intelligence report.

---

# 📊 Data Foundation

Primary dataset:
- **The Movies Dataset (Kaggle)**  
  - Metadata  
  - Cast & Crew  
  - Genres & Keywords  
  - Budget & Revenue  
  - Ratings  

Infrastructure:
- Supabase (primary DB)
- Pinecone (vector retrieval)
- LLMod.ai (LLM provider)
- Render (deployment)

---

# 🔌 API Specification

## ✅ GET `/api/team_info`

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
