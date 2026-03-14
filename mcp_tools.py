# mcp_tools.py
"""
PM Tool Server — MCP pattern.

Define tools once here. Any agent imports TOOL_DEFINITIONS and handle_tool_call.
Adding a new tool means adding it in exactly one place.
"""
import os
import json
from datetime import datetime
from pinecone import Pinecone
from openai import OpenAI

# Initialize once at module level
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ── Tool Manifest ─────────────────────────────────────────────────────────────
# This is what you'd expose in a real MCP server — the menu of available tools.

TOOL_DEFINITIONS = [
    {
        "name": "pm_knowledge_search",
        "description": """Search the PM knowledge base for company-specific information.
        Covers personalization strategy, Adobe Target configuration, buying group signals,
        Q3 results, and team strategies. Search multiple times with targeted queries
        for complex questions. Always search before answering company-specific questions.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific search query — be precise and targeted"
                },
                "filter_type": {
                    "type": "string",
                    "enum": ["technical", "performance", "strategy", "process", "any"],
                    "description": "Filter by document type. Use 'any' if unsure."
                },
                "n_results": {
                    "type": "integer",
                    "description": "Number of results (1-5). Default 3.",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_current_context",
        "description": """Get today's date, current quarter, and fiscal year context.
        Use this when the question involves timing, recency, or references to
        'this quarter', 'last quarter', 'this year', or any time-relative language.""",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "calculate_roi",
        "description": """Calculate realistic ROI for a personalization investment.
        Uses a traffic-derived model based on revenue and AOV inputs.
        Use this for any business case or investment question involving
        conversion lift, revenue impact, or payback period.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "annual_revenue": {
                    "type": "number",
                    "description": "Annual revenue in dollars"
                },
                "conversion_lift_pct": {
                    "type": "number",
                    "description": "Expected conversion lift as a percentage (e.g., 2.0 for 2%)"
                },
                "investment": {
                    "type": "number",
                    "description": "Investment amount in dollars"
                },
                "avg_order_value": {
                    "type": "number",
                    "description": "Average order value in dollars"
                }
            },
            "required": ["annual_revenue", "conversion_lift_pct", "investment", "avg_order_value"]
        }
    }
]

# ── Tool Handlers ─────────────────────────────────────────────────────────────

def pm_knowledge_search(query, filter_type="any", n_results=3):
    index = pc.Index("pm-knowledge")

    embedding = openai_client.embeddings.create(
        input=query, model="text-embedding-3-small"
    ).data[0].embedding

    kwargs = {
        "vector": embedding,
        "top_k": n_results,
        "include_metadata": True
    }
    if filter_type and filter_type != "any":
        kwargs["filter"] = {"type": {"$eq": filter_type}}

    results = index.query(**kwargs)

    if not results.matches:
        return json.dumps({"found": False, "message": "No relevant documents found."})

    items = [
        {
            "source": m.metadata["source"],
            "relevance": round(m.score, 3),
            "type": m.metadata.get("type", "unknown"),
            "content": m.metadata["text"]
        }
        for m in results.matches
    ]

    return json.dumps({"found": True, "results": items})

def get_current_context():
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1

    return json.dumps({
        "date": now.strftime("%Y-%m-%d"),
        "quarter": f"Q{quarter} {now.year}",
        "fiscal_note": "ServiceNow FY starts February 1",
        "days_into_quarter": (now.month - 1) % 3 * 30 + now.day
    })

def calculate_roi(annual_revenue, conversion_lift_pct, investment, avg_order_value):
    # Derive traffic from revenue and AOV
    baseline_conversion = 0.02
    traffic = annual_revenue / (avg_order_value * baseline_conversion)

    current_transactions = traffic * baseline_conversion
    new_transactions = traffic * (baseline_conversion + conversion_lift_pct / 100)
    additional_transactions = new_transactions - current_transactions
    additional_revenue = additional_transactions * avg_order_value

    roi_pct = ((additional_revenue - investment) / investment) * 100
    payback_months = (investment / additional_revenue) * 12 if additional_revenue > 0 else float("inf")

    return json.dumps({
        "additional_revenue": round(additional_revenue, 2),
        "roi_percentage": round(roi_pct, 1),
        "payback_months": round(payback_months, 1),
        "note": "Traffic-derived model based on revenue and AOV inputs"
    })

# ── Dispatch ──────────────────────────────────────────────────────────────────
# One function to route any tool call to the right handler.
# This is the MCP server's core responsibility.

def handle_tool_call(tool_name, tool_input):
    handlers = {
        "pm_knowledge_search": lambda: pm_knowledge_search(
            tool_input["query"],
            tool_input.get("filter_type", "any"),
            tool_input.get("n_results", 3)
        ),
        "get_current_context": get_current_context,
        "calculate_roi": lambda: calculate_roi(
            tool_input["annual_revenue"],
            tool_input["conversion_lift_pct"],
            tool_input["investment"],
            tool_input["avg_order_value"]
        )
    }

    handler = handlers.get(tool_name)
    if handler:
        return handler()
    return json.dumps({"error": f"Unknown tool: {tool_name}"})