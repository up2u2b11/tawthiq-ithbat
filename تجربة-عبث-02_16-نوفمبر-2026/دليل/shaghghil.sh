#!/bin/zsh
# يشغّل المتحققَين على الأساس والنسخ السبع، ويكتب ناتج كل تشغيل ورمز خروجه وزمنه في natija.txt.
#   v_main.py  = tech/tahaqquq_mustaqill.py على main يوم القياس (بعد سدّ ثغرة التزوير 2cc40097)
#   v_qadim.py = git show 2cc40097^:tech/tahaqquq_mustaqill.py (قبل السدّ — مرّ عليه التزوير في 9 أكتوبر)
# الحزم في export/abath_20261116 (محجوبة عن git)، والمخرجات هنا بجوار هذا الملف.
K=/Users/emad_alwan/up2u2b/archive/saif/abath_20261116
X=/Users/emad_alwan/up2u2b/export/abath_20261116
typeset -F SECONDS
: > "$K/natija.txt"
echo "# $(date '+%Y-%m-%d %H:%M:%S %z') · $(python3 --version 2>&1) · $(uname -sm)" >> "$K/natija.txt"
for b in base a1_content a1_seal a2_forge a3_batr a4_bila_tawqi a5_batr40 a6_ruju; do
  for v in v_main v_qadim; do
    t0=$SECONDS
    python3 -B "$K/$v.py" "$X/$b" > "$K/out_${b}__${v}.txt" 2>&1; rc=$?
    printf '%s | %s | rc=%d | %.1fs\n' "$b" "$v" "$rc" $((SECONDS - t0)) >> "$K/natija.txt"
  done
done
