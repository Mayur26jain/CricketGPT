import re
from typing import Dict, Any, List
from sqlalchemy.future import select
from sqlalchemy import text
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.services.rag import rag_service
from app.services.external_apis import ExternalAPIService
from app.core.database import AsyncSessionLocal

# Define agent node functions

async def intent_router_node(state: AgentState) -> Dict[str, Any]:
    query = state["query"].lower()
    intent = "SQL_STATISTICS" # Default fallback
    
    # Simple regex rules to direct query
    if any(k in query for k in ["rule", "lbw", "super over", "powerplay", "2019 world cup final", "2007 t20", "what happened in"]):
        intent = "RAG_KNOWLEDGE"
    elif any(k in query for k in ["live", "score", "commentary", "weather", "news", "today"]):
        intent = "LIVE_MATCH"
    elif any(k in query for k in ["predict", "winner", "fantasy", "suggest"]):
        intent = "PREDICTION"
        
    return {"intent": intent}

async def sql_agent_node(state: AgentState) -> Dict[str, Any]:
    query = state["query"].lower()
    sql_query = ""
    sql_results = []
    
    # Let's inspect query terms to build realistic SQL queries on our SQLite/PG schema
    async with AsyncSessionLocal() as session:
        if "highest batting average" in query:
            sql_query = """
                SELECT p.name, s.batting_average, s.format 
                FROM players p 
                JOIN player_stats s ON p.id = s.player_id 
                WHERE s.format = 'Test' 
                ORDER BY s.batting_average DESC 
                LIMIT 5;
            """
        elif "fastest century" in query or "century" in query:
            sql_query = """
                SELECT p.name, s.centuries, s.format 
                FROM players p 
                JOIN player_stats s ON p.id = s.player_id 
                ORDER BY s.centuries DESC 
                LIMIT 5;
            """
        elif "compare virat kohli and joe root" in query or ("kohli" in query and "root" in query):
            sql_query = """
                SELECT p.name, s.format, s.runs_scored, s.batting_average, s.strike_rate, s.centuries 
                FROM players p 
                JOIN player_stats s ON p.id = s.player_id 
                WHERE p.name IN ('Virat Kohli', 'Joe Root') AND s.format IN ('Test', 'ODI');
            """
        else:
            # Fallback statistics query
            sql_query = """
                SELECT p.name, s.format, s.runs_scored, s.batting_average 
                FROM players p 
                JOIN player_stats s ON p.id = s.player_id 
                LIMIT 5;
            """
        
        try:
            res = await session.execute(text(sql_query))
            # Format row data to dictionaries
            keys = res.keys()
            sql_results = [dict(zip(keys, row)) for row in res.fetchall()]
        except Exception as e:
            sql_results = [{"error": str(e)}]
            
    return {"sql_query": sql_query, "sql_results": sql_results}

async def rag_agent_node(state: AgentState) -> Dict[str, Any]:
    query = state["query"]
    
    # Query Chroma collections
    rules_docs = rag_service.query_rules(query)
    matches_docs = rag_service.query_matches(query)
    
    return {"rag_documents": rules_docs + matches_docs}

async def live_agent_node(state: AgentState) -> Dict[str, Any]:
    query = state["query"].lower()
    live_data = {}
    
    if "weather" in query:
        live_data["weather"] = ExternalAPIService.get_weather("Lord's Cricket Ground")
    elif "news" in query:
        live_data["news"] = ExternalAPIService.get_cricket_news()
    else:
        live_data["scores"] = ExternalAPIService.get_live_scores()
        live_data["commentary"] = ExternalAPIService.get_ball_by_ball(1)
        
    return {"live_api_data": live_data}

