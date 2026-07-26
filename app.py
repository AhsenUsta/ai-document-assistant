from __future__ import annotations

from pathlib import Path

import streamlit as st
import indexer
import rag

from config import (
    CHUNKS_PATH,
    DATA_ROOT,
    INDEX_PATH,
    META_PATH,
    BM25_PATH,
)
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide",
)


def cache_is_ready() -> bool:
    """Check whether both the FAISS index and chunk cache exist. """
    return INDEX_PATH.exists() and CHUNKS_PATH.exists()

def clear_index_cache() -> None:
    """Delete all generated retrieval cache files."""
    cache_files = [
        INDEX_PATH,
        CHUNKS_PATH,
        META_PATH,
        BM25_PATH ,
    ]

    for cache_file in cache_files:
        if cache_file.exists():
            cache_file.unlink()

def save_uploaded_files(uploaded_files) -> list[str]:
    """Save validated Streamlit uploads into the configured data folder."""
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    saved_files: list[str] = []

    for uploaded_file in uploaded_files:
        safe_name = Path(uploaded_file.name).name
        extension = Path(safe_name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {safe_name}")

        target_path = DATA_ROOT / safe_name
        target_path.write_bytes(uploaded_file.getbuffer())
        saved_files.append(safe_name)

    return saved_files
    
def reload_retrieval_components() -> None:
    """
    Reload FAISS, chunks, embeddings, and BM25 components from disk.

    This function must be called after indexer.main() rebuilds the index.
    """
    print("[DEBUG] Reloading retrieval components")

    success = rag.initialize_components(force_reload=True)

    print(f"[DEBUG] initialize_components returned: {success}")

    if success is False:
        raise RuntimeError(
            "Retrieval components could not be initialized."
        )

    chunk_count = (
        len(rag.document_chunks)
        if rag.document_chunks
        else 0
    )

    print(f"[DEBUG] Loaded chunk count: {chunk_count}")

    if rag.document_chunks:
        sources = sorted(
            {
                chunk.get("source", "unknown")
                for chunk in rag.document_chunks
            }
        )

        print(f"[DEBUG] Sources in loaded cache: {sources}")


def show_sources(result: dict) -> None:
    """Display source document names returned by RAG."""
    sources = result.get("sources", [])

    if not sources:
        st.info("No source document was returned.")
        return

    for source in sources:
        st.markdown(f"- `{source}`")


def show_retrieval_details(result: dict) -> None:
    """Display retrieved chunks and their scores."""
    results = result.get("results", [])

    if not results:
        st.info("No relevant chunks were found.")
        return

    for position, item in enumerate(results, start=1):
        source = item.get("source", "unknown")
        score = item.get("score", 0.0)
        text = item.get("text", "")

        title = (
            f"{position}. {source} "
            f"— score {score:.4f}"
        )

        with st.expander(title):
            st.write(text)

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Hybrid score",
                f"{score:.4f}",
            )

            col2.metric(
                "Semantic score",
                f"{item.get('semantic_score', 0.0):.4f}",
            )

            col3.metric(
                "BM25 score",
                f"{item.get('bm25_score', 0.0):.4f}",
            )


st.title("AI Document Assistant")

st.caption(
    "Upload PDF, PNG, or JPEG documents to automatically index them, "
    "then ask questions using hybrid retrieval and a local Ollama model."
)

# ------------------------------------------------------------
# Session state initialization
# ------------------------------------------------------------

if "index_version" not in st.session_state:
    st.session_state["index_version"] = 0

if "processed_files" not in st.session_state:
    st.session_state["processed_files"] = set()

if "rag_initialized" not in st.session_state:
    st.session_state["rag_initialized"] = False

if "messages" not in st.session_state:
    st.session_state["messages"] = []
    
# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------

