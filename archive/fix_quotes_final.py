with open('D:/DeepFake/generate_extras.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The previous fix replaced Unicode curly quotes with ASCII single quotes.
# This BREAKS Python strings because ASCII ' closes the string literal.
# Solution: remove ALL standalone ASCII single quotes that are NOT part of
# Python string delimiters (they were Chinese punctuation).

# Strategy: if a single-quote appears between Chinese characters (Unicode > U+2E80),
# it was originally a Chinese quote and should be removed, not replaced.

import re

# Remove single quotes that appear adjacent to CJK characters
# Pattern: CJK char followed by ' followed by CJK char
content = re.sub(r'([一-鿿])' + "'" + r'([一-鿿])', r'\1\2', content)

# Also handle ' at start/end of Chinese phrases
content = re.sub(r'([一-鿿])' + "'" + r'([，。！；：])', r'\1\2', content)
content = re.sub(r'([，。！；：])' + "'" + r'([一-鿿])', r'\1\2', content)

# Handle double quotes too
content = re.sub(r'([一-鿿])' + '"' + r'([一-鿿])', r'\1\2', content)

with open('D:/DeepFake/generate_extras.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed')
