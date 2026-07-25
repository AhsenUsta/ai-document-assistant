import ollama
from sentence_transformers import SentenceTransformer
from search import semantic_search,load_cache

from config import (
    TOP_K, 
    MODEL_NAME,
    EMBEDDING_MODEL
)

embedding_model = SentenceTransformer(EMBEDDING_MODEL)
faiss_index, document_chunks = load_cache()

def build_prompt(question: str, results: list[dict]) -> str:
    context_parts = []

    for index, result in enumerate(results, start=1):
        context_parts.append(
            f"[Document {index}]\n"
            f"Source: {result['source']}\n"
            f"Content: {result['text']}"
        )

    context = "\n\n".join(context_parts)

    return f"""
You are a document question-answering assistant.

Answer the question only using the provided context.

If the answer cannot be found in the context, say:
"I could not find the answer in the provided documents."

Context:
{context}

Question:
{question}

Answer:
""".strip()


def generate_answer(question: str) -> str:
    results = semantic_search(query=question,model=embedding_model,index=faiss_index,chunks=document_chunks,top_k=TOP_K,)

    if not results:
        return "No relevant document chunks were found."

    prompt = build_prompt(question, results)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        stream=False,
        think=False,
        options={
            "num_ctx": 2048,
            "temperature": 0.1,
            "top_p": 0.9,
        },
    )
#8192
    return response["message"]["content"]


def main():
    question = input("Question: ").strip()

    if not question:
        print("Question cannot be empty.")
        return

    answer = generate_answer(question)

    print("\nAnswer:")
    print(answer)


if __name__ == "__main__":
    main()