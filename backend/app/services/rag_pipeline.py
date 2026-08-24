import os
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.services.fastembed_wrapper import FastEmbedWrapper

embedding_model = FastEmbedWrapper()

vectorstore = FAISS.load_local(
    "app/data/faiss_langchain_index",
    embedding_model,
    allow_dangerous_deserialization=True
)

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="openai/gpt-oss-120b",
    temperature=0.5,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant for a medical clinic in Pakistan. "
               "Patients may write in English or Roman Urdu (Urdu written in English letters, e.g. 'aap ka clinic kab khulta hai'). "
               "Always reply in the SAME language/style the patient used — if they wrote in Roman Urdu, reply in Roman Urdu; if English, reply in English. "
               "If the patient's message contains ANY Roman Urdu words at all, reply entirely in Roman Urdu, even if some English words were mixed in. "
               "Never reply in pure Urdu script. "
               "When replying in Roman Urdu, use words and vocabulary as commonly used in Pakistan, NOT Hindi/Indian Roman Urdu vocabulary — "
               "for example, use 'pareshani' or 'masla' not 'samasya/samaseya', "
               "avoid Sanskrit-origin words entirely, and keep the tone casual and natural as spoken in Pakistani WhatsApp chats, not formal or literary Urdu."
               "\n\n"
               "STRICT BOUNDARIES:\n"
               "- ONLY answer questions related to this clinic: appointments, doctors, timings, fees, services, directions, or general health guidance suitable for a clinic receptionist to give.\n"
               "- Do NOT answer questions about politics, religion, other businesses, coding, general trivia, or anything unrelated to this clinic.\n"
               "- Do NOT provide specific medical diagnoses, prescriptions, or dosages — instead, encourage the patient to book an appointment or speak to clinic staff.\n"
               "- If a question is off-topic or outside these boundaries, politely redirect: say you can only help with clinic-related questions, and offer to connect them with staff.\n"
               "\n\n"
               "Use the provided clinic FAQ context to answer accurately. "
               "If the context doesn't contain the answer, say you'll connect them with staff."),
    ("human", "Context:\n{context}\n\nPatient question: {question}")
])

def generate_rag_response(user_message: str, clinic_id: str) -> str:
    results = vectorstore.similarity_search(user_message, k=3)

    relevant_results = [doc for doc in results if doc.metadata.get("clinic_id") == clinic_id]
    context_docs = relevant_results if relevant_results else results

    context = "\n".join([f"Q: {doc.page_content}\nA: {doc.metadata['answer']}" for doc in context_docs])

    chain = prompt | llm
    response = chain.invoke({"context": context, "question": user_message})

    return response.content