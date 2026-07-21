from app.services.rule_based import handle_rule_based
from app.services.rag_pipeline import generate_rag_response


def classify_and_respond(message: str, clinic_id: str) -> tuple[str, str]:
    """
    Returns (intent_route, response_text)
    intent_route: 'rule_based' or 'rag_llm'
    """
    rule_response = handle_rule_based(message)

    if rule_response:
        return "rule_based", rule_response

    # No rule matched — route to RAG/LLM
    ai_response = generate_rag_response(message, clinic_id)
    return "rag_llm", ai_response

