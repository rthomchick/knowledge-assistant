# knowledge_assistant_v3.py
import streamlit as st
import anthropic
import hashlib
import os
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI
from mcp_tools import TOOL_DEFINITIONS, handle_tool_call

st.set_page_config(
    page_title="PM Knowledge Assistant",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 PM Knowledge Assistant")
st.caption("Powered by Pinecone + Claude")

@st.cache_resource
def get_clients():
    return {
        "anthropic": anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"]),
        "openai": OpenAI(api_key=st.secrets["OPENAI_API_KEY"]),
        "pinecone": Pinecone(api_key=st.secrets["PINECONE_API_KEY"]).Index("pm-knowledge")
    }

clients = get_clients()

def get_embedding(text):
    return clients["openai"].embeddings.create(
        input=text, model="text-embedding-3-small"
    ).data[0].embedding

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size - overlap)
        if " ".join(words[i:i + chunk_size]).strip()
    ]

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("📚 Knowledge Base")
    stats = clients["pinecone"].describe_index_stats()
    st.metric("Vectors indexed", stats.total_vector_count)

    st.divider()
    st.subheader("Add Documents")

    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["txt", "md"],
        help="Text or markdown files"
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

    st.divider()
    st.caption("💡 Use **Knowledge Search** for quick lookups.\n\nUse **Strategy Assistant** for complex questions that need research across multiple sources.")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["📚 Knowledge Search", "🎯 Strategy Assistant"])

# ── Tab 1: Simple RAG ─────────────────────────────────────────────────────────

with tab1:
    st.subheader("Knowledge Search")
    st.caption("Fast lookups grounded in your indexed documents.")

    filter_type = st.selectbox(
        "Filter by document type (optional)",
        ["All", "technical", "performance", "strategy", "process"],
        key="filter_tab1"
    )

    query = st.text_input(
        "What do you want to know?",
        placeholder="e.g., What were our Q3 conversion results?",
        key="query_tab1"
    )

    if query:
        with st.spinner("Searching..."):
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
            st.warning("No relevant documents found.")
        else:
            context_pieces = [
                f"[Source: {m.metadata['source']} | Relevance: {m.score:.2f}]\n{m.metadata['text']}"
                for m in results.matches
            ]
            context_block = "\n\n---\n\n".join(context_pieces)

            with st.spinner("Generating answer..."):
                response = clients["anthropic"].messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1000,
                    temperature=0.3,
                    system="""Answer ONLY from the provided context. Cite [Source: ...] tags.
                    If context is insufficient, say so. Be direct and McKinsey-style.""",
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

# ── Tab 2: Strategy Assistant ─────────────────────────────────────────────────

with tab2:
    st.subheader("Strategy Assistant")
    st.caption("For complex questions that require research across multiple sources. Takes 60-90 seconds.")

    strategy_q = st.text_area(
        "Strategy question",
        placeholder="e.g., What should our personalization strategy be for Q4 given our Q3 results?",
        height=100,
        key="query_tab2"
    )

    if st.button("Generate Strategy", type="primary"):
        if not strategy_q:
            st.error("Please enter a strategy question.")
        else:
            # ── Planner ──
            with st.status("🔄 Running strategy analysis...", expanded=True) as status:

                st.write("**Step 1: Planning research questions...**")
                plan_response = clients["anthropic"].messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=500,
                    temperature=0.0,
                    messages=[{
                        "role": "user",
                        "content": f"""Break this strategy question into exactly 3 specific sub-questions
that together would fully answer it. Each must be independently researchable.

Strategy question: {strategy_q}

Return ONLY a numbered list."""
                    }]
                )

                sub_questions = [
                    line.split(". ", 1)[1].strip()
                    for line in plan_response.content[0].text.strip().split("\n")
                    if line.strip() and line[0].isdigit()
                ]

                for q in sub_questions:
                    st.write(f"  → {q}")

                # ── Workers ──
                st.write(f"\n**Step 2: Researching {len(sub_questions)} sub-questions...**")
                worker_outputs = []

                for i, sq in enumerate(sub_questions, 1):
                    st.write(f"  Worker {i}: {sq[:60]}...")

                    messages = [{"role": "user", "content": f"Research and answer: {sq}"}]
                    worker_system = """You are a research agent for a ServiceNow PM strategy team.
                    Search the knowledge base to answer ONE specific sub-question.
                    Be specific and cite sources. 150-300 words maximum."""

                    # Worker agent loop
                    for _ in range(6):
                        resp = clients["anthropic"].messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=1500,
                            temperature=0.3,
                            system=worker_system,
                            tools=TOOL_DEFINITIONS,
                            messages=messages
                        )

                        if resp.stop_reason == "tool_use":
                            messages.append({"role": "assistant", "content": resp.content})
                            tool_results = []
                            for block in resp.content:
                                if block.type == "tool_use":
                                    result = handle_tool_call(block.name, block.input)
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": result
                                    })
                            messages.append({"role": "user", "content": tool_results})
                        else:
                            output = next(
                                (b.text for b in resp.content if hasattr(b, "text")),
                                "No output."
                            )
                            worker_outputs.append(output)
                            st.write(f"  ✅ Worker {i} complete")
                            break

                # ── Synthesizer ──
                st.write("\n**Step 3: Synthesizing recommendation...**")

                research_block = "\n\n".join([
                    f"Research {i+1}:\n{output}"
                    for i, output in enumerate(worker_outputs)
                ])

                synth_response = clients["anthropic"].messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2500,
                    temperature=0.3,
                    system="""You are a McKinsey-style strategic advisor for ServiceNow personalization.
                    Structure: Situation → Key Findings → Prioritized Recommendations → Next Steps.
                    Cite specific numbers. 400-600 words.""",
                    messages=[{
                        "role": "user",
                        "content": f"Question: {strategy_q}\n\nResearch:\n{research_block}"
                    }]
                )

                recommendation = synth_response.content[0].text
                status.update(label="✅ Strategy complete!", state="complete")

            st.markdown("### Strategy Recommendation")
            st.markdown(recommendation)

            with st.expander("🔬 Research Details"):
                for i, (sq, output) in enumerate(zip(sub_questions, worker_outputs), 1):
                    st.markdown(f"**Sub-question {i}:** {sq}")
                    st.markdown(output)
                    st.divider()