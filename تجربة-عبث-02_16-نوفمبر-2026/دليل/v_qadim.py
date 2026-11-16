#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔎 التحقّقُ المستقلُّ من سلسلةِ UP2U2B — **بلا استيرادٍ من الكيان** (مكتبةُ Python المعياريّةُ + ssh-keygen).

يُوضَعُ داخلَ حزمةِ التصديرِ ويُشغَّلُ من أيِّ جهازٍ:
    python3 tahaqquq_mustaqill.py [مجلّدُ الحزمة]     # الافتراضيُّ: مجلّدُ هذا الملفّ

ما يُعيدُ حسابَه (العقدُ المجمَّدُ في طورِ ألف، مكتوبٌ هنا نصّاً لا مستورداً):
  seal_hash = SHA256( prev_hash ‖ content_hash ‖ JSON({9 حقول} بمفاتيحَ مرتّبةٍ بلا فراغات، ensure_ascii=False) )
  الحقولُ التسعة: kind · content_hash · size · type · source_filename · witness · niyyah · stage · hijri
  حلقةُ الأصل: prev_hash = 64 صفراً.
ثمّ يتحقّقُ من ختومِ السلسلةِ وتواقيعِ الحلقاتِ بـ `ssh-keygen -Y verify` (النطاقُ up2u2b-khatm)
— متنُ الدفعةِ لا سطرُ الحلقةِ حيثُ وُقِّعتْ دفعةً — ومن ختمِ OpenTimestamps إن وُجدَ `ots`.
رمزُ الخروج: 0 سليم · 2 عطبٌ حقيقيّ · 1 حزمةٌ ناقصة.
**حدُّه:** يُثبتُ الربطَ والترتيبَ وصحّةَ التواقيعِ على المتونِ المرفقة؛ ولا يُثبتُ محتوى الخزنةِ إن لم تُرفَق.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

SEAL_FIELDS = ("kind", "content_hash", "size", "type", "source_filename",
               "witness", "niyyah", "stage", "hijri")
NAMESPACE = "up2u2b-khatm"
GENESIS = "0" * 64


def _canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _rows(p):
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _verify_sig(signers, sig_text, matn):
    ident = open(signers, encoding="utf-8").read().split()[0]
    with tempfile.NamedTemporaryFile("w", suffix=".sig", delete=False) as t:
        t.write(sig_text); sp = t.name
    try:
        v = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", signers, "-I", ident,
                            "-n", NAMESPACE, "-s", sp], input=matn, capture_output=True, text=True)
        return v.returncode == 0
    finally:
        os.unlink(sp)


