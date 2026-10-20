# Read, fix, write -- simple and direct
path = 'D:/DeepFake/generate_extras.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Strategy: replace ALL ASCII single-quote characters (0x27)
# that appear BETWEEN two CJK characters (Chinese/Japanese/Korean)
# with nothing (remove them). These were originally Chinese quotation marks.
# Do NOT touch quotes used as Python string delimiters.

import re
# Pattern: CJK-char + ' + CJK-char -> CJK-char + CJK-char (remove the quote)
text = re.sub(r'([一-鿿　-〿＀-￯])' + "'" + r'([一-鿿　-〿＀-￯])', r'\1\2', text)

# Pattern: CJK-char + ' + non-CJK but Chinese punct
text = re.sub(r'([一-鿿])' + "'" + r'([　-〿＀-￯])', r'\1\2', text)

# Pattern: Chinese punct + ' + CJK-char
text = re.sub(r'([　-〿＀-￯])' + "'" + r'([一-鿿])', r'\1\2', text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Done')
