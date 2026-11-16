#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔴 عبثُ المحكّم — حرفٌ واحدٌ في الحلقةِ التي يختارُها المحكّم، والكسرُ الجديدُ بالأحمر.

    python3 -B abath_muhakkim.py <مجلّدُ الحزمة> <رقمُ السطرِ أو المعرّف> [--fihris] [--haql prev_hash|seal_hash|content_hash]
                                 [--mutahaqqiq <مسار>] [--lawn|--bila-lawn] [--bila-qalb]
    python3 -B abath_muhakkim.py --dukhan

- الرقمُ **سطرٌ من 1** كما يختارُه المحكّمُ بـ `sed -n Np ledger.jsonl`؛ ومع `--fihris` **فهرسٌ من 0** كما يطبعُه المتحقّق. تُطبَعُ الصيغتان.
- لا يمسُّ الحزمةَ الأصل: ينسخُها إلى `<الحزمة>_muhakkim_<فهرس>` بجوارِها، ويقلبُ **بايتًا واحدًا في المكانِ** على السطرِ الخامِ
  (لا إعادةَ كتابةِ JSON)، ثمّ يشغّلُ متحقّقَ الحزمةِ نفسَه على الأصلِ ثمّ النسخة، ويطبعُ الأسطرَ التي ظهرتْ في النسخةِ ولم تكنْ في الأصلِ **بالأحمر**.
- الحقلُ الافتراضيُّ `prev_hash` فيقعُ الكسرُ على حلقةِ المحكّمِ نفسِها («انقطاعُ ربطِ prev عندَ الفهرس N»).
  حدودٌ معلنة يُحذَّرُ منها: ختمُ آخرِ حلقةٍ بعدَ آخرِ رأسٍ مختوم، وبصمةُ محتوى حلقةٍ بلا توقيع — لا يمسكُهما المتحقّق.
- `--bila-qalb` ضابطٌ سالب: نسخٌ بلا قلبٍ فيجبُ ألّا يظهرَ سطرٌ جديد. اللونُ تلقائيٌّ على الطرفيّة؛ `--lawn` يفرضُه و`--bila-lawn` يطفئُه.
رمزُ الخروج: 0 ظهرَ كسرٌ جديد · 3 لم يظهرْ سطرٌ جديد (حدٌّ معلن) · 1 رفض (رقمٌ خارجَ المدى / معرّفٌ غائب / حقلٌ مجهول / حزمةٌ ناقصة / الأصلُ تغيّر).
الحدّ: يرى ما يطبعُه المتحقّقُ فقط (أوّلُ 20 عطبًا)، ولا يُثبتُ سلامةَ ما لم يُقلَب. مكتبةُ Python المعياريّةُ فقط.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter

HUQUL = ("prev_hash", "seal_hash", "content_hash")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _lawn(on):
    return (lambda s, c: f"\033[{c}m{s}\033[0m") if on else (lambda s, c: s)


def _farq(qadim, hadith):
    """الأسطرُ في hadith التي ليستْ في qadim (بعدِّ التكرار، بترتيبِها)."""
    c = Counter(qadim.splitlines()); out = []
    for l in hadith.splitlines():
        if c[l] > 0:
            c[l] -= 1
        else:
            out.append(l)
    return out


