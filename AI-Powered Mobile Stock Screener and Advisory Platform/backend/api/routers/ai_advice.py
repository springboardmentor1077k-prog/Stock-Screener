"""
AI Advice API Router
Provides endpoints for AI-powered investment advice and insights
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
from ...database.connection import get_db
from ...auth.jwt_handler import get_current_user
from ...models.database import User
from ...core.cache import ai_advice_cache

# Define request/response models
class AIAdviceRequest(BaseModel):
    query: str

class AIAdviceResponse(BaseModel):
    advice: str
    confidence: float
    sources: list[str]

ai_advice_router = APIRouter()

@ai_advice_router.post("/ai-advice", response_model=Dict[str, str])
def get_ai_advice(request: AIAdviceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get AI-powered investment advice based on user query using OpenAI.
    Falls back to rule-based responses if OpenAI is not configured.
    """
    from ...core.utils import handle_database_error
    from ...core.config import settings
    import openai
    
    try:
        query = request.query.strip()
        query_lower = query.lower()

        # First, attempt to serve from cache for frequent / repeated questions
        cached = ai_advice_cache.get(query_lower)
        if cached is not None:
            return {"advice": cached}
        
        # Check if OpenAI API key is configured
        if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key":
            # Use OpenAI for real AI responses
            try:
                client = openai.OpenAI(api_key=settings.openai_api_key)
                
                system_prompt = """
                You are an AI investment advisor for a stock screener application. Provide helpful, 
                informative responses about stocks, investing, and financial markets. Be professional 
                and accurate. If asked for specific investment advice, remind users to consult 
                licensed financial advisors. Keep responses concise but informative (2-3 paragraphs max).
                """
                
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                response = completion.choices[0].message.content

                # Store successful LLM response in cache
                ai_advice_cache.set(query_lower, response)
                return {"advice": response}
                
            except Exception as openai_error:
                # Log the OpenAI error and fall back to rule-based responses
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"OpenAI API error: {str(openai_error)}. Falling back to rule-based responses.")
        
        # Fallback to rule-based responses (existing logic)
        if any(word in query_lower for word in ["hello", "hi", "hey", "greetings"]):
            response = "Hello! I'm your AI investment advisor. I can help you with stock analysis, portfolio insights, market trends, and investment strategies. What would you like to know today?"
        elif any(word in query_lower for word in ["help", "support", "assist"]):
            response = "I can help you with:\n• Stock analysis and comparisons\n• Portfolio performance insights\n• Market trend explanations\n• Investment strategy recommendations\n• Financial metric interpretations\n\nWhat specific investment topic would you like to discuss?"
        elif any(word in query_lower for word in ["risk", "safe", "conservative", "volatile"]):
            response = "Investment risk varies by asset class and individual stock characteristics. Generally:\n• Blue-chip stocks tend to be less volatile\n• Growth stocks may offer higher returns but with increased risk\n• Diversification across sectors helps manage risk\n• Consider your investment timeline and risk tolerance\n\nWould you like specific risk analysis for particular stocks?"
        elif any(word in query_lower for word in ["buy", "sell", "recommend", "should i invest"]):
            response = "I can provide analysis and insights, but I cannot provide specific buy/sell recommendations. Investment decisions should be based on your personal financial situation, goals, and risk tolerance. Consider consulting with a licensed financial advisor for personalized advice."
        elif any(word in query_lower for word in ["market", "trend", "bull", "bear"]):
            response = "Current market trends show mixed signals with technology and healthcare sectors showing resilience. Economic indicators suggest moderate growth with inflation concerns. For personalized market insights based on your portfolio, I'd need more specific information about your holdings."
        elif any(ticker in query_lower for ticker in ["aapl", "goog", "msft", "amzn", "nvda", "tsla", "meta", "googl"]):
            # Provide sample analysis for popular tickers
            ticker = next(ticker for ticker in ["aapl", "goog", "msft", "amzn", "nvda", "tsla", "meta", "googl"] if ticker in query_lower)
            if ticker == "nvda":
                response = "NVIDIA (NVDA) continues to be a leader in AI chips with strong fundamentals. The company has shown consistent revenue growth driven by increasing demand for AI computing power. However, the stock trades at premium valuations, so consider your risk tolerance before investing."
            elif ticker == "aapl":
                response = "Apple (AAPL) maintains strong market position with diverse product ecosystem. The company has steady cash flows and consistent dividend payments, making it suitable for balanced portfolios. Monitor iPhone sales cycles for timing considerations."
            else:
                response = f"Analysis for {ticker.upper()} would typically include P/E ratio, growth prospects, competitive positioning, and sector outlook. For detailed analysis, consider reviewing the company's latest quarterly earnings and forward guidance."
        else:
            # Default response for general queries – keep concise but informative
            response = (
                f"I've received your query about '{request.query}'. "
                "As an AI investment advisor, I can help you compare sectors, analyze individual stocks, "
                "and understand risk/return trade-offs. For specific buy/sell decisions, please consult "
                "with a licensed financial advisor."
            )

        # Cache rule-based response as well so repeated generic questions are fast
        ai_advice_cache.set(query_lower, response)

        return {"advice": response}
        
    except Exception as e:
        handle_database_error(e)


@ai_advice_router.post("/explain-results")
def explain_screener_results(payload: Dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Explain screener results with AI-generated insights.
    """
    from ...core.utils import handle_database_error
    
    try:
        # Extract information from payload
        query = payload.get('query', '')
        results = payload.get('results', [])
        sector_summary = payload.get('sector_summary', {})
        avg_pe = payload.get('avg_pe', 0)
        avg_peg = payload.get('avg_peg', 0)
        avg_dividend = payload.get('avg_dividend', 0)
        
        # Generate explanation based on results
        if results:
            result_count = len(results)
            explanation = f"I've analyzed your screening results with {result_count} matches. "
            
            if sector_summary:
                top_sector = max(sector_summary, key=sector_summary.get) if sector_summary else "N/A"
                explanation += f"The results are predominantly from the {top_sector} sector. "
            
            if avg_pe > 0:
                explanation += f"The average P/E ratio is {avg_pe:.2f}. "
            
            if avg_peg > 0:
                explanation += f"The average PEG ratio is {avg_peg:.2f}. "
            
            if avg_dividend > 0:
                explanation += f"The average dividend yield is {avg_dividend:.2f}%. "
                
            explanation += "These stocks meet your screening criteria and show potential for further analysis. Consider researching individual companies' fundamentals before making investment decisions."
        else:
            explanation = "No stocks matched your screening criteria. You might want to adjust your filters or broaden your search parameters."
        
        return {"explanation": explanation}
        
    except Exception as e:
        handle_database_error(e)