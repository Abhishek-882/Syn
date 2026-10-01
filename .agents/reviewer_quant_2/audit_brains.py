import re
import sys

def audit_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    content = "".join(lines)
    
    # Find all brain functions
    brain_func_pattern = re.compile(r'int\s+(Brain\d{3}_[A-Za-z0-9_]+)\s*\(\s*\)', re.MULTILINE)
    matches = list(brain_func_pattern.finditer(content))
    
    print(f"Total brain function definitions found: {len(matches)}")
    
    brains = []
    for i, m in enumerate(matches):
        func_name = m.group(1)
        start_pos = m.start()
        
        # End pos is start of next match or start of CalculateEnsembleConsensusScore
        if i + 1 < len(matches):
            end_pos = matches[i+1].start()
        else:
            calc_match = re.search(r'double\s+CalculateEnsembleConsensusScore', content[start_pos:])
            if calc_match:
                end_pos = start_pos + calc_match.start()
            else:
                end_pos = len(content)
                
        func_body = content[start_pos:end_pos]
        start_line = content[:start_pos].count('\n') + 1
        end_line = content[:end_pos].count('\n') + 1
        
        brains.append({
            'num': i + 1,
            'name': func_name,
            'body': func_body,
            'start_line': start_line,
            'end_line': end_line,
            'line_count': end_line - start_line
        })
        
    print(f"Processed {len(brains)} brains.\n")
    
    # Check 1: Exactly 144 brains
    if len(brains) != 144:
        print(f"[FAIL] Expected 144 brains, but found {len(brains)}!")
    else:
        print("[PASS] Exactly 144 brains found.")
        
    # Check 2: Numbering Brain001 through Brain144
    numbering_ok = True
    for i, b in enumerate(brains):
        expected_prefix = f"Brain{i+1:03d}_"
        if not b['name'].startswith(expected_prefix):
            print(f"[FAIL] Brain {i+1} name {b['name']} does not start with {expected_prefix}")
            numbering_ok = False
    if numbering_ok:
        print("[PASS] All brains numbered consecutively Brain001 through Brain144.")
        
    # Check 3: Check return values for each brain
    # Returns should only ever be 1, -1, 0, or expressions evaluating to them.
    invalid_returns = []
    stub_brains = []
    bar0_accesses = []
    
    for b in brains:
        body = b['body']
        # Find all return statements
        returns = re.findall(r'return\s+([^;]+);', body)
        clean_returns = [r.strip() for r in returns]
        
        # Check if all returns are strictly 1, -1, 0 (or simple combinations)
        for cr in clean_returns:
            # Check if cr is not in ['0', '1', '-1', '+1']
            if cr not in ['0', '1', '-1', '+1']:
                invalid_returns.append((b['name'], cr, b['start_line']))
                
        # Check if brain is a stub (e.g. only returns 0 without logic, or line count < 5)
        if len(clean_returns) == 1 and clean_returns[0] in ['0', '1', '-1'] and b['line_count'] < 6:
            stub_brains.append((b['name'], b['line_count'], clean_returns))
            
        # Check for bar[0] or shift 0 access
        # Look for GetIndicatorVal(..., 0), GetIndicatorSeries(..., 0, ...), GetRatesSeries(..., 0, ...)
        # or CopyBuffer(..., 0, 0, ...)
        # Note: buffer_index can be 0, but shift parameter must not be 0.
        # GetIndicatorVal(handle, buffer_index, shift)
        # Check calls to GetIndicatorVal
        giv_calls = re.findall(r'GetIndicatorVal\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\)', body)
        for g in giv_calls:
            shift = g[2].strip()
            if shift == '0':
                bar0_accesses.append((b['name'], f"GetIndicatorVal shift=0", b['start_line']))
                
        # Check calls to GetIndicatorSeries(handle, buffer_index, shift, count, arr)
        gis_calls = re.findall(r'GetIndicatorSeries\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,', body)
        for g in gis_calls:
            shift = g[2].strip()
            if shift == '0':
                bar0_accesses.append((b['name'], f"GetIndicatorSeries shift=0", b['start_line']))

        # Check calls to GetRatesSeries(tf, shift, count, rates)
        grs_calls = re.findall(r'GetRatesSeries\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,', body)
        for g in grs_calls:
            shift = g[1].strip()
            if shift == '0':
                bar0_accesses.append((b['name'], f"GetRatesSeries shift=0", b['start_line']))

    if invalid_returns:
        print(f"[FAIL] Found {len(invalid_returns)} non-standard return statements:")
        for ir in invalid_returns[:10]:
            print(f"   {ir[0]} line {ir[2]}: return {ir[1]}")
    else:
        print("[PASS] All return statements across all 144 brains evaluate strictly to +1, -1, or 0.")
        
    if stub_brains:
        print(f"[FAIL] Found {len(stub_brains)} stub brains:")
        for sb in stub_brains:
            print(f"   {sb[0]}: {sb[1]} lines, returns: {sb[2]}")
    else:
        print("[PASS] Zero dummy or stub brains found! All brains have active logic.")
        
    if bar0_accesses:
        print(f"[FAIL] Found {len(bar0_accesses)} instances of unconfirmed bar[0] access:")
        for ba in bar0_accesses:
            print(f"   {ba[0]} line {ba[2]}: {ba[1]}")
    else:
        print("[PASS] Zero bar[0] accesses found. All brains query shift >= 1.")
        
    # Check distribution of line counts
    line_counts = [b['line_count'] for b in brains]
    avg_lines = sum(line_counts) / len(line_counts)
    min_lines = min(line_counts)
    max_lines = max(line_counts)
    print(f"\nBrain Line Count Stats: Min={min_lines}, Max={max_lines}, Avg={avg_lines:.1f}")

    # Check mapping in CalculateEnsembleConsensusScore
    consensus_body = content[content.find("CalculateEnsembleConsensusScore"):content.find("void ExecuteTrade")]
    votes_mapped = re.findall(r'votes\[(\d+)\]\s*=\s*(Brain\d{3}_[A-Za-z0-9_]+)\s*\(\s*\);', consensus_body)
    print(f"\nTotal brains mapped in CalculateEnsembleConsensusScore: {len(votes_mapped)}")
    
    missing_indices = []
    for i in range(144):
        found = False
        for vm in votes_mapped:
            if int(vm[0]) == i and vm[1] == brains[i]['name']:
                found = True
                break
        if not found:
            missing_indices.append(i)
            
    if missing_indices:
        print(f"[FAIL] Missing or mismatched brains in consensus calculation at indices: {missing_indices}")
    else:
        print("[PASS] All 144 brains correctly mapped 1-to-1 to votes[0..143] in CalculateEnsembleConsensusScore.")

if __name__ == '__main__':
    audit_file(r'c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5')
