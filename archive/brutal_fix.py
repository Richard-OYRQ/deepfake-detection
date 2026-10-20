path = 'D:/DeepFake/generate_extras.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Brutal approach: find all add_p/add_b/add_h lines and
# remove any single-quote that isn't the Python string delimiter

import re

def fix_line(match):
    line = match.group(0)
    # Keep only the structural quotes (first after 'doc, ' and last before ')')
    # Strategy: split on the pattern "doc, '" and "')" to find the real delimiters
    # Then remove all other single quotes from the content between them

    # Find the content between add_xxx(doc, ' and the final ')
    # This is the string content. Remove quotes from it.

    # Simple approach: find all ' that are within Chinese text context
    # and remove them. But keep Python string delimiters.

    # Use a simple heuristic: any ' that has another ' within 5 chars
    # on either side is likely part of Python delimiter. Keep those.
    # Any isolated ' surrounded by text is a Chinese quote - remove.

    chars = list(line)
    quotes = [i for i, c in enumerate(chars) if c == "'"]
    to_remove = set()

    for i, pos in enumerate(quotes):
        # Check if this quote is likely a Python delimiter
        left = line[max(0,pos-15):pos]
        right = line[pos+1:min(len(line),pos+15)]

        # Opening delimiter: preceded by 'doc, ' or ', '
        is_opener = left.rstrip().endswith('doc,') or left.rstrip().endswith(',')
        # Closing delimiter: followed by ')'
        is_closer = right.lstrip().startswith(')')

        if not (is_opener or is_closer):
            # Check if adjacent to non-ASCII (Chinese text) on either side
            left_ch = ord(chars[pos-1]) if pos > 0 else 0
            right_ch = ord(chars[pos+1]) if pos < len(chars)-1 else 0
            if left_ch > 127 or right_ch > 127:
                to_remove.add(pos)

    for pos in sorted(to_remove, reverse=True):
        del chars[pos]

    return ''.join(chars)

# Apply to all add_xxx function lines
text = re.sub(r"^\s*(add_[a-z]+)\(.*$", fix_line, text, flags=re.MULTILINE)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Brutal fix done')
