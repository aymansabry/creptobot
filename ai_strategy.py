# ai_strategy.py
import requests
import json

# Placeholder for your generative AI logic
class AIStrategy:
    def __init__(self, api_key=None):
        self.api_key = api_key or ""
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={self.api_key}"
    
    def analyze(self, market_data):
        prompt = f"Analyze the following market data to provide a brief, high-level overview of market status. Use simple terms and provide a concise summary. Here is the data: {market_data}"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
            result = response.json()
            
            if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "Analysis failed: No valid response from AI."
        except requests.exceptions.RequestException as e:
            return f"Analysis failed: Request error - {e}"
        except json.JSONDecodeError:
            return "Analysis failed: Could not decode JSON response from AI."
        except Exception as e:
            return f"An unexpected error occurred: {e}"