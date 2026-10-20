import json, re

with open('D:/DeepFake/output/results_2026-07-05T01-05-56Z.json', encoding='utf-8') as f:
    data = json.load(f)

forged = []
genuine = []
recovered = []

for r in data['results']:
    name = r['task_name']
    c = r['content']
    anomaly = verdict = conf = '?'
    for line in c.split('\n'):
        s = line.strip()
        m = re.search(r'(\d+)\s*/\s*14', s)
        if m and '异常项统计' in s: anomaly = m.group(1)
        if '伪造类型判断' in s:
            if '无伪造' in s: verdict = '无伪造'
            elif '换脸' in s: verdict = '换脸'
            elif '面部重演' in s: verdict = '面部重演'
        m = re.search(r'(\d+)\s*/\s*100', s)
        if m and '综合置信度' in s: conf = m.group(1) + '%'

    vote = r.get('vote_result', {})
    if verdict == '换脸' or verdict == '面部重演':
        forged.append(name)
        # Check if recovered in stage 2
        if vote and len(vote) > 1:
            recovered.append(name)
    else:
        genuine.append(name)

print(f'检出换脸: {len(forged)}/100')
recovered_str = ", ".join(sorted(recovered, key=lambda x: int(x[1:]))[:20])
if len(recovered) > 20: recovered_str += "..."
print(f'  其中阶段二复检纠正: {len(recovered)} ({recovered_str})')
g_f = [n for n in genuine if n.startswith('F')]
print(f'判为无伪造: {len(genuine)}/100')
print(f'  F系列漏检: {len(g_f)}')
print(f'\n--- F1-F10 ---')
for r in data['results']:
    name = r['task_name']
    if name in ['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10']:
        c = r['content']
        vote = r.get('vote_result', {})
        for line in c.split('\n'):
            if '异常项统计' in line or '伪造类型判断' in line:
                tag = ' [复检纠正]' if len(vote) > 1 else ''
                print(f'  {name}: {line.strip()[:100]}{tag}')
