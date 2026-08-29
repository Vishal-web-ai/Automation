import json
import requests
import datetime
from google import genai
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

# ============== CONFIGURATION ==============
GEMINI_API_KEY = "REMOVED - now uses GitHub secrets"
TELEGRAM_BOT_TOKEN = "REMOVED - now uses GitHub secrets"
TELEGRAM_CHAT_ID = "REMOVED - now uses GitHub secrets"
WORDS_PER_PAGE = 3
COLORS = ["orange", "teal", "purple", "pink", "blue", "green"]
# ===========================================

client = genai.Client(api_key=GEMINI_API_KEY)

def get_daily_words(count=5):
    today = datetime.date.today().strftime("%B %d, %Y")
    
    prompt = f"""Give me exactly {count} interesting English words I should learn today ({today}).
    
    Return ONLY a JSON array:
    [
        {{
            "word": "Ambition",
            "partOfSpeech": "noun",
            "hindiMeaning": "महत्वाकांक्षा / इच्छा / लक्ष्य",
            "transliteration": "Mahatvaakaanksha / Iccha / Lakshya",
            "englishMeaning": "A strong desire to achieve something; a goal or aspiration",
            "examples": ["His ambition drove him to succeed.", "She has the ambition to become a doctor.", "Ambition is the key to success."],
            "alternates": ["aspiration", "goal", "desire", "drive", "dream"]
        }}
    ]
    
    Rules:
    - Useful, interesting words not too common
    - Hindi meaning: give 2-3 Hindi synonyms separated by " / "
    - Transliteration: Romanized Hindi pronunciation in italics
    - English meaning: one-line clear definition
    - Examples: 3 sentences using the word in different contexts
    - Alternates: 5 synonyms
    - Return ONLY valid JSON array, no markdown"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    
    return json.loads(text)

def assign_colors(words):
    for i, word in enumerate(words):
        word["color"] = COLORS[i % len(COLORS)]
    return words

def chunk_into_pages(words, per_page):
    return [words[i:i + per_page] for i in range(0, len(words), per_page)]

def create_pdf(words, day=None):
    if day is None:
        day = datetime.date.today().day
    
    words = assign_colors(words)
    pages = chunk_into_pages(words, WORDS_PER_PAGE)
    
    env = Environment(loader=FileSystemLoader("D:/Automation"))
    template = env.get_template("vocab_template.html")
    
    html_content = template.render(
        pages=pages,
        day=day,
        page_words_count=len(words)
    )
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"D:/Automation/vocab_builder_{today_str}.pdf"
    
    with open(filename, "wb") as out_file:
        pisa_status = pisa.CreatePDF(html_content, dest=out_file)
    
    return filename, html_content

def send_telegram_pdf(filepath):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    with open(filepath, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        response = requests.post(url, files=files, data=data)
    return response.json()

def send_telegram_text(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

if __name__ == "__main__":
    try:
        print("Generating your daily words...")
        words = get_daily_words(5)
        print(f"Got {len(words)} words from Gemini")
        
        print("Creating PDF...")
        pdf_file, html_content = create_pdf(words)
        print(f"PDF created: {pdf_file}")
        
        # Save HTML for preview
        with open("D:/Automation/vocab_preview.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("HTML preview saved: vocab_preview.html")
        
        print("Sending PDF to Telegram...")
        result = send_telegram_pdf(pdf_file)
        
        if result.get("ok"):
            today = datetime.date.today().strftime("%B %d, %Y")
            send_telegram_text(f"Vocabulary Builder - {today}\n5 new words for you!")
            print("Done! PDF sent to your Telegram.")
        else:
            print(f"Telegram error: {result}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
