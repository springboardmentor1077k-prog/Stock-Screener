from google import genai
from config import GEMINI_API_KEY
from llm_prompt import STRICT_PROMPT

client = genai.Client(api_key=GEMINI_API_KEY)

def call_llm(user_query: str):
    """
    Calls Gemini and returns JSON response text
    """

    prompt = STRICT_PROMPT + "\n" + user_query

    response = client.models.generate_content(
        model="models/gemini-flash-lite-latest",
        contents=prompt
    )

    return response.text
