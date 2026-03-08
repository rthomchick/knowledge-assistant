import os
import streamlit as st
import anthropic
import chromadb
from openai import OpenAI
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="PM Knowledge Assistant",
    page_icon="🧠",
    layout="wide"
)

# ── Initialize Clients ────────────────────────────────────────────────

@st.cache_resource
def get_clients():
    return {
        "anthropic": anthropic.Anthropic(
            api_key=st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        ),
        "openai": OpenAI(
            api_key=st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        ),
        "chroma": chromadb.PersistentClient(path="./vector_store")
    }

clients = get_clients()

# ── Core Functions ────────────────────────────────────────────────────

def get_embedding(text):
    response = clients["openai"].embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def get_or_create_collection():
    return clients["chroma"].get_or_create_collection(
        name="pm_knowledge",
        metadata={"hnsw:space": "cosine"}
    )

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def ingest_document(text, source_name, doc_type="general"):
    collection = get_or_create_collection()
    chunks = chunk_text(text)

    for i, chunk in enumerate(chunks):
        chunk_id = f"{source_name}_{i}"
        embedding = get_embedding(chunk)
        collection.add(
            ids=[chunk_id],
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{
                "source": source_name,
                "type": doc_type,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "ingested_at": datetime.now().isoformat()
            }]
        )
    return len(chunks)

def retrieve(query, doc_type_filter=None, n_results=4):
    collection = get_or_create_collection()
    query_embedding = get_embedding(query)

    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count() or 1)
    }

    if doc_type_filter and doc_type_filter != "All":
        query_args["where"] = {"type": doc_type_filter.lower()}

    results = collection.query(**query_args)

    context_pieces = []
    for doc, meta, dist in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ):
        similarity = 1 - (dist / 2)
        context_pieces.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "type": meta.get("type", "unknown"),
            "score": similarity
        })

    return context_pieces

def generate_answer(query, context_pieces):
    context_block = "\n\n---\n\n".join([
        f"[Source: {p['source']}]\n{p['text']}"
        for p in context_pieces
    ])

    response = clients["anthropic"].messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        temperature=0.3,
        system="""You are a knowledgeable assistant for ServiceNow product management.
        
Answer questions based ONLY on the provided context documents.
Always cite which [Source: ...] you drew from.
If the context doesn't contain enough information, say so clearly — never make up answers.
Be crisp and direct.""",
        messages=[{
            "role": "user",
            "content": f"Question: {query}\n\nContext:\n{context_block}"
        }]
    )

    return response.content[0].text, response.usage

# ── UI ────────────────────────────────────────────────────────────────

st.title("🧠 PM Knowledge Assistant")
st.caption("Ask questions grounded in your team's actual documents")

# Sidebar
with st.sidebar:
    st.header("📚 Knowledge Base")

    collection = get_or_create_collection()
    doc_count = collection.count()
    st.metric("Chunks indexed", doc_count)

    st.divider()
    st.subheader("Add Documents")

    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["txt", "md"],
        help="Upload text or markdown files"
    )

    doc_type = st.selectbox(
        "Document type",
        ["general", "technical", "performance", "strategy", "process"],
        help="Used for filtering searches"
    )

    if uploaded_file:
        if st.button("Index Document", type="primary"):
            with st.spinner(f"Indexing {uploaded_file.name}..."):
                text = uploaded_file.read().decode("utf-8")
                n_chunks = ingest_document(text, uploaded_file.name, doc_type)
            st.success(f"✅ Indexed {n_chunks} chunks from {uploaded_file.name}")
            st.rerun()

    # Show indexed sources
    if doc_count > 0:
        st.divider()
        st.subheader("Indexed Sources")
        all_docs = collection.get(include=['metadatas'])
        sources = {}
        for meta in all_docs['metadatas']:
            source = meta.get('source', 'unknown')
            doc_type_label = meta.get('type', 'unknown')
            if source not in sources:
                sources[source] = {"type": doc_type_label, "chunks": 0}
            sources[source]["chunks"] += 1

        for source, info in sources.items():
            st.markdown(f"**{source}**  \n`{info['type']}` · {info['chunks']} chunks")

# Main area
if doc_count == 0:
    st.info("👈 Upload documents in the sidebar to get started.")
    st.markdown("""
    ### How it works
    1. **Upload** your documents (txt or markdown files)
    2. **Ask** questions in plain English
    3. Get **grounded answers** citing your actual documents

    Unlike asking Claude directly, this assistant only answers from
    your uploaded documents — no hallucinated facts, no generic answers.
    """)
else:
    # Filter option
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Ask a question",
            placeholder="e.g. What signals identify an Economic Buyer?"
        )
    with col2:
        filter_type = st.selectbox(
            "Filter by type",
            ["All", "Technical", "Performance", "Strategy", "Process", "General"]
        )

    if query:
        with st.spinner("Searching knowledge base..."):
            context_pieces = retrieve(
                query,
                doc_type_filter=filter_type if filter_type != "All" else None
            )

        if not context_pieces:
            st.warning("No relevant documents found. Try a different question or upload more content.")
        else:
            with st.spinner("Generating answer..."):
                answer, usage = generate_answer(query, context_pieces)

            # Display answer
            st.markdown("### Answer")
            st.markdown(answer)

            # Cost info
            cost = (usage.input_tokens * 0.000003 + usage.output_tokens * 0.000015)
            st.caption(
                f"Tokens: {usage.input_tokens} in, {usage.output_tokens} out | "
                f"Cost: ~${cost:.4f}"
            )

            # Sources
            with st.expander("📄 Retrieved Sources"):
                for i, piece in enumerate(context_pieces, 1):
                    st.markdown(
                        f"**{i}. {piece['source']}** "
                        f"`{piece['type']}` "
                        f"· similarity: {piece['score']:.3f}"
                    )
                    st.text(piece['text'][:300] + "..." if len(piece['text']) > 300 else piece['text'])
                    if i < len(context_pieces):
                        st.divider()

            # Feedback
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Helpful"):
                    st.success("Thanks for the feedback!")
            with col2:
                if st.button("👎 Not helpful"):
                    st.info("Sorry — try rephrasing or uploading more relevant documents.")