with st.sidebar:
    st.header("Document index")

    debug_mode = st.toggle(
        "Show retrieval details",
        value=False,
        help=(
            "Display sources, retrieved chunks, "
            "and similarity scores."
        ),
    )

    if st.button(
        "Clear conversation",
        use_container_width=True,
    ):
        st.session_state["messages"] = []
        st.rerun()

    st.divider()

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help=(
            "Turkish and English digital or scanned "
            "documents are supported."
        ),
    )

    # If `uploaded_files` is empty, use it as [] 
    uploaded_files = uploaded_files or []

    current_names = {
        Path(uploaded_file.name).name
        for uploaded_file in uploaded_files
    }

    removed_files = (
        st.session_state["processed_files"]
        - current_names
    )

    new_files = [
        uploaded_file
        for uploaded_file in uploaded_files
        if Path(uploaded_file.name).name
        not in st.session_state["processed_files"]
    ]

    # --------------------------------------------------------
    # Removed documents
    # --------------------------------------------------------

    if removed_files:
        try:
            with st.status(
                "Removing documents...",
                expanded=True,
            ) as status:
                for filename in removed_files:
                    file_path = DATA_ROOT / filename

                    if file_path.exists():
                        file_path.unlink()

                st.session_state[
                    "processed_files"
                ].difference_update(removed_files)

                # If there are still documents in the folder, rebuild the index
                remaining_files = [
                    path
                    for path in DATA_ROOT.iterdir()
                    if path.is_file()
                    and path.suffix.lower()
                    in ALLOWED_EXTENSIONS
                ]

                if remaining_files:
                    st.write("Rebuilding document index")
                    indexer.main()

                    if not cache_is_ready():
                        raise RuntimeError(
                            "The index could not be rebuilt."
                        )

                    st.write(
                        "Reloading retrieval components"
                    )
                    reload_retrieval_components()

                    st.session_state[
                        "rag_initialized"
                    ] = True

                else:
                    # If there are no documents left, clear the old cache
                    clear_index_cache()

                    rag.faiss_index = None
                    rag.document_chunks = None
                    rag.bm25 = None

                    st.session_state["rag_initialized"] = False

                st.session_state["index_version"] += 1

                # Previous answers may relate to the previous index
                st.session_state["messages"] = []

                status.update(
                    label="Documents removed",
                    state="complete",
                )

            st.success(
                f"Removed {len(removed_files)} file(s)."
            )

        except Exception as exc:
            st.error(
                f"Document removal failed: {exc}"
            )

    # --------------------------------------------------------
    # New documents
    # --------------------------------------------------------

    if new_files:
        try:
            with st.status(
                "Processing new documents...",
                expanded=True,
            ) as status:
                st.write(
                    f"Saving {len(new_files)} new file(s)"
                )

                saved_files = save_uploaded_files(
                    new_files
                )

                st.write(
                    "Extracting text, running OCR, "
                    "and creating chunks"
                )

                st.write(
                    "Generating embeddings and "
                    "rebuilding the FAISS cache"
                )

                indexer.main()

                if not cache_is_ready():
                    raise RuntimeError(
                        "The index could not be created. "
                        "Check the terminal output for "
                        "extraction or OCR errors."
                    )

                st.write(
                    "Reloading retrieval components"
                )

                reload_retrieval_components()

                st.session_state[
                    "processed_files"
                ].update(saved_files)

                st.session_state[
                    "index_version"
                ] += 1

                st.session_state[
                    "rag_initialized"
                ] = True

                # Clear the old chat when a new message arrives
                st.session_state["messages"] = []

                status.update(
                    label="Index is ready",
                    state="complete",
                )

            st.success(
                f"Indexed {len(saved_files)} new file(s)."
            )

        except Exception as exc:
            st.error(f"Indexing failed: {exc}")

    st.divider()

    if cache_is_ready():
        st.success("Index cache is available.")

        if not st.session_state[
            "rag_initialized"
        ]:
            try:
                reload_retrieval_components()

                st.session_state[
                    "rag_initialized"
                ] = True

            except Exception as exc:
                st.error(
                    "Could not load retrieval components: "
                    f"{exc}"
                )

    else:
        st.warning(
            "No index cache found. "
            "Upload documents to build the index."
        )

    if st.session_state["processed_files"]:
        st.caption("Indexed files:")

        for filename in sorted(
            st.session_state["processed_files"]
        ):
            st.caption(f"• {filename}")

# ------------------------------------------------------------
# Question area
# ------------------------------------------------------------
st.subheader("Document chat")

if not cache_is_ready():
    st.info("Upload documents to build the index "
        "before asking a question."
    )

# Show previous messages
for message in st.session_state["messages"]:
    role = message.get("role", "assistant")

    with st.chat_message(role):
        st.markdown(message.get("content", ""))

        if (role == "assistant" and debug_mode and message.get("result")):
            result = message["result"]

            with st.expander("Sources and retrieval details", expanded=False,):
                left, right = st.columns([1, 2])

                with left:
                    st.markdown("#### Sources")
                    show_sources(result)

                with right:
                    st.markdown("#### Retrieved chunks")
                    show_retrieval_details(result)


question = st.chat_input("Ask a question about your documents...", disabled=not cache_is_ready(),)

if question:
    # Save and display user message
    user_message = {
        "role": "user",
        "content": question,
    }

    st.session_state["messages"].append(user_message)

    with st.chat_message("user"):
        st.markdown(question)

    try:
        if not st.session_state["rag_initialized"]:
            reload_retrieval_components()
            st.session_state["rag_initialized"] = True

        with st.chat_message("assistant"):
            with st.spinner("Searching documents and generating an answer..."):
                result = rag.generate_answer(question)

            answer = result.get("answer", "No answer could be generated.",)

            st.markdown(answer)

            if debug_mode:
                with st.expander("Sources and retrieval details", expanded=False,):
                    left, right = st.columns([1, 2])

                    with left:
                        st.markdown("#### Sources")
                        show_sources(result)

                    with right:
                        st.markdown("#### Retrieved chunks")
                        show_retrieval_details(result)

        # Store answer and full RAG result in history
        assistant_message = {
            "role": "assistant",
            "content": answer,
            "result": result,
        }

        st.session_state["messages"].append(
            assistant_message
        )

    except FileNotFoundError as exc:
        error_message = f"Index cache is missing: {exc}"

        with st.chat_message("assistant"):
            st.error(error_message)

        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": error_message,
            }
        )

    except ConnectionError:
        error_message = (
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        )

        with st.chat_message("assistant"):
            st.error(error_message)

        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": error_message,
            }
        )

    except Exception as exc:
        error_message = (
            "The question could not be answered: "
            f"{exc}"
        )

        with st.chat_message("assistant"):
            st.error(error_message)

        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": error_message,
            }
        )
        