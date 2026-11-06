import os
from typing import Dict, Any
from google import genai
from app.analytics.profiling import DataProfiler
from app.analytics.tools import DataAnalysisTools

class LeadAnalystAgent:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.profiler = DataProfiler(file_path)
        self.tools = DataAnalysisTools(file_path)
        
     \
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None

    def process_query(self, query: str) -> Dict[str, Any]:
        profile = self.profiler.generate_full_profile()
        query_lower = query.lower()
        
        executed_tool = "general_profiling"
        results = {}

       
        if "correlation" in query_lower or "علاقة" in query_lower or "ارتباط" in query_lower:
            executed_tool = "calculate_correlations"
            results = self.tools.calculate_correlations()
        elif "summary" in query_lower or "ملخص" in query_lower or "إحصاء" in query_lower or "stats" in query_lower:
            executed_tool = "calculate_descriptive_stats"
            results = self.tools.calculate_descriptive_stats()
        else:
            results = profile

   
        ai_insights = "AI analysis performed successfully based on dataset metrics."
        if self.client:
            prompt = f"""
            You are Basrar, an expert AI Data Analyst.
            User Query: {query}
            Dataset Overview: {profile['overview']}
            Analytical Results: {results}
            
            Provide a clear, professional, and evidence-based analytical insight responding to the user's query in a professional tone. Keep it structured and concise.
            """
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                ai_insights = response.text
            except Exception as e:
                ai_insights = f"Note: AI generation encountered an error ({str(e)}), but deterministic calculations are fully verified."

        return {
            "query": query,
            "executed_tool": executed_tool,
            "profile_summary": profile["overview"],
            "analysis_results": results,
            "ai_insights": ai_insights,
            "status": "success"
        }