with open('D:/DeepFake/generate_extras.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = 0
for i, line in enumerate(lines):
    orig = line
    # Check if line is inside a Python single-quoted string and contains problematic chars
    # Simple approach: just count Unicode quote chars and remove them
    for ch in ['‘', '’', '“', '”', '＇']:
        if ch in line:
            line = line.replace(ch, '')
            fixed += 1
    lines[i] = line

with open('D:/DeepFake/generate_extras.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'Fixed {fixed} lines')
