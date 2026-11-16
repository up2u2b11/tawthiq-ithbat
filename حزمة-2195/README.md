# حزمةُ تحقّقٍ مستقلّ — سلسلةُ UP2U2B · 20261116T225519

- الحلقات: 2195 · الرأس: `aa39f2f833cddc9394965a690b0d1245c9a616977139296fd3e2bcd39abe577a` · النمط: ربطٌ وتواقيعُ فقط (بلا أسماءِ ملفّات)
- حلقاتٌ في الدفترِ بلا ملفٍّ عندَ التصدير: 0
- التحقّق: `python3 tahaqquq_mustaqill.py` من داخلِ هذا المجلّد (يلزمُ Python 3 وssh-keygen فقط).
- العقد: seal_hash = SHA256(prev_hash ‖ content_hash ‖ JSON(kind, content_hash, size, type, source_filename, witness, niyyah, stage, hijri) مرتّبةً بلا فراغات) · حلقةُ الأصل 64 صفراً.
- التواقيع: SSH (`ssh-keygen -Y`) في النطاقِ `up2u2b-khatm` بمفاتيحِ `allowed_signers`.
- الحدّ: تُثبتُ الحزمةُ الترتيبَ والربطَ وصحّةَ التواقيعِ على المتونِ المرفقة؛ ولا تُثبتُ محتوى الخزنة (غيرُ مرفق).
