#!/usr/bin/env python3
"""Parse registry without importing - improved"""
import re

REGISTRY_PATH = '/mnt/e/桌面/AiOps/aiopslab/AIOpsLab/aiopslab/orchestrator/problems/registry.py'

def parse_registry():
    with open(REGISTRY_PATH, 'r') as f:
        content = f.read()
    
    # Find all quoted strings that look like problem IDs
    # Pattern: "something-task_type-N" where task_type is detection/localization/analysis/mitigation
    pattern = r'"([a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*-[a-z]+-\d+)"'
    matches = re.findall(pattern, content, re.IGNORECASE)
    
    # Deduplicate and sort
    unique_ids = sorted(set(matches))
    return unique_ids

if __name__ == "__main__":
    ids = parse_registry()
    print(f"Found {len(ids)} problems:")
    for pid in ids:
        print(f"  - {pid}")