import os
import requests
import urllib3
from app.config import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LLMService:
    @staticmethod
    def synthesize_response(query: str, intent: str, context_data: dict, history: list = None) -> str:
        """Synthesizes a response using Gemini or OpenAI based on query, intent, context, and history."""
        # Clean history for prompt context
        history_str = ""
        if history:
            history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-5:]])
            
        # Build prompt
        system_prompt = (
            "You are CricketGPT, an expert AI cricket assistant and analyst. "
            "You have access to structured data retrieved from database/API tools. "
            "Your job is to synthesize a professional, engaging, and accurate response "
            "answering the user's query using the provided context data and chat history.\n"
            "Guidelines:\n"
            "1. Be factual and clear. Do not invent stats or information.\n"
            "2. Keep the formatting clean using markdown.\n"
            "3. Do NOT mention that you are an AI or using tools/contexts unless asked."
        )
        
        user_prompt = f"User Query: {query}\n"
        if history_str:
            user_prompt += f"Recent Chat History:\n{history_str}\n\n"
        user_prompt += f"Retrieved Context Data ({intent}): {context_data}\n\n"
        user_prompt += "Please synthesize the final answer:"
        
        # 1. Try Gemini first (preferred)
        if settings.GEMINI_API_KEY:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": f"{system_prompt}\n\n{user_prompt}"
                                }
                            ]
                        }
                    ]
                }
                res = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
                if res.status_code == 200:
                    data = res.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if text:
                        return text.strip()
            except Exception as e:
                print("Gemini API call failed:", e)
                
        # 2. Try OpenAI fallback
        if settings.OPENAI_API_KEY:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
                }
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3
                }
                res = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
                if res.status_code == 200:
                    data = res.json()
                    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if text:
                        return text.strip()
            except Exception as e:
                print("OpenAI API call failed:", e)
                
        # 3. Local templates fallback if no API key is available or both fail
        return LLMService.local_synthesize_fallback(query, intent, context_data)
        
    @staticmethod
    def local_synthesize_fallback(query: str, intent: str, context_data: dict) -> str:
        if intent == "SQL_STATISTICS":
            results = context_data.get("sql_results", [])
            if "compare" in query.lower():
                response = f"Here is the statistics comparison for your query: **'{query}'**.\n\n"
                response += "| Player | Format | Runs | Average | Strike Rate | Centuries |\n"
                response += "|---|---|---|---|---|---|\n"
                for row in results:
                    response += f"| {row.get('name')} | {row.get('format')} | {row.get('runs_scored', 0)} | {row.get('batting_average', 0.0)} | {row.get('strike_rate', 0.0)} | {row.get('centuries', 0)} |\n"
                return response
            else:
                response = f"According to historical statistics matching your query:\n\n"
                for index, row in enumerate(results):
                    response += f"{index+1}. **{row.get('name')}**: {list(row.values())[1]} ({row.get('format', 'N/A')})\n"
                return response
        elif intent == "RAG_KNOWLEDGE":
            docs = context_data.get("rag_documents", [])
            if docs:
                return "Based on CricketGPT rules and historical knowledge:\n\n" + "\n".join([f"- {doc}" for doc in docs])
            return "I couldn't find matches in my knowledge base. Cricket matches usually consist of runs, wickets, and exciting overs!"
        elif intent == "LIVE_MATCH":
            api_data = context_data.get("live_api_data", {})
            if "scores" in api_data and api_data["scores"]:
                score = api_data["scores"][0]
                response = f"### Live Score: {score['team_home']} vs {score['team_away']}\n"
                response += f"**Venue**: {score['venue']} | **Status**: {score['status']}\n\n"
                response += f"- **{score['team_home']}**: {score['scores']['team_home_runs']}/{score['scores']['team_home_wickets']} ({score['scores']['team_home_overs']} ov)\n"
                return response
            return "No live matches available at this moment."
        elif intent == "PREDICTION":
            pred = context_data.get("prediction_results", {})
            response = f"### AI Match Prediction: {pred.get('match')}\n\n"
            response += f"- **Win Probability**: {pred.get('team1_win_probability', 50)}% vs {pred.get('team2_win_probability', 50)}%\n"
            return response
        return "Could not process request."

llm_service = LLMService()
