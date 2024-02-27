from dotenv import load_dotenv
import os
import google.generativeai as genai
load_dotenv()

genai.configure(api_key = os.getenv('GEMINI_API_KEY'))
print(os.environ.get('GEMINI_API_KEY'))
def gemini_response(promt, question):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content([promt, question])
    return response.text