def _shaghghil(mutahaqqiq, d):
    t0 = time.time()
    p = subprocess.run([sys.executable, "-B", mutahaqqiq, d], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr, time.time() - t0


def ijra(huzma, raqm, fihris=False, haql="prev_hash", mutahaqqiq=None, lawn=True, bila_qalb=False, out=print):
    L = _lawn(lawn)
    huzma = os.path.abspath(huzma.rstrip("/"))
    ledger = os.path.join(huzma, "ledger.jsonl")
    mutahaqqiq = mutahaqqiq or os.path.join(huzma, "tahaqquq_mustaqill.py")
    if not os.path.isfile(ledger) or not os.path.isfile(mutahaqqiq):
        out("⛔ حزمةٌ ناقصة: يلزمُ ledger.jsonl وtahaqquq_mustaqill.py (أو --mutahaqqiq)"); return 1, []
    if haql not in HUQUL:
        out(f"⛔ الحقلُ {haql} ليس من {HUQUL}"); return 1, []
    sutur = open(ledger, encoding="utf-8").read().splitlines(keepends=True)
    mawadi = [i for i, l in enumerate(sutur) if l.strip()]
    rows = [json.loads(sutur[i]) for i in mawadi]
    ids = [r.get("id") for r in rows]
    n = len(rows)
    if raqm.isdigit():
        idx = int(raqm) if fihris else int(raqm) - 1
        if not (0 <= idx < n):
            out(f"⛔ الرقمُ خارجَ المدى: الدفترُ {n} حلقة (السطور 1..{n} · الفهارس 0..{n - 1})"); return 1, []
    else:
        if raqm not in ids:
            out(f"⛔ لا حلقةَ بالمعرّف {raqm}"); return 1, []
        idx = ids.index(raqm)
    r = rows[idx]
    out(f"■ السطر {idx + 1} = الفهرس {idx} · {r.get('id')}")
    out(f"  ختمُها {str(r.get('seal_hash', ''))[:12]}… · بصمتُها {str(r.get('content_hash', ''))[:12]}… · سابقُها {str(r.get('prev_hash', ''))[:12]}…")
    # تحذيراتُ الحدِّ المعلن
    silsila = os.path.join(huzma, "khatm_silsila.jsonl")
    if haql == "seal_hash" and idx == n - 1:
        akhir = -1
        if os.path.isfile(silsila):
            S = [json.loads(l) for l in open(silsila, encoding="utf-8") if l.strip()]
            ras = S[-1].get("رأس") if S else None
            akhir = ids.index(ras) if ras in ids else -1
        if idx > akhir:
            out("⚠️ آخرُ حلقةٍ وبعدَ آخرِ رأسٍ مختوم: قلبُ ختمِها لا يمسكُه شيء (حدٌّ معلن — يُغلَقُ بختمِ الرأس)")
    if haql == "content_hash":
        tawaqi = os.path.join(huzma, "nafadh_tawaqi.jsonl")
        muwaqqa = {json.loads(l).get("id") for l in open(tawaqi, encoding="utf-8") if l.strip()} if os.path.isfile(tawaqi) else set()
        if r.get("id") not in muwaqqa:
            out("⚠️ حلقةٌ بلا توقيعٍ في الحزمة: قلبُ بصمةِ محتواها لا يمسكُه المتحقّق (حدٌّ معلن — يُغلَقُ بالتوقيع)")
    nuskha = f"{huzma}_muhakkim_{idx}"
    shutil.rmtree(nuskha, ignore_errors=True); shutil.copytree(huzma, nuskha)
    qabl = _sha(ledger)
    if bila_qalb:
        out("■ ضابط: نسخةٌ بلا قلب")
    else:
        satr = sutur[mawadi[idx]]
        m = re.search(r'("%s"\s*:\s*")([0-9a-f])' % haql, satr)
        if not m:
            out(f"⛔ لم أجدِ الحقلَ {haql} في سطرِ الحلقة"); shutil.rmtree(nuskha, ignore_errors=True); return 1, []
        h = m.group(2); jadid = "0" if h != "0" else "1"
        sutur2 = list(sutur); sutur2[mawadi[idx]] = satr[:m.start(2)] + jadid + satr[m.end(2):]
        open(os.path.join(nuskha, "ledger.jsonl"), "w", encoding="utf-8").write("".join(sutur2))
        a = open(ledger, "rb").read(); b = open(os.path.join(nuskha, "ledger.jsonl"), "rb").read()
        mukhtalif = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
        out(f"■ قُلِبَ حرفٌ واحدٌ في {haql}: {h} ⟵ {jadid} · البايتاتُ المختلفةُ بينَ الدفترَين: {mukhtalif}")
        if mukhtalif != 1:
            out("⛔ ليس بايتًا واحدًا — أوقف"); return 1, []
    rc0, o0, t0 = _shaghghil(mutahaqqiq, huzma)
    rc1, o1, t1 = _shaghghil(mutahaqqiq, nuskha)
    if _sha(ledger) != qabl:
        out("⛔ دفترُ الأصلِ تغيّرَ أثناءَ التشغيل — النتيجةُ باطلة"); return 1, []
    out(f"■ الأصل : رمزُ الخروج {rc0} · {t0:.1f}s · {os.path.basename(huzma)}")
    out(f"■ النسخة: رمزُ الخروج {rc1} · {t1:.1f}s · {os.path.basename(nuskha)}")
    jadid_s = _farq(o0, o1); zail = _farq(o1, o0)
    for l in zail:
        out("  " + L("− " + l, "32"))
    for l in jadid_s:
        out("  " + L("+ " + l, "31"))
    if jadid_s:
        out(L(f"⛔ {len(jadid_s)} سطرٍ جديد — حرفٌ واحدٌ كشفَه المتحقّق", "31")); return 0, jadid_s
    out(L("⚠️ لا سطرَ جديد — حدٌّ معلن: ما قُلِبَ لا يحرسُه هذا المتحقّق", "33")); return 3, []


def _dukhan():
    n = ok = 0

    def t(w, c):
        nonlocal n, ok
        n += 1; ok += bool(c); print(("  ✅ " if c else "  ❌ ") + w)
    tmp = tempfile.mkdtemp(prefix="muhakkim_dukhan_")
    try:
        huzma = os.path.join(tmp, "mini"); os.makedirs(huzma)
        prev = "0" * 64; L = []
        for i in range(5):
            ch = hashlib.sha256(f"muhtawa-{i}".encode()).hexdigest()
            seal = hashlib.sha256((prev + ch).encode()).hexdigest()
            L.append(json.dumps({"content_hash": ch, "id": f"r{i}", "prev_hash": prev, "seal_hash": seal}, separators=(",", ":")) + "\n")
            prev = seal
        open(os.path.join(huzma, "ledger.jsonl"), "w").write("".join(L))
        mut = os.path.join(ROOT, "tech", "tahaqquq_mustaqill.py")
        t("المتحقّقُ المستقلُّ موجودٌ في tech/", os.path.isfile(mut))
        shutil.copy(mut, os.path.join(huzma, "tahaqquq_mustaqill.py"))
        q = _sha(os.path.join(huzma, "ledger.jsonl"))
        sakit = lambda *a, **k: None  # noqa: E731
        rc, j = ijra(huzma, "3", lawn=False, out=sakit)
        t("قلبُ prev_hash للسطر 3 ⟵ رمز 0 وسطرٌ جديدٌ فيه «عندَ الفهرس 2»", rc == 0 and any("عندَ الفهرس 2" in l for l in j))
        rc, j = ijra(huzma, "3", lawn=False, bila_qalb=True, out=sakit)
        t("⛔ سالب: نسخةٌ بلا قلبٍ ⟵ 0 أسطرٍ جديدةٍ ورمز 3", rc == 3 and j == [])
        rc, _ = ijra(huzma, "99999", lawn=False, out=sakit)
        t("⛔ سالب: رقمٌ خارجَ المدى يُرفَض (رمز 1)", rc == 1)
        rc, _ = ijra(huzma, "la-wujud", lawn=False, out=sakit)
        t("⛔ سالب: معرّفٌ غائبٌ يُرفَض (رمز 1)", rc == 1)
        rc, _ = ijra(huzma, "2", lawn=False, haql="la", out=sakit)
        t("⛔ سالب: حقلٌ مجهولٌ يُرفَض (رمز 1)", rc == 1)
        t("⛔ سالب: دفترُ الأصلِ لم يتغيّرْ بعدَ خمسِ محاولات", _sha(os.path.join(huzma, "ledger.jsonl")) == q)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n🔥 دخانُ عبثِ المحكّم: {ok}/{n}")
    return 0 if ok == n else 2


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--dukhan" in a:
        sys.exit(_dukhan())

    def _opt(name, default=None):
        if name in a:
            i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
        return default

    def _flag(name):
        if name in a:
            a.remove(name); return True
        return False
    haql = _opt("--haql", "prev_hash"); mut = _opt("--mutahaqqiq")
    fih = _flag("--fihris"); force = _flag("--lawn"); off = _flag("--bila-lawn"); bq = _flag("--bila-qalb")
    lawn = (force or sys.stdout.isatty()) and not off
    if len(a) != 2:
        print(__doc__); sys.exit(1)
    rc, _ = ijra(a[0], a[1], fihris=fih, haql=haql, mutahaqqiq=mut, lawn=lawn, bila_qalb=bq)
    sys.exit(rc)
