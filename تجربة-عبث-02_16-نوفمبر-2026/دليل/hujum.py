#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار العبث لعرض «سيف»: يبني سبع نسخ معبوث بها من حزمة تحقق، ولا يمس الأصل.

    python3 -B hujum.py <مجلد الحزمة الأساس>

النسخ تُكتب بجوار الأساس. القيد المهاجَم: الفهرس 1000 (والفهارس تبدأ من 0).
"""
import hashlib, json, os, shutil, sys

base = os.path.abspath(sys.argv[1]); IDX = 1000


def nuskha(ism):
    d = os.path.join(os.path.dirname(base), ism)
    shutil.rmtree(d, ignore_errors=True); shutil.copytree(base, d); return d


def qra(d):
    return [json.loads(l) for l in open(os.path.join(d, "ledger.jsonl"), encoding="utf-8") if l.strip()]


def ktb(d, R):
    open(os.path.join(d, "ledger.jsonl"), "w", encoding="utf-8").write(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in R))


def qalb(h):
    return ("0" if h[0] != "0" else "1") + h[1:]


# 1أ: حرف واحد في بصمة المحتوى للقيد 1000
d = nuskha("a1_content"); R = qra(d); R[IDX]["content_hash"] = qalb(R[IDX]["content_hash"]); ktb(d, R)
# 1ب: حرف واحد في ختم القيد 1000
d = nuskha("a1_seal"); R = qra(d); R[IDX]["seal_hash"] = qalb(R[IDX]["seal_hash"]); ktb(d, R)
# 2: تزوير بصمة المحتوى للقيد 1000 ثم إعادة حساب كل ختم بعده حتى يتصل الربط
d = nuskha("a2_forge"); R = qra(d)
R[IDX]["content_hash"] = hashlib.sha256(b"forged").hexdigest()
for i in range(IDX, len(R)):
    R[i]["prev_hash"] = R[i - 1]["seal_hash"]
    R[i]["seal_hash"] = hashlib.sha256((R[i]["prev_hash"] + R[i]["content_hash"]).encode()).hexdigest()
ktb(d, R)
# 3: حذف آخر 10 قيود (كلها بعد آخر ختم سلسلة)
d = nuskha("a3_batr"); R = qra(d); ktb(d, R[:-10])
# 4: حرف واحد في بصمة محتوى القيد الذي لا توقيع له
R = qra(base)
T = {json.loads(l)["id"] for l in open(os.path.join(base, "nafadh_tawaqi.jsonl"), encoding="utf-8") if l.strip()}
bila = [i for i, r in enumerate(R) if r["id"] not in T]
if bila:
    d = nuskha("a4_bila_tawqi"); R[bila[0]]["content_hash"] = qalb(R[bila[0]]["content_hash"]); ktb(d, R)
# 5: حذف آخر 40 قيدًا (يدخل الحذف في ما ختمته السلسلة)
d = nuskha("a5_batr40")
L = [l for l in open(os.path.join(base, "ledger.jsonl"), encoding="utf-8") if l.strip()]
open(os.path.join(d, "ledger.jsonl"), "w", encoding="utf-8").write("".join(L[:-40]))
# 6: الرجوع إلى حال أقدم — حذف آخر ختم سلسلة وكل قيد بعد رأس الختم الذي قبله
d = nuskha("a6_ruju")
KH = [l for l in open(os.path.join(base, "khatm_silsila.jsonl"), encoding="utf-8") if l.strip()]
ras_sabiq = json.loads(KH[-2])["رأس"]
ids = [json.loads(l)["id"] for l in L]
open(os.path.join(d, "khatm_silsila.jsonl"), "w", encoding="utf-8").write("".join(KH[:-1]))
open(os.path.join(d, "ledger.jsonl"), "w", encoding="utf-8").write("".join(L[:ids.index(ras_sabiq) + 1]))

R = qra(base)
print("القيد 1000:", R[IDX]["id"], "| عدد القيود:", len(R), "| بلا توقيع:", [(i, R[i]["id"]) for i in bila])
