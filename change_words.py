import json
import sys

SELECTED_FILE = "D:/Automation/selected_words.json"

def load_selected():
    with open(SELECTED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_selected(data):
    with open(SELECTED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def update_word(position, new_word):
    data = load_selected()
    words = data["words"]
    
    if position < 1 or position > len(words):
        return False, f"Invalid position. Choose 1-{len(words)}"
    
    old_word = words[position - 1]
    words[position - 1] = new_word
    data["words"] = words
    data["confirmed"] = False
    
    save_selected(data)
    return True, f"Changed '{old_word}' to '{new_word}'"

def confirm_words():
    data = load_selected()
    data["confirmed"] = True
    save_selected(data)
    return True, "Words confirmed for tomorrow's PDF!"

def show_current():
    data = load_selected()
    words = data["words"]
    msg = "Current selection:\n"
    for i, w in enumerate(words, 1):
        msg += f"{i}. {w}\n"
    return True, msg

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python change_words.py <command>")
        print("Commands:")
        print("  show              - Show current words")
        print("  update <pos> <word> - Replace word at position")
        print("  confirm           - Confirm words for PDF")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "show":
        success, msg = show_current()
        print(msg)
    
    elif command == "update" and len(sys.argv) == 4:
        pos = int(sys.argv[2])
        new_word = sys.argv[3]
        success, msg = update_word(pos, new_word)
        print(msg)
    
    elif command == "confirm":
        success, msg = confirm_words()
        print(msg)
    
    else:
        print("Invalid command. Use: show, update <pos> <word>, or confirm")
