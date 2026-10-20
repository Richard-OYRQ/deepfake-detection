"""Extract detection summary from latest results JSON."""
import json, re, glob, os

files = glob.glob("output/results_*.json")
latest = max(files, key=os.path.getmtime)

with open(latest, "r", encoding="utf-8") as f:
    data = json.load(f)

lines = []
lines.append("")
lines.append("=" * 95)
lines.append(f"  DeepFake Detection Results -- {latest}")
lines.append("=" * 95)
lines.append(f"{'Video':<6s} {'Anomaly':<8s} {'Fake Type':<20s} {'Conf':<8s} {'Tokens':>7s} {'Time':>6s}  Verdict")
lines.append("-" * 95)

fake = 0
real = 0
unknown = 0

for r in data["results"]:
    name = r["task_name"]
    content = r.get("content", "")
    tokens = r.get("usage", {}).get("total_tokens", 0)
    elapsed = r.get("elapsed_seconds", 0)

    m = re.search(r"异常项统计[：:]\**\s*(\d+)\s*/\s*(\d+)", content)
    anomaly = f" {m.group(1)}/{m.group(2)} " if m else "  ?/?   "

    t = re.search(r"伪造类型判断[：:]\**\s*(.+?)(?:\n|$)", content)
    fake_type = t.group(1).strip().replace("*", "").replace("**", "").strip() if t else "?"

    c = re.search(r"综合置信度[：:]\**\s*(\d+)\s*/\s*(\d+)", content)
    conf = f" {c.group(1)}/{c.group(2)} " if c else "  ?/?  "

    # conclusion
    conclusion = ""
    for i, line in enumerate(content.split("\n")):
        if "最终结论" in line:
            for j in range(i+1, min(i+5, len(content.split("\n")))):
                s = content.split("\n")[j].strip()
                if s and not s.startswith("#") and not s.startswith("（") and len(s) > 5:
                    conclusion = s[:120]
                    break
            break

    # classify -- check "无伪造" FIRST before "伪造"
    if fake_type == "无伪造":
        real += 1
        tag = "[REAL]"
    elif any(kw in fake_type for kw in ["换脸", "篡改", "重演", "全生成"]):
        fake += 1
        tag = "[FAKE]"
    elif "伪造" in fake_type:
        fake += 1
        tag = "[FAKE]"
    else:
        # infer from conclusion
        if any(kw in conclusion for kw in ["已被", "被AI换脸", "换脸技术篡改", "深度伪造"]):
            fake += 1
            tag = "[FAKE]"
        elif any(kw in conclusion for kw in ["未被AI", "未被换脸", "未发现AI", "真实人物", "真实录制", "真实拍摄", "无伪造"]):
            real += 1
            tag = "[REAL]"
        else:
            unknown += 1
            tag = "[???]"

    lines.append(f"{name:<6s} {anomaly:<8s} {fake_type:<20s} {conf:<8s} {tokens:>7d} {elapsed:>5.0f}s  {tag}")
    if conclusion:
        lines.append(f"       |-- {conclusion}")

lines.append("-" * 95)
lines.append(f"  TOTAL: [FAKE]={fake}  [REAL]={real}  [???]={unknown}  Grand Total={fake+real+unknown}")
lines.append("=" * 95)
lines.append("")

out = "\n".join(lines)
with open("output/_detection_summary.txt", "w", encoding="utf-8-sig") as f:
    f.write(out)
print("Summary written to output/_detection_summary.txt")
print(f"FAKE={fake}, REAL={real}, UNKNOWN={unknown}")
