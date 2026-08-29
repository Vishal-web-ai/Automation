import json
import requests
import datetime
from google import genai
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ============== CONFIGURATION ==============
GEMINI_API_KEY = "REMOVED - now uses GitHub secrets"
TELEGRAM_BOT_TOKEN = "REMOVED - now uses GitHub secrets"
TELEGRAM_CHAT_ID = "REMOVED - now uses GitHub secrets"
SELECTED_FILE = "D:/Automation/selected_words.json"
VOCAB_FILE = "D:/Automation/vocabulary-list.md"
WORDS_PER_PAGE = 3
COLORS = ["orange", "teal", "purple", "pink", "blue", "green"]
COLOR_HEX = {
    "orange": "#ea580c",
    "teal": "#0d9488",
    "purple": "#9333ea",
    "pink": "#db2777",
    "blue": "#2563eb",
    "green": "#16a34a"
}
COLOR_BG = {
    "orange": "#fff7ed",
    "teal": "#f0fdfa",
    "purple": "#faf5ff",
    "pink": "#fdf2f8",
    "blue": "#eff6ff",
    "green": "#f0fdf4"
}
# ===========================================

client = genai.Client(api_key=GEMINI_API_KEY)
pdfmetrics.registerFont(TTFont('NotoDevanagari', 'D:/Automation/NotoSansDevanagari.ttf'))

