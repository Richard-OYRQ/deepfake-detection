# -*- coding: utf-8 -*-
"""200 条（拟合40+留出160）池化 + 5 折交叉验证：规则族 phys≥p2 ∨ (fv≥t1 ∧ prior≥p1)
的诚实上限评估。离线重放，无 API 调用。阈值仅在训练折上搜索。"""
import json
import random

rows = []
for f in (r"E:\deepfake\output_self40_fusion.json",
          r"E:\deepfake\output_self160_fusion.json"):
    rows += json.load(open(f, encoding="utf-8"))["rows"]

random.seed(42)
fakes = [r for r in rows if r["label"] == "fake"]
reals = [r for r in rows if r["label"] == "real"]
random.shuffle(fakes)
random.shuffle(reals)
K = 5
fold_fakes = [fakes[i::K] for i in range(K)]
fold_reals = [reals[i::K] for i in range(K)]


def evaluate(rs, t1, p1, p2):
    hit = miss = fp = ok = 0
    for r in rs:
        v = "伪造" if (r["phys"] >= p2 or (r["fv"] >= t1 and r["prior"] >= p1)) else "无伪造"
        if r["label"] == "fake":
            hit += (v == "伪造"); miss += (v == "无伪造")
        else:
            fp += (v == "伪造"); ok += (v == "无伪造")
    n = len(rs)
    return ((hit + ok) / n, hit - fp, hit, miss, fp)


def grid_best(train):
    best = None
    for t1 in (1, 2, 3):
        for p1 in (round(0.30 + i * 0.02, 2) for i in range(36)):
            for p2 in (round(-1.2 + i * 0.05, 2) for i in range(49)):
                m = evaluate(train, t1, p1, p2)
                if best is None or m[:3] > best[0][:3]:
                    best = (m, (t1, p1, p2))
    return best


print("===== 5 折交叉验证（200 条池化，阈值仅拟合于训练折）=====\n")
fold_hit = fold_fp = fold_acc = 0
all_test = 0
details = []
for i in range(K):
    test = fold_fakes[i] + fold_reals[i]
    train = [r for j in range(K) if j != i for r in (fold_fakes[j] + fold_reals[j])]
    (acc, diff, hit, miss, fp), (t1, p1, p2) = grid_best(train)
    m_test = evaluate(test, t1, p1, p2)
    fold_hit += m_test[2]
    fold_fp += m_test[4]
    fold_acc += m_test[0] * len(test)
    all_test += len(test)
    details.append((i + 1, t1, p1, p2, m_test))
    print(f"折{i + 1}: 训练折选出 (t1={t1}, p1={p1:.2f}, p2={p2:.2f}) | "
          f"测试折 检出{m_test[2]}/20 误报{m_test[4]}/20 正确率{m_test[0]*100:.1f}%")

n_test_fake = sum(len(fold_fakes[i]) for i in range(K))
n_test_real = sum(len(fold_reals[i]) for i in range(K))
print(f"\n5 折合计: 检出 {fold_hit}/{n_test_fake}（{fold_hit/n_test_fake*100:.1f}%） "
      f"误报 {fold_fp}/{n_test_real}（{fold_fp/n_test_real*100:.1f}%） "
      f"总正确率 {fold_acc/all_test*100:.1f}%")
print("\n对比:")
print("  拟合40自评:        检出80.0% 误报10.0% 正确率85.0%")
print("  留出160冻结复测:   检出53.8% 误报21.2% 正确率66.2%")
print("  200条5折CV诚实值:  检出%.1f%% 误报%.1f%% 正确率%.1f%%" % (
    fold_hit/n_test_fake*100, fold_fp/n_test_real*100, fold_acc/all_test*100))
