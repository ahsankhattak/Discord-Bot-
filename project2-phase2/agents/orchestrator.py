"""
Orchestrator
------------
This is the "manager" agent from Phase 1. It doesn't clean or analyze data itself -
it defines the graph (nodes + edges) and decides the order things happen in:
raw data -> Clean Agent -> Analysis Agent -> done.

Built with LangGraph:
- state  = the data that gets passed along and updated at every step
- node   = one agent's work (clean, or analyze)
- edge   = what runs next after a node finishes
"""

import json
import pandas as pd
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.clean_agent import clean_data
from agents.analysis_agent import analyze_data


# ---- STATE ----
# This is the shared "backpack" of data that gets passed from node to node,
# each node reads from it and updates it before passing it along.
class PipelineState(TypedDict):
    raw_df: Optional[pd.DataFrame]
    cleaned_df: Optional[pd.DataFrame]
    insights: Optional[dict]


# ---- NODES ----
# Each node is just a function: takes the current state, returns updates to it.

def clean_node(state: PipelineState) -> PipelineState:
    print("\n[Orchestrator] Routing to Clean Agent...")
    cleaned = clean_data(state["raw_df"])
    return {"cleaned_df": cleaned}


def analysis_node(state: PipelineState) -> PipelineState:
    print("\n[Orchestrator] Routing to Analysis Agent...")
    insights = analyze_data(state["cleaned_df"])
    return {"insights": insights}


# ---- BUILD THE GRAPH ----
def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("clean", clean_node)
    graph.add_node("analyze", analysis_node)

    # edges: what happens next
    graph.set_entry_point("clean")
    graph.add_edge("clean", "analyze")
    graph.add_edge("analyze", END)

    return graph.compile()


if __name__ == "__main__":
    print("[Orchestrator] Received raw retail CSV. Deciding processing order...")

    raw_df = pd.read_csv("data/superstore.csv")

    pipeline = build_graph()
    final_state = pipeline.invoke({"raw_df": raw_df, "cleaned_df": None, "insights": None})

    # Save outputs so the dashboard step can use them
    final_state["cleaned_df"].to_csv("data/superstore_cleaned.csv", index=False)
    with open("data/insights.json", "w") as f:
        json.dump(final_state["insights"], f, indent=2)

    print("\n[Orchestrator] Pipeline complete.")
    print("[Orchestrator] Cleaned data -> data/superstore_cleaned.csv")
    print("[Orchestrator] Insights -> data/insights.json")