def main(dalil):
    ledger = os.path.join(dalil, "ledger.jsonl")
    sijill = os.path.join(dalil, "sijill_min.jsonl")
    silsila = os.path.join(dalil, "khatm_silsila.jsonl")
    tawaqi = os.path.join(dalil, "nafadh_tawaqi.jsonl")
    signers = os.path.join(dalil, "allowed_signers")
    if not os.path.exists(ledger):
        print("⛔ لا ledger.jsonl في الحزمة"); return 1
    rows = _rows(ledger)
    atab = []
    # ① ربطُ prev_hash — تلاعبٌ دائماً إن انقطع
    prev = GENESIS
    for i, r in enumerate(rows):
        if r.get("prev_hash") != prev:
            atab.append(f"انقطاعُ ربطِ prev عندَ الفهرس {i} ({r.get('id')})")
        prev = r.get("seal_hash", "")
    ras = prev
    print(f"■ الدفتر: {len(rows)} حلقة · الرأس {ras[:16]} · كسورُ الربط: {len(atab)}")
    # ② إعادةُ حسابِ seal_hash — إن أُرفِقتْ حقولُ العقد (--kamil)
    if os.path.exists(sijill):
        recs = {r["id"]: r for r in _rows(sijill)}
        prev = GENESIS; ok = 0; sup = 0; bad = 0; ghaib = 0
        for r in rows:
            rec = recs.get(r["id"])
            if not rec:
                ghaib += 1            # حلقةٌ في الدفترِ بلا حقولِ عقد — لم تُفحَص، ولا تُعَدُّ مطابقة
            else:
                h = hashlib.sha256((prev + rec["content_hash"] + _canon({k: rec.get(k) for k in SEAL_FIELDS})).encode("utf-8")).hexdigest()
                if h == r["seal_hash"]:
                    ok += 1
                elif rec.get("superseded_by"):
                    sup += 1          # مسوّدةٌ متجاوَزةٌ — إخباريٌّ بالعقدِ المعلَن
                else:
                    bad += 1; atab.append(f"seal_hash لا يطابقُ العقدَ: {r['id']}")
            prev = r["seal_hash"]
        print(f"■ العقد: مطابقٌ {ok} · متجاوَزٌ (إخباريّ) {sup} · مخالفٌ {bad} · غيرُ مفحوص {ghaib}")
        if ghaib:
            atab.append(f"{ghaib} حلقةً في الدفترِ بلا حقولِ عقدٍ في الحزمة — لم تُفحَص")
    else:
        print("■ العقد: لم تُرفَقْ حقولُه (--rabt) — يُتحقَّقُ الربطُ والتواقيعُ فقط")
    # ③ ختومُ السلسلة
    if os.path.exists(silsila) and os.path.exists(signers):
        S = _rows(silsila); good = 0; ids = {r["id"] for r in rows}
        prev_hash_s = None
        for i, s in enumerate(S):
            if not _verify_sig(signers, s.get("توقيع", ""), s.get("payload", "")):
                atab.append(f"توقيعُ ختمِ سلسلةٍ باطل: {s.get('زمن')}"); continue
            if s.get("رأس") not in ids:
                atab.append(f"رأسُ ختمٍ ليس في الدفتر: {s.get('رأس')}")
            if str(s.get("payload", "")).startswith("SILSILA2|"):
                # صيغة 2: يحملُ هاشَ الختمِ السابق — يُعادُ حسابُه من السطرِ السابق فعلاً
                mutawaqqa = hashlib.sha256((S[i-1]["payload"] + "\n" + S[i-1]["توقيع"]).encode("utf-8")).hexdigest() if i > 0 else GENESIS
                if s.get("هاش_الختم_السابق") != mutawaqqa or s["payload"].split("|")[5] != mutawaqqa:
                    atab.append(f"ختمُ سلسلةٍ صيغة 2 لا يربطُ سابقَه: {s.get('زمن')}")
            good += 1
        akhir = S[-1] if S else None
        print(f"■ ختومُ السلسلة: {len(S)} · صحيحُ التوقيع {good}" +
              (f" · آخرُها {akhir['زمن']} على {akhir['عدد_الحلقات']} حلقة" if akhir else ""))
        if akhir and akhir.get("هاش_الرأس") != ras and akhir.get("رأس") != rows[-1]["id"]:
            print(f"  ⚠️ {len(rows) - 1 - [r['id'] for r in rows].index(akhir['رأس'])} حلقةً بعدَ آخرِ ختمٍ بلا شاهدٍ على الرأس"
                  if akhir.get("رأس") in ids else "  ⚠️ رأسُ آخرِ ختمٍ غيرُ موجود")
    else:
        print("■ ختومُ السلسلة: لم تُرفَقْ أو لا allowed_signers")
    # ④ تواقيعُ الحلقات
    if os.path.exists(tawaqi) and os.path.exists(signers):
        T = _rows(tawaqi); good = 0
        for t in T:
            matn = t.get("متن_الدفعة") or t.get("payload", "")
            if _verify_sig(signers, t.get("توقيع", ""), matn) and t.get("payload", "").split("|")[0] in matn:
                good += 1
            else:
                atab.append(f"توقيعُ حلقةٍ باطل: {t.get('id')}")
        print(f"■ تواقيعُ الحلقات: {len(T)} · صحيح {good}")
    # ⑤ OpenTimestamps إن وُجد
    ots_dir = os.path.join(dalil, "ots")
    if os.path.isdir(ots_dir):
        sijl = os.path.join(ots_dir, "khatm_zaman.jsonl")
        Z = _rows(sijl)
        ots_bin = None
        for c in ("ots", os.path.join(dalil, "..", "..", "tech", ".venv", "bin", "ots")):
            try:
                subprocess.run([c, "--version"], capture_output=True, timeout=10); ots_bin = c; break
            except Exception:
                continue
        print(f"■ الشاهدُ الزمنيُّ الخارجيّ: {len(Z)} ختماً مسجَّلاً" + ("" if ots_bin else " · (ots غيرُ مثبَّتٍ هنا — يُتحقَّقُ بأداةٍ مستقلّة)"))
        for z in Z[-3:]:
            f = os.path.join(ots_dir, os.path.basename(z.get("malaf", "")))
            if ots_bin and os.path.exists(f):
                v = subprocess.run([ots_bin, "--no-bitcoin", "verify", "-d", z["digest_ots"], f], capture_output=True, text=True, timeout=60)
                print(f"   {z['zaman']} ← {(v.stdout + v.stderr).strip().splitlines()[-1][:90] if (v.stdout+v.stderr).strip() else 'لا جواب'}")
    print("\n" + ("✅ سليم — لا عطبَ حقيقيّاً" if not atab else "⛔ أعطاب:\n  - " + "\n  - ".join(atab[:20])))
    print("الحدّ: يُثبتُ الربطَ والترتيبَ وصحّةَ التواقيعِ على المتونِ المرفقة؛ التحقّقُ الكاملُ من OTS يستلزمُ عقدةَ بتكوين أو مقارنةَ جذرِ الكتلةِ بمصدرٍ مستقلّ.")
    return 0 if not atab else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))))
