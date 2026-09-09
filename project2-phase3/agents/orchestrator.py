"""
Orchestrator (Phase 3 - domain-aware pipeline)
------------------------------------------------
Phase 2 version only had 2 steps: Clean -> Analyze.
Phase 3 adds two new steps on either end:

  Domain Config -> Clean -> Analyze -> Dashboard

The Domain Config Agent runs FIRST and inspects whatever dataset comes in,
so the whole rest of the pipeline works on any domain (retail, restaurant,
inventory, ecommerce, etc.) without being rewritten per dataset.

Built with LangGraph:
- state  = the data that gets passed along and updated at every step
- node   = one agent's work (domain config, clean, analyze, or dashboard)
- edge   = what runs next after a node finishes
"""

import json
import os
import pandas as pd
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.domain_config_agent import detect_domain_config
from agents.clean_agent import clean_data
from agents.analysis_agent import analyze_data
from agents.dashboard_agent import build_dashboard


# ---- STATE ----
class PipelineState(TypedDict):
    raw_df: Optional[pd.DataFrame]
    domain_config: Optional[dict]
    cleaned_df: Optional[pd.DataFrame]
    insights: Optional[dict]
    dashboard_path: Optional[str]


# ---- NODES ----

def domain_config_node(state: PipelineState) -> PipelineState:
    print("\n[Orchestrator] Routing to Domain Config Agent...")
    config = detect_domain_config(state["raw_df"])
    return {"domain_config": config}


def clean_node(state: PipelineState) -> PipelineState:
    print("\n[Orchestrator] Routing to Clean Agent...")
    cleaned = clean_data(state["raw_df"], state["domain_config"])
    return {"cleaned_df": cleaned}


def analysis_node(state: PipelineState) -> PipelineState:
    print("\n[Orchestrator] Routing to Analysis Agent...")
    insights = analyze_data(state["cleaned_df"], state["domain_config"])
    return {"insights": insights}


def dashboard_node(state: PipelineState) -> PipelineState:
    print("\n[Orchestrator] Routing to Dashboard Agent...")
    domain = state["domain_config"].get("domain", "unknown")
    assets_dir = f"assets_{domain}"
    path = build_dashboard(state["insights"], assets_dir=assets_dir)
    return {"dashboard_path": path}


# ---- BUILD THE GRAPH ----
def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("domain_config", domain_config_node)
    graph.add_node("clean", clean_node)
    graph.add_node("analyze", analysis_node)
    graph.add_node("dashboard", dashboard_node)

    graph.set_entry_point("domain_config")
    graph.add_edge("domain_config", "clean")
    graph.add_edge("clean", "analyze")
    graph.add_edge("analyze", "dashboard")
    graph.add_edge("dashboard", END)

    return graph.compile()


def run_pipeline(csv_path: str):
    """Run the full pipeline on any CSV file, no code changes needed per dataset."""
    print(f"[Orchestrator] Received {csv_path}. Deciding processing order...")

    raw_df = pd.read_csv(csv_path)

    pipeline = build_graph()
    final_state = pipeline.invoke({
        "raw_df": raw_df,
        "domain_config": None,
        "cleaned_df": None,
        "insights": None,
        "dashboard_path": None,
    })

    os.makedirs("data", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(csv_path))[0]

    final_state["cleaned_df"].to_csv(f"data/{base_name}_cleaned.csv", index=False)
    with open(f"data/{base_name}_domain_config.json", "w") as f:
        json.dump(final_state["domain_config"], f, indent=2)
    with open(f"data/{base_name}_insights.json", "w") as f:
        json.dump(final_state["insights"], f, indent=2, default=str)

    print("\n[Orchestrator] Pipeline complete.")
    domain_name = final_state['domain_config']['domain']
    print(f"[Orchestrator] Domain detected -> {domain_name}")
    print(f"[Orchestrator] Cleaned data -> data/{base_name}_cleaned.csv")
    print(f"[Orchestrator] Insights -> data/{base_name}_insights.json")
    dashboard_path = final_state['dashboard_path']
    print(f"[Orchestrator] Dashboard -> {dashboard_path}")

    return final_state


if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/superstore.csv"
    run_pipeline(csv_path)

