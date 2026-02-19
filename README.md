# Support AI Chatbot

An AI-powered assistant that recommends support solutions based on historical ticket data. The system uses hybrid retrieval, LLM reranking, and user feedback to continuously improve solution quality.

---

## Setup

### Prerequisites

- **Python 3.8+**
- **[Streamlit](https://streamlit.io/)**
- **[Ollama](https://ollama.ai/)** installed and running locally
- **Excel file** with historical support tickets (place in `data/` directory)

### Installation & First-Time Setup

1. **Copy or unzip the project folder** to your local machine.

2. **Create and activate a virtual environment:**

   **Windows:**
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Prepare Ollama:**
   - Start Ollama:  
     ```
     ollama serve
     ```
   - Pull required models:  
     ```
     ollama pull nomic-embed-text
     ollama pull llama3:latest
     ```

5. **Prepare data:**
   - Place your Excel ticket data file in the `data/` directory.

6. **Create embeddings and index:**
   - Run the ingestion script to process your data and build the vector store:
     ```
     python backend/ingest.py
     ```
   - This step must be repeated whenever you update or replace your ticket data.

7. **Run the app:**
   ```
   streamlit run frontend/app.py
   ```

---

## Usage

- Enter your support request in the text area.
- Click **"Find Solution"** to search for relevant historical tickets.
- Review the top recommended solution and alternatives.
- Click **"Worked"** if a solution resolves your issue. This feedback improves future recommendations.

---

## System Assumptions & Behavior

- **Ollama must be running locally** with the required models available.
- **Ticket data** must be present in the `data/` directory before first use.
- **You must run `backend/ingest.py`** after adding or updating your ticket data to create/update the embeddings and index.
- **Feedback logic:**
  - Clicking **"Worked"** increments both the "success" and "attempt" counters for that solution.
  - Feedback is only counted once per ticket per session.
- **Guardrails:**
  - The app warns if the match confidence is low.
  - Warnings are shown for solutions that include risky actions (e.g., "factory reset", "delete", "reinstall OS").
- **No external files** are required beyond those described above; all backend logic is implemented in the provided Python files.

---

## Project Structure

```
ai-support/
│
├── backend/
│   ├── feedback.py            # Handles user feedback on solutions and updates success/attempt counters.
│   ├── ingest.py              # Processes historical ticket data, creates embeddings, and builds the vector store.
│   ├── llm_reranker.py        # Uses LLM to rerank retrieved solutions based on relevance to the user query.
│   ├── solution_summarizer.py # Summarizes top solutions for concise presentation in the frontend.
│   ├── vector_store.py        # Manages the vector store: storage, retrieval, and similarity searches.
│
├── data/
│   └── <your_ticket_data>.xlsx # tickets_dataset.xlsx
│
├── frontend/
│   └── app.py                 # Streamlit app: UI for entering queries, displaying solutions, and collecting feedback.
│
├── requirements.txt           # Python dependencies.
└── README.md                  # This documentation file.

```

---

