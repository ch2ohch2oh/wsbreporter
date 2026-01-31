from google import genai
import config
import os

try:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    print("Listing available models:")
    for m in client.models.list(config={"page_size": 100}):
        print(f"- {m.name}")
        if "flash" in m.name.lower():
            print(f"  (Flash model found: {m.name})")

except Exception as e:
    print(f"Error listing models: {e}")