def load_selected_words():
    with open(SELECTED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["words"]

def mark_words_as_learned(words):
    with open(VOCAB_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    for word in words:
        content = content.replace(f"\n{word}\n", "\n")
    
    if "## Learned Words (move here after learning)" in content:
        content = content.replace(
            "## Learned Words (move here after learning)",
            f"## Learned Words (move here after learning)\n" + "\n".join(words)
        )
    
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def get_word_details(word_list):
    words_str = ", ".join(word_list)
    
    prompt = f"""Give me details for these English words: {words_str}

    Return ONLY a JSON array:
    [
        {{
            "word": "Ambition",
            "partOfSpeech": "noun",
            "hindiMeanings": ["महत्वाकांक्षा", "इच्छा", "लक्ष्य"],
            "transliterations": ["Mahatvaakaanksha", "Iccha", "Lakshya"],
            "englishMeanings": [
                "A strong desire to achieve something",
                "The object or goal desired"
            ],
            "examples": ["His ambition drove him to succeed.", "She has the ambition to become a doctor.", "Ambition is the key to success."],
            "alternates": ["aspiration", "goal", "desire", "drive", "dream"]
        }}
    ]

    Rules:
    - hindiMeanings: List of distinct Hindi meanings, one per English meaning. Each meaning is a separate item in the array.
    - transliterations: Romanized Hindi pronunciation for each hindiMeaning, same count.
    - englishMeanings: List ONLY genuinely distinct, commonly used meanings of the word. Do NOT force multiple meanings.
      - If a word has ONE common meaning, output exactly ONE meaning.
      - If a word has TWO genuinely distinct meanings, output exactly TWO.
      - If a word has THREE genuinely distinct meanings, output exactly THREE.
      - Never target a fixed number. Let the word determine how many meanings it has.
      - Do NOT invent, stretch, or artificially split meanings.
      - Do NOT count minor variations, synonyms, or contextual nuances as separate meanings.
      - Prefer common dictionary meanings over rare, archaic, or technical meanings.
      - Before finalizing, ask for each meaning: "Is this genuinely a separate, commonly recognized meaning?" If NO, delete it.
      Example: "Elephant" → ONE meaning: "A very large mammal with a trunk, tusks, and large ears."
      Example: "Bank" → TWO meanings: "A financial institution" and "The land alongside a river."
      Example: "Bark" → TWO meanings: "The outer covering of a tree" and "The sound made by a dog."
    - Examples: 3 sentences using the word
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

def create_pdf(words, day=None):
    if day is None:
        day = datetime.date.today().day
    
    words = assign_colors(words)
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"D:/Automation/vocab_builder_{today_str}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=A4, 
                           leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=15*mm, bottomMargin=15*mm)
    
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                  fontSize=24, textColor=HexColor('#1e1b4b'),
                                  spaceAfter=5, alignment=TA_CENTER)
    
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                     fontSize=11, textColor=HexColor('#6b7280'),
                                     alignment=TA_CENTER, spaceAfter=15)
    
    word_style = ParagraphStyle('Word', parent=styles['Heading1'],
                                 fontSize=20, spaceAfter=5, spaceBefore=10)
    
    section_style = ParagraphStyle('Section', parent=styles['Normal'],
                                    fontSize=9, textColor=HexColor('#374151'),
                                    fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5)
    
    hindi_style = ParagraphStyle('Hindi', parent=styles['Normal'],
                                  fontSize=14, textColor=HexColor('#1e1b4b'),
                                  fontName='NotoDevanagari', spaceAfter=3)
    
    translit_style = ParagraphStyle('Translit', parent=styles['Normal'],
                                     fontSize=10, textColor=HexColor('#6b7280'),
                                     fontName='Helvetica-Oblique')
    
    meaning_style = ParagraphStyle('Meaning', parent=styles['Normal'],
                                    fontSize=11, textColor=HexColor('#374151'))
    
    example_style = ParagraphStyle('Example', parent=styles['Normal'],
                                    fontSize=10, textColor=HexColor('#4b5563'),
                                    leftIndent=10)
    
    alt_style = ParagraphStyle('Alt', parent=styles['Normal'],
                                fontSize=10, textColor=HexColor('#4b5563'),
                                spaceBefore=5)
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                   fontSize=10, textColor=HexColor('#9ca3af'),
                                   alignment=TA_CENTER, spaceBefore=20)
    
    story.append(Paragraph("Vocabulary Builder", title_style))
    story.append(Paragraph(f"Day {day} — {len(words)} Words with Hindi & English Meanings", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=HexColor('#e5e7eb'), spaceAfter=15))
    
    for i, word in enumerate(words):
        color = word["color"]
        hex_color = COLOR_HEX[color]
        bg_hex = COLOR_BG[color]
        
        word_custom_style = ParagraphStyle('WordCustom', parent=word_style,
                                           textColor=HexColor(hex_color))
        story.append(Paragraph(f"{word['word']} <font size=10 color='#6b7280'><i>({word['partOfSpeech']})</i></font>", word_custom_style))
        
        story.append(Paragraph("HINDI MEANING", section_style))
        hindi_meanings = word['hindiMeanings']
        transliterations = word.get('transliterations', word.get('transliteration', '').split(' / '))
        hindi_rows = []
        for j, hindi_m in enumerate(hindi_meanings):
            hindi_rows.append([Paragraph(f"{j+1}. {hindi_m}", hindi_style)])
            if j < len(transliterations):
                hindi_rows.append([Paragraph(transliterations[j], translit_style)])
        hindi_table = Table(hindi_rows, colWidths=[doc.width])
        hindi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor(bg_hex)),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(hindi_table)
        story.append(Spacer(1, 5))

        story.append(Paragraph("ENGLISH MEANING", section_style))
        for j, meaning in enumerate(word['englishMeanings']):
            story.append(Paragraph(f"{j+1}. {meaning}", meaning_style))
        
        story.append(Paragraph("EXAMPLES", section_style))
        for ex in word['examples']:
            ex_data = [[Paragraph(f"• {ex}", example_style)]]
            ex_table = Table(ex_data, colWidths=[doc.width])
            ex_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor(bg_hex)),
                ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(ex_table)
            story.append(Spacer(1, 3))
        
        alts = " | ".join(word['alternates'])
        story.append(Paragraph(f"<b>ALTERNATE WORDS:</b> {alts}", alt_style))
        
        if i < len(words) - 1:
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb'), spaceBefore=10, spaceAfter=10))
    
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=2, color=HexColor('#e5e7eb'), spaceAfter=10))
    story.append(Paragraph(f"Keep learning — Day {day + 1} coming soon!", footer_style))
    
    doc.build(story)
    return filename

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
        "text": message
    }
    response = requests.post(url, json=payload)
    return response.json()

if __name__ == "__main__":
    try:
        print("Loading selected words...")
        word_list = load_selected_words()
        print(f"Words: {word_list}")
        
        print("Getting word details from Gemini...")
        words = get_word_details(word_list)
        print(f"Got details for {len(words)} words")
        
        print("Creating PDF...")
        pdf_file = create_pdf(words)
        print(f"PDF created: {pdf_file}")
        
        print("Sending to Telegram...")
        result = send_telegram_pdf(pdf_file)
        
        if result.get("ok"):
            print("Marking words as learned...")
            mark_words_as_learned(word_list)
            
            today = datetime.date.today().strftime("%B %d, %Y")
            send_telegram_text(f"Vocabulary Builder - {today}\nYour daily words are ready!")
            print("Done! Sent to Telegram.")
        else:
            print(f"Error: {result}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
