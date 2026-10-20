import re

with open('D:/DeepFake/generate_extras.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all single quote-like chars inside Python string literals with safe alternatives
# Target: left/right single quotation marks (Unicode), ideographic comma, etc.
replacements = {
    '‘': "'",  # left single quote
    '’': "'",  # right single quote
    '“': '"',  # left double quote
    '”': '"',  # right double quote
    '＇': "'",  # fullwidth apostrophe
}

for old, new in replacements.items():
    count = content.count(old)
    if count > 0:
        content = content.replace(old, new)
        print(f'Replaced {count} of U+{ord(old):04X}')

with open('D:/DeepFake/generate_extras.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
