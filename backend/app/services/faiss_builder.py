from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.services.fastembed_wrapper import FastEmbedWrapper
from app.services.db import supabase

embedding_model = FastEmbedWrapper()

def build_faiss_index():
    result = supabase.table("faqs").select("id, question, answer, clinic_id, category").execute()
    faqs = result.data

    if not faqs:
        print("No FAQs found in Supabase.")
        return

    documents = [
        Document(
            page_content=row["question"],
            metadata={"answer": row["answer"], "clinic_id": row["clinic_id"], "category": row["category"]}
        )
        for row in faqs
    ]

    vectorstore = FAISS.from_documents(documents, embedding_model)
    vectorstore.save_local("app/data/faiss_langchain_index")

    print(f"LangChain FAISS index built with {len(faqs)} FAQs.")

if __name__ == "__main__":
    build_faiss_index()