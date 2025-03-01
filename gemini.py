import google.generativeai as genai
import os
api_key = os.getenv("GEMINI_API_KEY")
print(api_key)
# genai.configure(api_key=api_key)
# for model in genai.list_models():
#     print(model.name)