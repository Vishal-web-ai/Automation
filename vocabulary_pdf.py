from fpdf import FPDF
import os

font_dir = "D:/Automation/fonts"

# Create PDF
pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Add fonts - use Arial for English, NotoDevanagari for Hindi
pdf.add_font("NotoDevanagari", "", font_dir + "/NotoSansDevanagari-Regular.ttf")
pdf.add_font("Arial", "", "C:/Windows/Fonts/arial.ttf")

# Title
pdf.set_font("Arial", size=20)
pdf.cell(0, 15, "Vocabulary List", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.ln(10)

# Vocabulary words
words = [
    {"english": "Happy", "hindi": "खुश", "pronunciation": "Khush", "meaning": "Feeling good and pleased"},
    {"english": "House", "hindi": "घर", "pronunciation": "Ghar", "meaning": "A place where people live"},
    {"english": "Water", "hindi": "पानी", "pronunciation": "Paani", "meaning": "A clear liquid we drink"},
    {"english": "Friend", "hindi": "दोस्त", "pronunciation": "Dost", "meaning": "A person you like and trust"},
    {"english": "Book", "hindi": "किताब", "pronunciation": "Kitab", "meaning": "Pages with words that you read"},
]

for i, word in enumerate(words, 1):
    # Number and English word
    pdf.set_font("Arial", size=14)
    pdf.cell(10, 10, f"{i}.")
    pdf.cell(30, 10, word["english"])
    
    # Hindi meaning with pronunciation (on same line, inside parentheses)
    pdf.set_font("NotoDevanagari", size=14)
    hindi_text = f'{word["hindi"]}'
    pdf.cell(30, 10, hindi_text)
    
    # Pronunciation in parentheses using Arial
    pdf.set_font("Arial", size=14)
    pdf.cell(40, 10, f'({word["pronunciation"]})')
    
    pdf.ln(10)
    
    # English meaning (simple, easy to understand)
    pdf.set_font("Arial", size=12)
    pdf.cell(10, 8, "")
    pdf.cell(0, 8, f'Meaning: {word["meaning"]}', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)

# Save
output_path = "D:/Automation/vocabulary.pdf"
pdf.output(output_path)
print(f"PDF created successfully at: {output_path}")
