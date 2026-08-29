import json
import requests
import datetime
import random

# ============== CONFIGURATION ==============
TELEGRAM_BOT_TOKEN = "REMOVED - now uses GitHub secrets"
TELEGRAM_CHAT_ID = "REMOVED - now uses GitHub secrets"
VOCAB_FILE = "D:/Automation/vocabulary-list.md"
SELECTED_FILE = "D:/Automation/selected_words.json"
# ===========================================

def load_vocabulary():
    words = []
    learned = []
    in_words = False
    in_learned = False
    
    with open(VOCAB_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "## Words":
                in_words = True
                in_learned = False
                continue
            elif line == "## Learned Words (move here after learning)":
                in_words = False
                in_learned = True
                continue
            
            if in_words and line and not line.startswith("#"):
                words.append(line)
            elif in_learned and line and not line.startswith("#"):
                learned.append(line)
    
    unlearned = [w for w in words if w not in learned]
    return unlearned

def pick_random_words(count=5):
    unlearned = load_vocabulary()
    if len(unlearned) < count:
        count = len(unlearned)
    return random.sample(unlearned, count)

def save_selected_words(words):
    data = {
        "words": words,
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "confirmed": False
    }
    with open(SELECTED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=payload)
    return response.json()

if __name__ == "__main__":
    try:
        print("Picking 5 unlearned words...")
        selected = pick_random_words(5)
        print(f"Selected: {selected}")
        
        save_selected_words(selected)
        print("Saved to selected_words.json")
        
        today = datetime.date.today().strftime("%B %d")
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%B %d")
        
        msg = f"Tomorrow's Words ({tomorrow}):\n\n"
        for i, word in enumerate(selected, 1):
            msg += f"{i}. {word}\n"
        
        msg += f"\nReply to change words:"
        msg += f"\nExample: '2:Ephemeral' to replace word 2"
        msg += f"\nOr 'ok' to confirm these words"
        
        print("Sending to Telegram...")
        result = send_telegram(msg)
        
        if result.get("ok"):
            print("Done! Preview sent.")
        else:
            print(f"Error: {result}")
            
    except Exception as e:
        print(f"Error: {e}")
