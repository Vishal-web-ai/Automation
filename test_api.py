import json
from google import genai

client = genai.Client(api_key="REMOVED - now uses GitHub secrets")

prompt = """Give me exactly 3 interesting English words.
Return ONLY a JSON array:
[{"word": "word", "pos": "noun/verb/adj", "meaning_en": "meaning", "examples": ["ex1", "ex2"], "alternatives": ["a1", "a2", "a3"]}]
Rules: Useful words, 2 examples, 3 alternatives."""

response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
text = response.text.strip()
if text.startswith("```"):
    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
print(text)
