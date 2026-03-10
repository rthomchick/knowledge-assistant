# knowledge_assistant_v2.py
import streamlit as st
import anthropic
import hashlib
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI

st.set_page_config(
    page_title="PM Knowledge Assistant",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 PM Knowledge Assistant")
st.caption("Grounded answers from your team's actual documents — powered by Pinecone + Claude")

@st.cache_resource
def get_clients():
    return {
        "anthropic": anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"]),
        "openai": OpenAI(api_key=st.secrets["OPENAI_API_KEY"]),
        "pinecone": Pinecone(api_key=st.secrets["PINECONE_API_KEY"]).Index("pm-knowledge")
    }

clients = get_clients()

def get_embedding(text):
    response = clients["openai"].embeddings.create(
        input=text, model="text-embedding-3-small"
    )
    return response.data[0].embedding

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size - overlap)
        if " ".join(words[i:i + chunk_size]).strip()
    ]

SYSTEM_PROMPT = """You are a knowledgeable assistant for ServiceNow product management.
Answer ONLY from the provided context. Cite [Source: ...] tags.
If context is insufficient, say so clearly. Be direct and McKinsey-style."""

# Sidebar: Document Management
with st.sidebar:
    st.header("📚 Knowledge Base")

    stats = clients["pinecone"].describe_index_stats()
    st.metric("Vectors indexed", stats.total_vector_count)

    st.divider()
    st.subheader("Add Documents")

    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["txt", "md"],
        help="Upload text or markdown files to add to the knowledge base"
    )
    doc_type = st.selectbox(
        "Document type",
        ["technical", "performance", "strategy", "process"]
    )

    if uploaded_file and st.button("Index Document"):
        text = uploaded_file.read().decode("utf-8")
        chunks = chunk_text(text)

        with st.spinner(f"Indexing {len(chunks)} chunks..."):
            vectors = []
            for i, chunk in enumerate(chunks):
                embedding = get_embedding(chunk)
                chunk_id = hashlib.md5(
                    f"{uploaded_file.name}_{i}".encode()
                ).hexdigest()[:16]
                vectors.append({
                    "id": chunk_id,
                    "values": embedding,
                    "metadata": {
                        "source": uploaded_file.name,
                        "type": doc_type,
                        "text": chunk,
                        "chunk_index": i,
                        "ingested_at": datetime.now().isoformat()
                    }
                })

                if len(vectors) >= 100:
                    clients["pinecone"].upsert(vectors=vectors)
                    vectors = []

            if vectors:
                clients["pinecone"].upsert(vectors=vectors)

        st.success(f"✅ Indexed {len(chunks)} chunks from {uploaded_file.name}")
        st.rerun()

# Main: Ask Questions
st.subheader("Ask a Question")

filter_type = st.selectbox(
    "Filter by document type (optional)",
    ["All", "technical", "performance", "strategy", "process"]
)

query = st.text_input(
    "What do you want to know?",
    placeholder="e.g., What were our Q3 conversion results?"
)

if query:
    with st.spinner("Searching knowledge base..."):
        query_embedding = get_embedding(query)

        search_kwargs = {
            "vector": query_embedding,
            "top_k": 5,
            "include_metadata": True
        }

        if filter_type != "All":
            search_kwargs["filter"] = {"type": {"$eq": filter_type}}

        results = clients["pinecone"].query(**search_kwargs)

    if not results.matches:
        st.warning("No relevant documents found. Try uploading more content.")
    else:
        context_pieces = [
            f"[Source: {m.metadata['source']} | Type: {m.metadata.get('type', 'unknown')} | Relevance: {m.score:.2f}]\n{m.metadata['text']}"
            for m in results.matches
        ]
        context_block = "\n\n---\n\n".join(context_pieces)

        with st.spinner("Generating grounded answer..."):
            response = clients["anthropic"].messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                temperature=0.3,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Question: {query}\n\nContext:\n{context_block}"
                }]
            )

        st.markdown("### Answer")
        st.markdown(response.content[0].text)

        with st.expander("📚 Sources Retrieved"):
            for m in results.matches:
                st.markdown(
                    f"**{m.metadata['source']}** "
                    f"(score: {m.score:.3f} | type: {m.metadata.get('type', 'unknown')})"
                )
                st.text(m.metadata['text'][:200] + "...")
                st.divider()

        st.caption(
            f"Tokens: {response.usage.input_tokens} in, "
            f"{response.usage.output_tokens} out | "
            f"Cost: ~${(response.usage.input_tokens * 0.000003 + response.usage.output_tokens * 0.000015):.4f}"
        )