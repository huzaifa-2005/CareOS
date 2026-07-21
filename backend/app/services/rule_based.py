# Keyword-based matching, case-insensitive, no external API calls

GREETINGS = ["hi", "hello", "hey", "salam", "assalam", "aoa", "asalam"]

FAQ_RULES = {
    ("timing", "timings", "hours", "open", "close", "khulta", "khultay", "waqt"): 
    "Our clinic is open Mon–Sat, 10 AM to 8 PM.",
    ("location", "address", "where"): 
        "We're located at Gulshan-e-Iqbal, University Road, Karachi.",
    ("fee", "fees", "cost", "price", "charges"): 
        "Consultation fee is Rs. 2000. It may vary by doctor.",
    ("doctor", "doctors", "available"): 
        "We have general physicians and specialists available. Would you like to book an appointment?",
}

def check_greeting(message: str) -> str | None:
    msg = message.lower().strip()
    if any(greet in msg for greet in GREETINGS):
        return "Hello! Welcome to CareOS. How can I help you today — booking, FAQs, or something else?"
    return None

def check_faq(message: str) -> str | None:
    msg = message.lower().strip()
    for keywords, response in FAQ_RULES.items():
        if any(keyword in msg for keyword in keywords):
            return response
    return None

def handle_rule_based(message: str) -> str | None:
    """
    Returns a response string if a rule matches (greeting or FAQ).
    Returns None if nothing matches — caller should route to
    intent classifier / RAG-LLM flow instead.
    """
    greeting_response = check_greeting(message)
    if greeting_response:
        return greeting_response

    faq_response = check_faq(message)
    if faq_response:
        return faq_response

    return None