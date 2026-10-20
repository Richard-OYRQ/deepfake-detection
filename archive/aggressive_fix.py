path = 'D:/DeepFake/generate_extras.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = 0
new_lines = []
for line in lines:
    if any(fn in line for fn in ['add_p(', 'add_b(', 'add_h(', 'add_tip(', 'add_code(']) \
       and any(ord(c) > 127 for c in line):
        # Find positions of all single-quote chars
        quote_positions = [i for i, c in enumerate(line) if c == "'"]
        if len(quote_positions) >= 2:
            # First quote is Python string opener, last is closer. Keep them.
            # Remove all quotes in between that are adjacent to non-ASCII chars
            chars = list(line)
            for pos in quote_positions[1:-1]:  # skip first and last
                left_ok = pos > 0 and ord(chars[pos-1]) > 127
                right_ok = pos < len(chars)-1 and ord(chars[pos+1]) > 127
                if left_ok or right_ok:
                    chars[pos] = ''
                    fixed += 1
            line = ''.join(chars)

    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'Removed {fixed} problematic quotes')
