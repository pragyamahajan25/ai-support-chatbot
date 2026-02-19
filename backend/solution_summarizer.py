import ollama

def summarize_solutions(ticket):
    """
    Combine solution1, solution2, and solution3 of a ticket
    into a single, easy-to-follow numbered list of steps.
    Returns the summarized instructions as a string.
    """

    # Collect all available solutions for the ticket
    solutions = []
    for i in range(1, 4):
        sol = ticket.get(f"solution{i}")
        # Ignore empty or 'nan' solutions
        if sol and str(sol).strip() and str(sol).lower() != "nan":
            solutions.append(str(sol).strip())

    # If no solutions are available, return a default message
    if not solutions:
        return "No solutions available for this ticket."

    # Build a prompt for the LLM
    prompt = f"""
You are a technical support assistant.
Here are the solutions attempted for a ticket:
{chr(10).join([f"{i+1}. {s}" for i, s in enumerate(solutions)])}

Summarize these solutions into a numbered list of actionable steps only.
Do NOT include any notes, explanations, or assumptions.
Do NOT reference previous solutions.
Return only the numbered steps.
"""

    try:
        # Ask the LLM to generate a concise step-by-step summary
        response = ollama.generate(
            model="llama3:latest",
            prompt=prompt,
            options={
                "num_tokens": 300,
                "temperature": 0.2,
            }
        )

        # Extract and clean the LLM response
        summary = response["response"].strip()
        return summary

    except Exception as e:
        print(f"Error summarizing solutions for ticket {ticket.get('ticketID')}: {e}")
        return "Error generating summary."