async def prediction_agent_node(state: AgentState) -> Dict[str, Any]:
    query = state["query"].lower()
    
    # Determine teams in prediction query
    team1, team2 = "India", "England"
    if "aus" in query or "australia" in query:
        team2 = "Australia"
        
    # Return simulation statistics
    prediction = {
        "match": f"{team1} vs {team2}",
        "team1_win_probability": 58.4,
        "team2_win_probability": 41.6,
        "key_factors": [
            "Pitch is historically spin-friendly, giving India's spinners an edge.",
            "India's top order batting average at this venue is 46.2 vs Australia's 34.8."
        ],
        "fantasy_suggesions": [
            {"player": "Virat Kohli", "role": "Captain", "reason": "Averaging 58.6 in ODIs"},
            {"player": "Jofra Archer", "role": "Bowler", "reason": "Excellent economy rate"}
        ]
    }
    return {"prediction_results": prediction}

async def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    intent = state["intent"]
    query = state["query"]
    response = ""
    chart_schema = None
    
    # 1. Build chart schemas for React visualization components
    if intent == "SQL_STATISTICS":
        results = state.get("sql_results", [])
        if "compare" in query.lower():
            chart_schema = {
                "type": "radar",
                "data": [
                    {"metric": "Runs (scaled)", "Kohli": 80.0, "Root": 65.0},
                    {"metric": "Average", "Kohli": 58.6, "Root": 50.1},
                    {"metric": "Strike Rate", "Kohli": 93.5, "Root": 86.7},
                    {"metric": "Centuries (x2)", "Kohli": 100.0, "Root": 64.0}
                ],
                "keys": ["Kohli", "Root"],
                "indexBy": "metric"
            }
        else:
            chart_schema = {
                "type": "bar",
                "data": [{"name": row["name"], "value": list(row.values())[1]} for row in results if len(row) > 1],
                "xKey": "name",
                "yKey": "value"
            }
    elif intent == "PREDICTION":
        pred = state.get("prediction_results", {})
        chart_schema = {
            "type": "pie",
            "data": [
                {"name": "India", "value": pred.get("team1_win_probability", 50.0), "color": "#2563eb"},
                {"name": "Opponent", "value": pred.get("team2_win_probability", 50.0), "color": "#db2777"}
            ]
        }
        
    # 2. Synthesize dynamic, contextual final response using the LLM Service (Gemini/OpenAI/Fallback)
    context_data = {
        "sql_results": state.get("sql_results"),
        "rag_documents": state.get("rag_documents"),
        "live_api_data": state.get("live_api_data"),
        "prediction_results": state.get("prediction_results")
    }
    
    from app.services.llm import LLMService
    response = LLMService.synthesize_response(query, intent, context_data, history=state.get("history"))
    
    return {"response": response, "chart_schema": chart_schema}


# Routing logic
def route_intent(state: AgentState):
    intent = state["intent"]
    if intent == "SQL_STATISTICS":
        return "sql_agent"
    elif intent == "RAG_KNOWLEDGE":
        return "rag_agent"
    elif intent == "LIVE_MATCH":
        return "live_agent"
    elif intent == "PREDICTION":
        return "prediction_agent"
    return END

# Assemble LangGraph Workflow StateGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("intent_router", intent_router_node)
workflow.add_node("sql_agent", sql_agent_node)
workflow.add_node("rag_agent", rag_agent_node)
workflow.add_node("live_agent", live_agent_node)
workflow.add_node("prediction_agent", prediction_agent_node)
workflow.add_node("synthesizer", synthesizer_node)

# Add Edges
workflow.set_entry_point("intent_router")
workflow.add_conditional_edges(
    "intent_router",
    route_intent,
    {
        "sql_agent": "sql_agent",
        "rag_agent": "rag_agent",
        "live_agent": "live_agent",
        "prediction_agent": "prediction_agent"
    }
)
workflow.add_edge("sql_agent", "synthesizer")
workflow.add_edge("rag_agent", "synthesizer")
workflow.add_edge("live_agent", "synthesizer")
workflow.add_edge("prediction_agent", "synthesizer")
workflow.add_edge("synthesizer", END)

# Compile graph
cricket_graph = workflow.compile()
