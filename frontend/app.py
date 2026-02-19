import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import re
import math

# Set path to backend folder to import modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from backend.vector_store import retrieve_candidates
from backend.llm_reranker import relevance_score
from backend.feedback import record_feedback, get_success_count
from backend.solution_summarizer import summarize_solutions

# Simple keyword overlap score for hybrid search
def keyword_overlap_score(query: str, ticket: dict) -> float:
    """
    Count common words between user query and ticket text.
    Returns a fraction (0-1) representing keyword similarity.
    """
    text = f"{ticket.get('faultText','')} {ticket.get('customerComplaint','')}".lower()
    query_words = set(re.findall(r"\w+", query.lower()))
    ticket_words = set(re.findall(r"\w+", text))
    if not query_words:
        return 0.0
    overlap = len(query_words & ticket_words)
    return overlap / len(query_words)

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Support AI", layout="wide")
st.title("AI Support Assistant")

# Initialize session state variables
for key in ["query_cache", "best_ticket", "best_score", "clicked_solution_per_ticket"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key in ["query_cache", "clicked_solution_per_ticket"] else None

# User input: query box
query = st.text_area("Enter your support request")

# ------------------ Search ------------------
if st.button("Find Solution") and query.strip():
    # Retrieve top 5 tickets using hybrid FAISS + keyword search
    candidates = retrieve_candidates(query, top_k=5)
    best_ticket = None
    best_score = -1

    for cand in candidates:
        ticket = cand["ticket"]

        # Hybrid retrieval: combine vector similarity + keyword overlap
        vector_score = cand["vector_score"]
        keyword_score = keyword_overlap_score(query, ticket)
        retrieval_score = 0.7 * vector_score + 0.3 * keyword_score

        # AI reranker + recency score
        rerank_score = relevance_score(query, ticket)

        # Final combined score for ticket ranking
        final_score = 0.6 * retrieval_score + 0.4 * rerank_score

        # Keep the ticket with highest score
        if final_score > best_score:
            best_score = final_score
            best_ticket = ticket

    # Store best ticket and score in session
    st.session_state.best_ticket = best_ticket
    st.session_state.best_score = best_score
    st.session_state.query_cache[query] = (best_ticket, best_score)
    st.session_state.clicked_solution_per_ticket.clear()

# ------------------ Display Result ------------------
ticket = st.session_state.best_ticket
if ticket:
    ticket_id = str(ticket.get("ticketID"))

    # Show ticket information
    st.subheader(f"Best Matching Ticket: {ticket_id}")
    st.write(f"**Matching Score:** {st.session_state.best_score:.3f}")
    st.write(f"**System:** {ticket.get('systemName')}")
    st.write(f"**Complaint:** {ticket.get('customerComplaint')}")
    st.write(f"**Fault:** {ticket.get('faultText')}")

    # Summarized solution using LLM
    st.subheader("Recommended Troubleshooting Steps")
    summary_text = summarize_solutions(ticket)
    st.markdown(summary_text)

    # Individual solutions
    st.subheader("Solutions")
    solutions = [
        ("solution3", ticket.get("solution3")),
        ("solution2", ticket.get("solution2")),
        ("solution1", ticket.get("solution1")),
    ]

    # Solution weights for hierarchy + feedback priority
    ESCALATION_WEIGHT = {
        "solution1": 1.0,
        "solution2": 0.8,
        "solution3": 0.6
    }

    solution_scores = []
    for key, text in solutions:
        text = str(text or "").strip()
        if text and text.lower() != "nan":
            unique_key = f"{ticket_id}_{key}"
            feedback_count = get_success_count(unique_key)

            # Base weight for hierarchy, feedback dominates ranking
            base_weight = ESCALATION_WEIGHT.get(key, 0.5)
            feedback_score = 1 + (feedback_count * 0.5)
            final_score = feedback_score * base_weight

            solution_scores.append((final_score, key, text, feedback_count, unique_key))

    # Sort solutions by final score
    solution_scores.sort(reverse=True, key=lambda x: x[0])

    # Normalize confidence between 0-1 for display
    if solution_scores:
        max_score = solution_scores[0][0]
    else:
        max_score = 1.0

    normalized_solution_scores = []
    for score, key, text, feedback_count, unique_key in solution_scores:
        confidence = score / max_score
        normalized_solution_scores.append((score, key, text, feedback_count, unique_key, confidence))

    # Feedback handler function
    def record_feedback_and_update(unique_key):
        record_feedback(unique_key)
        ticket_id_part = unique_key.split("_")[0]
        st.session_state.clicked_solution_per_ticket[ticket_id_part] = unique_key

    # Display each solution with button
    for idx, (score, key, text, feedback_count, unique_key, confidence) in enumerate(normalized_solution_scores, start=1):
        highlight = "TOP RECOMMENDED" if idx == 1 else ""
        col1, col2 = st.columns([6, 1])

        with col1:
            st.markdown(f"### Option {idx} {highlight}")
            st.write(text)
            st.info(f"Users confirmed this worked **{feedback_count} time(s)**")
            st.write(f"**Effectiveness Score:** {confidence:.2f}")

        with col2:
            clicked = st.session_state.clicked_solution_per_ticket.get(ticket_id)
            disabled = clicked is not None
            st.button(
                "Worked",
                key=unique_key,
                on_click=lambda k=unique_key: record_feedback_and_update(k),
                disabled=disabled
            )

    # ------------------ Guardrails ------------------
    # Warn if ticket is low match
    if st.session_state.best_score < 0.3:
        st.warning("This issue does not closely match historical tickets. Recommendation may be unreliable.")

    # Warn if solution includes dangerous actions
    danger_words = ["factory reset", "full recovery", "delete", "reinstall os"]
    if any(word in summary_text.lower() for word in danger_words):
        st.error("This solution includes system-reset actions. Confirm backup before proceeding.")

    # Success message when feedback is recorded
    if st.session_state.clicked_solution_per_ticket.get(ticket_id):
        st.success("Feedback recorded! Your confirmed solution will naturally rise in ranking.")
