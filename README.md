# Clinical Trial Query Chatbot

## 🎯 Overview

A **Pharma-focused chatbot** that answers questions grounded in clinical trial data from two sources:
1. **DOCX** (`Pharma_Clinical_Trial_Notes.docx`) - Narrative context and label cautions
2. **Excel** (`Pharma_Clinical_Trial_AllDrugs.xlsx`) - Structured drug data (dosing, AEs, severity, outcomes)

All answers include **source citations** and implement **safety guardrails** to prevent medical advice contextually.

---

## 🚀 Quick Start

### **One-Click Launch (Windows)**
Double-click `start_react_app.bat` to launch the **React UI** and Backend.
- Front End: `http://localhost:5173`
- Backend: `http://localhost:8001`

*(Alternative: Use `start_chatbot.bat` for the Legacy Gradio UI)*

---

## 🧠 Approach & Methodology

### **1. Hybrid Retrieval Architecture**
We use a **Split-Retrieval Strategy** to handle the distinct nature of the data sources:
- **Excel Retriever**: Optimizes for structured data (Dose, adverse events tables). Converts rows into semantic text chunks while preserving column metadata.
- **Doc Retriever**: Optimizes for unstructured narrative (Label notes, trial summaries). Splits documents by headers and paragraphs.

### **2. Semantic Search & Ranking**
- **Embedding Model**: `all-MiniLM-L6-v2` (Sentence Transformers) maps queries and documents to a dense vector space.
- **Index**: **FAISS** (Facebook AI Similarity Search) enables sub-millisecond similarity search.
- **Relevance Filtering**: We implement a **Strict Ratio Filter** that requires >0 meaningful keyword overlaps (after synonym expansion) to prevent hallucinations (e.g., rejecting "Space" queries).

### **3. Medical Logic Engine**
- **Query Classification**: The engine detects if the user is asking for "quantitative" data (Excel preference) or "qualitative" guidance (Doc preference).
- **Synonym Expansion**: Maps terms like "kidney" → "renal", "side effects" → "adverse events" to bridge the gap between user and clinical terminology.
- **Snippet Extraction**: Instead of dumping large chunks, the engine extracts the specific sentences matching the query keywords.

---

## 🛠️ Assumptions

1.  **Data Quality**: The source files (`.xlsx`, `.docx`) are assumed to be structured consistently. The Excel file must have columns for Drug Name, Indication, Dose, etc.
2.  **Scope**: The chatbot is limited to the drugs and trials present in the provided dataset. It does not access external internet data.
3.  **User Intent**: Users are assumed to be inquiring about clinical data. General chit-chat is minimized (except for greetings).
4.  **Single Session**: While conversation history exists, each page refresh starts a new session.

---

## 🚧 Limitations

1.  **Safety First**: The bot aggressively refuses queries that sound like medical advice requests ("Should I take...", "Plan for me..."). This may sometimes block legitimate hypothetical questions.
2.  **Context Window**: The conversation history is limited to the last 5 turns. Complex, long references might be lost.
3.  **Exact Keyword nuance**: While synonym mapping helps, highly specific medical jargon might theoretically be missed if not in the synonym dictionary or embedding space.
4.  **Static Data**: The indices are built at startup. Adding new rows to Excel requires a server restart.

---

## 📦 Installation & Manual Run

### **Prerequisites**
- Python 3.8+
- Node.js & npm (for React UI)

### **1. Backend**
```bash
pip install -r backend/requirements.txt
cd backend
python app.py
```
*Port*: `http://localhost:8001`

### **2. Frontend (React)**
```bash
cd frontend
npm install
npm run dev
```
*Port*: `http://localhost:5173`

---

## 🏗️ Technical Stack

- **Backend**: FastAPI
- **Search**: FAISS + SentenceTransformers
- **Processing**: Pandas (Excel), Python-Docx (Docs)
- **Frontend**: React + Vite + Framer Motion
- **Logging**: Loguru

---

## 👥 Acknowledgments
Built for the Axtria GenAI Hands-on Assignment.
