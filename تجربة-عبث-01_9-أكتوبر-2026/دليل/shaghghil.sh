#!/bin/zsh
# يشغّل المتحققَين على الأساس والنسخ السبع، ويكتب ناتج كل تشغيل ورمز خروجه.
#   v_trunk.py = ~/up2u2b/tech/tahaqquq_mustaqill.py كما هو يوم القياس
#   v_fixed.py = git show 97b6d3bc:tech/tahaqquq_mustaqill.py
cd "$(dirname "$0")"
for b in base a1_content a1_seal a2_forge a3_batr a4_bila_tawqi a5_batr40 a6_ruju; do for v in v_trunk v_fixed; do
  python3 -B $v.py "$PWD/$b" > "out_${b}__${v}.txt" 2>&1; echo "$b | $v | rc=$?" >> natija.txt
done; done
