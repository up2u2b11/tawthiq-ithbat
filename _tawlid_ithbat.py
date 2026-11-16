#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔳 مولّدُ إثباتِ التجارب — نسخةُ دليلٍ بايتيّة + بيانُ بصماتٍ + رمزُ QR لكلِّ تجربة (حتميٌّ · صفرُ توكن).

    python3 -B توثيق/_tawlid_ithbat.py            # يولّدُ لكلِّ تجربةٍ في مصدر.json: دليل/ · MANIFEST.sha256 · qr.png · qr.svg · بصمة-الاثبات.txt
    python3 -B توثيق/_tawlid_ithbat.py --tahaqquq # يعيدُ حسابَ كلِّ بصمةٍ ويقارنُ (رمزُ خروجٍ 2 عندَ أيِّ فرق)
    python3 -B توثيق/_tawlid_ithbat.py --dukhan   # دخانٌ بضوابطَ سالبة
    python3 -B توثيق/_tawlid_ithbat.py --miraa    # يبني نسخةَ المرآةِ العلنيّةِ في export/ (محتوى توثيق/ وحدَه) ويطبعُ أوامرَ النشرِ لطرفيّةِ 306

- `مصدر.json`: `asl` = قاعدةُ الرابطِ الذي يحملُه QR، و`tajarib` = لكلِّ تجربةٍ مجلّدُها ومصدرُ دليلِها وقائمةُ الملفّاتِ المسموحِ نشرُها
  (`"*"` = كلُّ ملفّاتِ المصدر). **ما ليس في القائمةِ لا يُنسَخ** — هذا هو حدُّ السرّيّة، مكتوبٌ لا مضمَر.
- `دليل/` نسخٌ بايتيّةٌ من المصدر؛ `MANIFEST.sha256` يشملُ `اثبات.md` و`دليل/*` بصيغةِ `shasum -a 256 -c`.
- رمزُ QR يحملُ `asl/<مجلّد>/اثبات.md` (الحروفُ العربيّةُ مرمَّزةً)؛ وبصمةُ `اثبات.md` تُكتَبُ في `بصمة-الاثبات.txt` لتُطبَعَ بجوارِ الرمز.
- المكتبة: `qrcode` إن وُجدتْ (PNG + SVG)، وإلّا مولّدُ البيتِ `tech/up2b_code._qr_png` (CoreImage، PNG فقط).
- `MANIFEST.sha256` العلويُّ في جذرِ المجلّدِ يشملُ كلَّ ملفٍّ (ومنها الحزمةُ المقيسة `حزمة-*`) **إلّا PDF** (مخرجُ الطباعةِ يتغيّرُ بايتًا مع كلِّ طباعة؛ بصمةُ الـmd هي الحكم).
- `--miraa`: ينسخُ محتوى توثيق/ إلى `export/<miraa.wijha>` ويتحقّقُ من البيانِ هناك ويطبعُ أوامرَ `git`/`gh` — **ولا ينشرُ شيئًا**؛ النشرُ بيدِ 306.
الحدّ: لا يتحقّقُ من فتحِ الرابط؛ يُثبتُ أنّ الملفّاتِ هي هي، لا أنّها منشورة.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MASDAR = os.path.join(HERE, "مصدر.json")


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _qr(url, png, svg):
    try:
        import qrcode
        import qrcode.image.svg
        q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2, box_size=8)
        q.add_data(url); q.make(fit=True)
        q.make_image().save(png)
        qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2,
                    error_correction=qrcode.constants.ERROR_CORRECT_M).save(svg)
        return "qrcode"
    except ImportError:
        sys.path.insert(0, os.path.join(ROOT, "tech"))
        import up2b_code
        ok = up2b_code._qr_png(url, png, "M")
        if os.path.exists(svg):
            os.remove(svg)
        return "CoreImage" if ok else None


def _rabt(asl, mujallad):
    return asl.rstrip("/") + "/" + quote(mujallad, safe="") + "/" + quote("اثبات.md", safe="")


def _malaffat(cfg, src):
    m = cfg.get("malaffat", "*")
    if m == "*":
        return sorted(f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f)) and not f.startswith("."))
    return list(m)


