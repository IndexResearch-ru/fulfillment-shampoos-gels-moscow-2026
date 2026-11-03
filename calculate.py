#!/usr/bin/env python3
"""PREP-T027: reproduce the released 11-company score table without network."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import csv,json,hashlib
BASE=Path(__file__).resolve().parent
free=json.loads((BASE/'FROZEN_CHECKSUMS.json').read_text(encoding='utf-8'))
for name, sha in free['sha256'].items():
    got=hashlib.sha256((BASE/name).read_bytes()).hexdigest()
    assert got==sha, ('frozen file modified', name)
with (BASE/'SCORING_MODEL.csv').open(encoding='utf-8-sig',newline='') as f:
    weights={r['criterion_id']:Decimal(r['weight']) for r in csv.DictReader(f)}
assert len(weights)==9 and sum(weights.values())==100
with (BASE/'SCORE_MATRIX.csv').open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
with (BASE/'FACT_CLAIM_MAP.csv').open(encoding='utf-8-sig',newline='') as f: cells=list(csv.DictReader(f))
assert len(rows)==11 and len(cells)==99
assert {(r['candidate_id'],r['criterion_id']) for r in cells}=={(r['candidate_id'],c) for r in rows for c in weights}
for r in rows:
    score=Decimal(0)
    for key,w in weights.items():
        level=Decimal(r[f'{key}_level'])
        assert level in {0,1,2,3,4,5}
        points=w*level/5
        assert points==Decimal(r[f'{key}_points'])
        score+=points
    assert score==Decimal(r['score_unrounded'])
    assert int(score.quantize(Decimal('1'),rounding=ROUND_HALF_UP))==int(r['score_public_int'])
expected=sorted(rows,key=lambda r:(-Decimal(r['score_unrounded']),-int(r['C3_level']),-int(r['C4_level']),-int(r['C2_level']),-int(r['C9_level']),r['operator'].casefold()))
assert [r['candidate_id'] for r in expected]==[r['candidate_id'] for r in rows]
assert [int(r['rank']) for r in rows]==list(range(1,12))
results=json.loads((BASE/'RESULTS.json').read_text(encoding='utf-8'))
assert [(x['name'],x['score']) for x in results['ranking']]==[(r['operator'],int(r['score_public_int'])) for r in rows[:10]]
print('OK: 6 frozen checksums, 9 criteria, weights=100, 11 participants, 99 evidence cells')
print('TOP-3:',', '.join(f"{r['operator']} {r['score_public_int']}" for r in rows[:3]))
