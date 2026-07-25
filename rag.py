import ollama
from sentence_transformers import SentenceTransformer
from search import create_bm25, hybrid_search,load_cache

from config import (
    TOP_K, 
    MODEL_NAME,
    EMBEDDING_MODEL
)

embedding_model = SentenceTransformer(EMBEDDING_MODEL)
faiss_index, document_chunks = load_cache()
bm25 = create_bm25(document_chunks)

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
You are a document question answering assistant.

Use ONLY the supplied context.

Rules:

- Never use outside knowledge.
- Copy numbers exactly.
- Never calculate values unless explicitly requested.
- If a value exists in the document, return it exactly.
- When multiple numbers appear near a label, always match the number
  that immediately FOLLOWS the label, not one that precedes it.
- Pay close attention to which label each number belongs to.
- If the answer is missing say:

"I could not find the answer in the provided documents."

Never assume missing values are zero.

Return concise answers.

Context:
{context}

Question:
{question}

Answer:
""".strip()


def generate_answer(question: str) -> dict:
    results = hybrid_search(query=question, model=embedding_model, index=faiss_index, chunks=document_chunks, bm25=bm25, top_k=TOP_K,)

    if not results:
        return {
            "question": question,
            "answer": (
                "I could not find the answer "
                "in the provided documents."
            ),
            "sources": [],
            "results": [],
        }

    prompt = build_prompt(question=question,results=results,)

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
            "temperature": 0,
            "top_p": 0.9,
        },
    )

    answer = response["message"]["content"].strip()

    sources = list(
        dict.fromkeys(
            result["source"]
            for result in results
        )
    )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "results": results,
    }


def print_retrieval_results(results: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("RETRIEVAL RESULTS")
    print("=" * 80)

    for index, result in enumerate(results, start=1):
        print(f"\n[{index}]")
        print(f"Score : {result['score']:.4f}")
        print(f"Source: {result['source']}")
        print("-" * 80)
        print(result["text"][:700])


def main() -> None:
    question = input("Question: ").strip()
    if not question:
        print("Question cannot be empty.")
        return

    result = generate_answer(question)
    print_retrieval_results(result["results"])
    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")
    if result["sources"]:
        for source in result["sources"]:
            print(f"- {source}")
    else:
        print("- No source found")


if __name__ == "__main__":
    main()