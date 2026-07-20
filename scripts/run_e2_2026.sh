#!/usr/bin/env bash
# 2026 E-2 decomposition driver: augment the freshly-detected caches, then grade the champion
# across the 2x2 grid {pre-fix, post-fix cache} x {Tier-2 off, on}.
set -e
cd /home/user/AI-trading-agents
SP=/tmp/claude-0/-home-user-AI-trading-agents/8f4cdd65-f942-532a-87f2-c9c07c27272a/scratchpad

echo "=== augment OB onto post-fix caches ==="
python3 -m scripts._augment_ob data/reference/nq_1m_feb_jul2026.parquet \
    output/triggers_feb.csv output/triggers_marjul.csv

echo ""
echo "=== GRID: baseline -> +E2 -> +E2+Tier2 ==="
# PREFIX = old detection (pre E-2), POSTFIX = new detection (E-2 fixed)
python3 -m scripts.grade_e2_split output/triggers_feb_ob_prefix.csv output/triggers_marjul_ob_prefix.csv PREFIX  TIER2=OFF 2>&1 | tee $SP/g_pre_t2off.txt
python3 -m scripts.grade_e2_split output/triggers_feb_ob.csv        output/triggers_marjul_ob.csv        POSTFIX TIER2=OFF 2>&1 | tee $SP/g_post_t2off.txt
python3 -m scripts.grade_e2_split output/triggers_feb_ob.csv        output/triggers_marjul_ob.csv        POSTFIX TIER2=ON  2>&1 | tee $SP/g_post_t2on.txt
echo "ALL_2026_GRADES_DONE"
