#!/usr/bin/env python3
import re

registry_path = '/mnt/e/桌面/AiOps/aiopslab/AIOpsLab/aiopslab/orchestrator/problems/registry.py'
with open(registry_path, 'r') as f:
    content = f.read()

# Correct patterns: must end with task_type keywords
task_types = 'detection|localization|analysis|mitigation'
p1 = rf'"([a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*-({task_types})-\d+)"'
p2 = rf'"([a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*-({task_types}))"'

m1 = re.findall(p1, content, re.IGNORECASE)
m2 = re.findall(p2, content, re.IGNORECASE)

# m1, m2 are tuples of (full_match, task_type)
m1_ids = [x[0] for x in m1]
m2_ids = [x[0] for x in m2]

# p1 captures all with variant; p2 captures all without variant
# Some IDs may be in both (edge cases)
all_ids = sorted(set(m1_ids) | set(m2_ids))
print(f'Total: {len(all_ids)}, p1={len(m1_ids)}, p2={len(m2_ids)}')

# Check flower (use x[0] since it's a tuple)
flower = [x[0] for x in m2 if 'flower' in x[0]]
print(f'\nFlower problems: {flower}')

# Docker-like: no variant number
# These are IDs matched by p2 but NOT by p1
p1_set = set(m1_ids)
p2_only = sorted(set(x[0] for x in m2 if x[0] not in p1_set))
print(f'\nNo-variant (docker) problems: {len(p2_only)}')
for p in p2_only: print(f'  {p}')