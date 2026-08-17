from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    query: str
    intent: Optional[str]
    sql_query: Optional[str]
    sql_results: Optional[List[Dict[str, Any]]]
    rag_documents: Optional[List[str]]
    live_api_data: Optional[Dict[str, Any]]
    prediction_results: Optional[Dict[str, Any]]
    chart_schema: Optional[Dict[str, Any]]
    response: Optional[str]
    history: List[Dict[str, str]]
