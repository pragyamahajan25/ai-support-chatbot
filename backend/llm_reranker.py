import ollama
from datetime import datetime
import math

# Function to compute how recent a ticket is
def compute_ticket_recency(ticket):
    """
    Calculates a recency weight for a ticket.
    Uses dateFinished1 + timeFinished1.
    Newer tickets get a higher score (closer to 1.0), older tickets decay smoothly.
    """
    date_val = ticket.get("dateFinished1")
    time_val = ticket.get("timeFinished1", "00:00")  # default to midnight if missing

    if not date_val:
        return 0.0  # treat missing dates as old

    try:
        dt = datetime.strptime(f"{date_val} {time_val}", "%d.%m.%Y %H:%M")
        # Calculate days difference from now
        days_diff = (datetime.now() - dt).total_seconds() / (24 * 3600)

        # Use exponential decay to slowly reduce score over time (1 year scale)
        recency_score = math.exp(-days_diff / 365)
        return recency_score

    except Exception as e:
        print(f"Recency parsing error for ticket {ticket.get('ticketID')}: {e}")
        return 0.0

# Function to compute overall relevance of a ticket
def relevance_score(query: str, ticket) -> float:
    """
    Computes a combined relevance score for a ticket based on:
    1. AI relevance using the LLM (semantic understanding of query vs ticket)
    2. Recency of the ticket (newer tickets are preferred)
    Returns a float between 0.0 and 1.0.
    """

    # Prepare the ticket text for the LLM
    ticket_text = f"""
System: {ticket.get('systemName','')}
Complaint: {ticket.get('customerComplaint','')}
Fault: {ticket.get('faultText','')}
"""

    try:
        # Ask the LLM to rate relevance
        prompt = f"""
Query: "{query}"
Ticket: "{ticket_text}"
Rate the relevance from 0 (not relevant) to 1 (highly relevant).
Return only the numeric value.
"""
        response = ollama.generate(
            model="llama3:latest",
            prompt=prompt,
            options={
                "num_tokens": 10,
                "temperature": 0,  # deterministic output
            },
        )
        # Convert LLM response to float and clamp between 0 and 1
        ai_score = float(response["response"].strip())
        ai_score = max(0.0, min(1.0, ai_score))

    except Exception as e:
        print(f"Error computing AI relevance: {e}")
        ai_score = 0.0

    # Compute recency score
    recency_score = compute_ticket_recency(ticket)

    # Combine AI relevance and recency
    # Alpha = weight for AI relevance, (1-alpha) = weight for recency
    alpha = 0.8
    final_score = alpha * ai_score + (1 - alpha) * recency_score

    return final_score