def tawlid(masdar=MASDAR, out=print):
    d = json.load(open(masdar, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(masdar))
    natija = []
    for cfg in d["tajarib"]:
        tj = os.path.join(base, cfg["mujallad"]); src = os.path.join(os.path.dirname(base), cfg["masdar"]) if not os.path.isabs(cfg["masdar"]) else cfg["masdar"]
        os.makedirs(tj, exist_ok=True)
        ithbat = os.path.join(tj, "اثبات.md")
        if not os.path.isfile(ithbat):
            out(f"⛔ {cfg['mujallad']}: لا اثبات.md — يُكتَبُ بيدٍ قبلَ التوليد"); return 1
        dalil = os.path.join(tj, "دليل"); os.makedirs(dalil, exist_ok=True)
        files = _malaffat(cfg, src); mansukh = 0
        for f in files:
            s = os.path.join(src, f)
            if not os.path.isfile(s):
                out(f"⛔ {cfg['mujallad']}: ملفٌّ في القائمةِ غائبٌ عن المصدر: {f}"); return 1
            shutil.copyfile(s, os.path.join(dalil, f)); mansukh += 1
        # ما في دليل/ وليس في القائمة يُحذَفُ — حتى لا يتسرّبَ ملفٌّ قديم
        for f in os.listdir(dalil):
            if f not in files:
                os.remove(os.path.join(dalil, f))
        rows = [f"{_sha(ithbat)}  اثبات.md"] + [f"{_sha(os.path.join(dalil, f))}  دليل/{f}" for f in files]
        open(os.path.join(tj, "MANIFEST.sha256"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
        open(os.path.join(tj, "بصمة-الاثبات.txt"), "w", encoding="utf-8").write(
            f"{_sha(ithbat)}  اثبات.md\n{_rabt(d['asl'], cfg['mujallad'])}\n")
        lib = _qr(_rabt(d["asl"], cfg["mujallad"]), os.path.join(tj, "qr.png"), os.path.join(tj, "qr.svg"))
        if not lib:
            out(f"⛔ {cfg['mujallad']}: تعذّرَ توليدُ QR"); return 1
        out(f"✅ {cfg['mujallad']}: دليل {mansukh} ملفًّا · MANIFEST {len(rows)} سطرًا · QR ({lib}) ⟵ {_rabt(d['asl'], cfg['mujallad'])}")
        natija.append((cfg["mujallad"], mansukh))
    bayan_alawi(base, out=out)
    return 0


SKIP_TOP = (".git", "__pycache__", ".DS_Store")


def _top_rows(base):
    rows = []
    for dp, dn, fn in os.walk(base):
        dn[:] = sorted(x for x in dn if x not in SKIP_TOP and "_muhakkim_" not in x)
        for f in sorted(fn):
            rel = os.path.relpath(os.path.join(dp, f), base)
            if f in SKIP_TOP or f == "MANIFEST.sha256" and dp == base or f.endswith((".pdf", ".pyc")):
                continue
            rows.append(f"{_sha(os.path.join(dp, f))}  {rel}")
    return rows


def bayan_alawi(base, out=print):
    rows = _top_rows(base)
    open(os.path.join(base, "MANIFEST.sha256"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    out(f"■ البيانُ العلويّ: {len(rows)} ملفًّا (بلا PDF)")
    return len(rows)


def tahaqquq_alawi(base, out=print):
    man = os.path.join(base, "MANIFEST.sha256")
    if not os.path.isfile(man):
        out("⛔ لا بيانَ علويًّا"); return 1
    kutib = {l.rstrip("\n").split("  ", 1)[1]: l.split("  ", 1)[0] for l in open(man, encoding="utf-8") if l.strip()}
    hadir = {l.split("  ", 1)[1]: l.split("  ", 1)[0] for l in _top_rows(base)}
    naqis = sorted(set(kutib) - set(hadir)); zaid = sorted(set(hadir) - set(kutib))
    mukhalif = sorted(k for k in kutib if k in hadir and kutib[k] != hadir[k])
    for k in naqis: out(f"⛔ غائبٌ عن القرص: {k}")
    for k in zaid: out(f"⛔ ملفٌّ ليس في البيان: {k}")
    for k in mukhalif: out(f"⛔ بصمةٌ تخالف: {k}")
    n = len(naqis) + len(zaid) + len(mukhalif)
    out(f"{'✅' if not n else '⚠️'} البيانُ العلويّ: {len(kutib)} بصمةً · أعطاب {n}")
    return n


def tahaqquq(masdar=MASDAR, out=print):
    d = json.load(open(masdar, encoding="utf-8")); base = os.path.dirname(os.path.abspath(masdar)); atab = 0
    for cfg in d["tajarib"]:
        tj = os.path.join(base, cfg["mujallad"]); man = os.path.join(tj, "MANIFEST.sha256")
        if not os.path.isfile(man):
            out(f"⛔ {cfg['mujallad']}: لا MANIFEST"); atab += 1; continue
        n = 0
        for line in open(man, encoding="utf-8"):
            if not line.strip():
                continue
            h, rel = line.rstrip("\n").split("  ", 1); p = os.path.join(tj, rel)
            if not os.path.isfile(p) or _sha(p) != h:
                out(f"⛔ {cfg['mujallad']}: بصمةٌ تخالف: {rel}"); atab += 1
            n += 1
        # نسخُ الدليلِ تطابقُ مصدرَها إن كان المصدرُ حاضرًا
        src = os.path.join(os.path.dirname(base), cfg["masdar"])
        if os.path.isdir(src):
            for f in _malaffat(cfg, src):
                a, b = os.path.join(src, f), os.path.join(tj, "دليل", f)
                if os.path.isfile(a) and (not os.path.isfile(b) or _sha(a) != _sha(b)):
                    out(f"⛔ {cfg['mujallad']}: نسخةُ الدليلِ تخالفُ مصدرَها: {f}"); atab += 1
        out(f"{'✅' if not atab else '⚠️'} {cfg['mujallad']}: {n} بصمةً فُحِصت")
    atab += tahaqquq_alawi(base, out=out)
    out("■ الحدّ: يُثبتُ أنّ الملفّاتِ هي هي؛ ولا يُثبتُ أنّ الرابطَ يُفتَح.")
    return 0 if not atab else 2


def miraa(masdar=MASDAR, out=print):
    d = json.load(open(masdar, encoding="utf-8")); base = os.path.dirname(os.path.abspath(masdar)); m = d.get("miraa") or {}
    if not m.get("wijha"):
        out("⛔ لا miraa.wijha في مصدر.json"); return 1
    wijha = os.path.join(ROOT, m["wijha"]) if not os.path.isabs(m["wijha"]) else m["wijha"]
    if tahaqquq(masdar, out=lambda *a, **k: None) != 0:
        out("⛔ المصدرُ لا يمرُّ بالتحقّق — أعِدِ التوليدَ أوّلًا"); return 2
    # تفريغُ الوجهةِ عدا .git ثمّ نسخٌ بايتيّ
    os.makedirs(wijha, exist_ok=True)
    for f in os.listdir(wijha):
        if f == ".git":
            continue
        p = os.path.join(wijha, f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    def _tajahul(dp, names):   # يُهمَلُ: .git وما شابهه، وملفّاتُ .pyc، و**مجلّداتُ** نسخِ المحكّم (لا ملفّاتٌ تحملُ الاسم)
        return {n for n in names if n in SKIP_TOP or n.endswith(".pyc") or ("_muhakkim_" in n and os.path.isdir(os.path.join(dp, n)))}
    for f in sorted(os.listdir(base)):
        src = os.path.join(base, f); dst = os.path.join(wijha, f)
        if f in SKIP_TOP or ("_muhakkim_" in f and os.path.isdir(src)):
            continue
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=_tajahul)
        else:
            shutil.copyfile(src, dst)
    n = tahaqquq_alawi(wijha, out=out)
    if n:
        out("⛔ نسخةُ المرآةِ تخالفُ البيان"); return 2
    url = f"https://github.com/{m.get('malik','<المالك>')}/{m.get('ism','<الاسم>')}"
    out(f"✅ نسخةُ المرآةِ في {wijha} · تطابقُ البيانَ العلويّ · الرابطُ المتوقَّع {url}")
    out("■ النشرُ بيدِ 306 — في طرفيّتِه (لا يُنفَّذُ من هنا):")
    out(f"   cd '{wijha}' && git init -b main && git add -A && git commit -m 'توثيق: إثباتٌ مفتوحٌ لكلِّ تجربة — مرآةٌ علنيّةٌ لمجلّدِ توثيق/'")
    out(f"   gh repo create {m.get('malik','<المالك>')}/{m.get('ism','<الاسم>')} --public --source=. --remote=origin --push")
    return 0


def _dukhan():
    n = ok = 0

    def t(w, c):
        nonlocal n, ok
        n += 1; ok += bool(c); print(("  ✅ " if c else "  ❌ ") + w)
    tmp = tempfile.mkdtemp(prefix="ithbat_dukhan_")
    try:
        root = os.path.join(tmp, "repo"); src = os.path.join(root, "archive", "x"); os.makedirs(src)
        open(os.path.join(src, "a.txt"), "w").write("alpha\n"); open(os.path.join(src, "sirr.txt"), "w").write("secret\n")
        tw = os.path.join(root, "توثيق"); tj = os.path.join(tw, "t1"); os.makedirs(tj)
        open(os.path.join(tj, "اثبات.md"), "w", encoding="utf-8").write("# إثبات\n")
        cfg = {"asl": "https://example.invalid/base", "tajarib": [{"mujallad": "t1", "masdar": "archive/x", "malaffat": ["a.txt"]}]}
        m = os.path.join(tw, "مصدر.json"); json.dump(cfg, open(m, "w", encoding="utf-8"), ensure_ascii=False)
        sakit = lambda *a, **k: None  # noqa: E731
        t("التوليدُ يمرّ", tawlid(m, out=sakit) == 0)
        t("⛔ سالب: ما ليس في القائمةِ لا يُنسَخ (sirr.txt غائب)", not os.path.exists(os.path.join(tj, "دليل", "sirr.txt")))
        t("MANIFEST فيه اثبات.md ودليل/a.txt", open(os.path.join(tj, "MANIFEST.sha256"), encoding="utf-8").read().count("\n") == 2)
        t("الرابطُ مرمَّزٌ بالعربيّة", open(os.path.join(tj, "بصمة-الاثبات.txt"), encoding="utf-8").read().splitlines()[1] == "https://example.invalid/base/t1/" + quote("اثبات.md", safe=""))
        t("qr.png وُلِد", os.path.getsize(os.path.join(tj, "qr.png")) > 200)
        t("التحقّقُ يمرُّ على السليم (0)", tahaqquq(m, out=sakit) == 0)
        open(os.path.join(tj, "دليل", "a.txt"), "a").write("x")
        t("⛔ سالب: بايتٌ في الدليلِ ⟵ التحقّقُ 2", tahaqquq(m, out=sakit) == 2)
        tawlid(m, out=sakit)
        open(os.path.join(tj, "اثبات.md"), "a", encoding="utf-8").write("x")
        t("⛔ سالب: حرفٌ في اثبات.md ⟵ التحقّقُ 2", tahaqquq(m, out=sakit) == 2)
        q1 = _sha(os.path.join(tj, "qr.png")); cfg["asl"] = "https://example.invalid/other"
        json.dump(cfg, open(m, "w", encoding="utf-8"), ensure_ascii=False); tawlid(m, out=sakit)
        t("⛔ سالب: تغييرُ الرابطِ يغيّرُ الرمز", _sha(os.path.join(tj, "qr.png")) != q1)
        cfg["tajarib"][0]["malaffat"] = ["la-wujud.txt"]; json.dump(cfg, open(m, "w", encoding="utf-8"), ensure_ascii=False)
        t("⛔ سالب: ملفٌّ في القائمةِ غائبٌ ⟵ يرفضُ التوليد (1)", tawlid(m, out=sakit) == 1)
        cfg["tajarib"][0]["malaffat"] = ["a.txt"]; cfg["miraa"] = {"malik": "x", "ism": "y", "wijha": os.path.join(tmp, "miraa")}
        json.dump(cfg, open(m, "w", encoding="utf-8"), ensure_ascii=False); tawlid(m, out=sakit)
        open(os.path.join(tj, "اثبات.pdf"), "wb").write(b"%PDF-fake")
        t("البيانُ العلويُّ يستثني PDF", "اثبات.pdf" not in open(os.path.join(tw, "MANIFEST.sha256"), encoding="utf-8").read())
        t("التحقّقُ العلويُّ يمرّ", tahaqquq_alawi(tw, out=sakit) == 0)
        open(os.path.join(tw, "dakhil.txt"), "w").write("stray")
        t("⛔ سالب: ملفٌّ دخيلٌ ليس في البيانِ يُكشَف", tahaqquq_alawi(tw, out=sakit) == 1)
        os.remove(os.path.join(tw, "dakhil.txt"))
        t("المرآةُ تُبنى وتطابقُ البيان", miraa(m, out=sakit) == 0 and os.path.isfile(os.path.join(tmp, "miraa", "t1", "اثبات.md")))
        t("⛔ سالب: المرآةُ لا تحملُ ما ليس في القائمة", not os.path.exists(os.path.join(tmp, "miraa", "t1", "دليل", "sirr.txt")))
        open(os.path.join(tj, "out_muhakkim_1.txt"), "w").write("ok"); os.makedirs(os.path.join(tj, "x_muhakkim_1"), exist_ok=True)
        open(os.path.join(tj, "x_muhakkim_1", "ledger.jsonl"), "w").write("{}")
        tawlid(m, out=sakit); miraa(m, out=sakit)
        t("ملفٌّ باسمِ muhakkim يُنسَخُ إلى المرآة (العطبُ المقيسُ 17 نوفمبر)", os.path.isfile(os.path.join(tmp, "miraa", "t1", "out_muhakkim_1.txt")))
        t("⛔ سالب: مجلّدُ نسخةِ المحكّمِ لا يُنسَخُ ولا يدخلُ البيان", not os.path.exists(os.path.join(tmp, "miraa", "t1", "x_muhakkim_1")) and "x_muhakkim_1" not in open(os.path.join(tw, "MANIFEST.sha256"), encoding="utf-8").read())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n🔥 دخانُ مولّدِ الإثبات: {ok}/{n}")
    return 0 if ok == n else 2


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--dukhan" in a:
        sys.exit(_dukhan())
    if "--tahaqquq" in a:
        sys.exit(tahaqquq())
    if "--miraa" in a:
        sys.exit(miraa())
    sys.exit(tawlid())
