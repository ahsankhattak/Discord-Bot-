# Project 2 — Phase 2: Multi-Agent Retail Data Pipeline

A working multi-agent pipeline built with LangChain + LangGraph that takes a raw retail sales CSV, cleans it, analyzes it, and presents the results on a static dashboard — coordinated by an orchestrator agent.

## Dataset

Used the "Superstore" retail sales dataset from Kaggle (`data/superstore.csv`) — 800 rows with columns for Region, Category, Sub-Category, Product Name, Sales, Quantity, Discount, and Profit.

## The Agents

**Orchestrator** (`agents/orchestrator.py`) — the manager. Doesn't clean or analyze anything itself. Built with LangGraph: defines a graph with a shared `state` (the data being passed along), and two `nodes` connected by `edges` — it decides the raw data goes to the Clean Agent first, then the result goes to the Analysis Agent.

**Clean Agent** (`agents/clean_agent.py`) — removes duplicate rows, converts numeric columns that may have been read as text, drops rows missing critical fields, and removes rows with negative sales/quantity. On this dataset nothing needed removing (it was already clean), which the terminal output confirms.

**Analysis Agent** (`agents/analysis_agent.py`) — calculates total sales, total profit, total orders, units sold, the top 5 best-selling products, and sales broken down by region and category.

**Dashboard/Visualization Agent** (`agents/dashboard_agent.py`) — the bonus agent. Reads the analysis output and generates 3 charts (sales by region, sales by category, top 5 products) plus a static HTML dashboard summarizing everything.

## The Flow

```
raw CSV → Orchestrator → Clean Agent → Analysis Agent → Dashboard
```

1. `data/superstore.csv` (raw) is loaded.
2. The Orchestrator routes it through the graph: `clean` node runs first — see `assets/cleaning-result.png` for the terminal output showing this step.
3. The `analyze` node runs next — see `assets/analysis-output.png` for the generated insights (total sales, profit, top products, regional/category breakdown).
4. The full graph running end-to-end (Orchestrator routing between both agents) is shown in `assets/flow-diagram.png`.
5. Finally, the Dashboard Agent turns the insights into charts and a static page — see `assets/dashboard-preview.png` and `assets/dashboard.html` for the final result.

## How to run it

```
python -m venv venv
venv\Scripts\activate
pip install langchain langgraph langchain-groq pandas matplotlib
python -m agents.orchestrator
python agents/dashboard_agent.py
```

Then open `assets/dashboard.html` in any browser.

## What I learned

Building the orchestrator with LangGraph made the node/edge/state concepts from Phase 1 concrete — the state (a dictionary carrying the dataframe and insights) gets passed and updated as it moves through each node, and the edges are just "what runs next." Keeping the pipeline to two required agents plus one bonus agent, instead of overcomplicating it, made it much easier to get a fully working end-to-end result.
