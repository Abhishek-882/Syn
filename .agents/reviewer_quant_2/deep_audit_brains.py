import re

with open(r'c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5', 'r', encoding='utf-8') as f:
    text = f.read()

brain_func_pattern = re.compile(r'int\s+(Brain\d{3}_[A-Za-z0-9_]+)\s*\(\s*\)', re.MULTILINE)
matches = list(brain_func_pattern.finditer(text))

print(f"Auditing {len(matches)} brain functions for deep quantitative logic...\n")

issues = []
zero_division_risks = []
missing_guard_risks = []

for i, m in enumerate(matches):
    bname = m.group(1)
    start = m.start()
    end = matches[i+1].start() if i+1 < len(matches) else text.find('CalculateEnsembleConsensusScore', start)
    body = text[start:end]
    
    # 1. Check if division exists and if denominator is guarded
    # Search for / followed by variable or expression
    # Skip comments //
    code_lines = [l for l in body.split('\n') if not l.strip().startswith('//')]
    clean_code = "\n".join(code_lines)
    
    divisions = re.findall(r'/([^/*;\n,)]+)', clean_code)
    for d in divisions:
        denom = d.strip()
        # If denom is a constant number like 2.0 or 100.0 or count, it's safe if > 0
        try:
            val = float(denom)
            if val == 0:
                zero_division_risks.append((bname, f"Division by zero constant {denom}"))
            continue
        except ValueError:
            pass
            
        # Denom is a variable or expression
        # Check if guarded by if(denom <= 0) or if(denom == 0) or MathAbs(denom) < ...
        # Let's inspect variable name
        var_match = re.search(r'[A-Za-z0-9_]+', denom)
        if var_match:
            var_name = var_match.group(0)
            if var_name not in ['_Point', 'g_pipSize', 'count', 'ArraySize']:
                # Check if var_name is guarded in body
                if not re.search(r'\b' + re.escape(var_name) + r'\s*(<=|==|<|!=)', clean_code):
                    zero_division_risks.append((bname, f"Potential un-guarded denominator '{var_name}' in '{denom}'"))

    # 2. Check if indicator handle is used, is it one of the defined global handles?
    used_handles = re.findall(r'(g_h_[A-Za-z0-9_]+)', body)
    for h in used_handles:
        if h not in text[:start]: # Defined before?
            issues.append((bname, f"Undefined handle {h}"))

    # 3. Check for rates or indicators fetched
    has_rates = "GetRatesSeries" in body
    has_ind_val = "GetIndicatorVal" in body
    has_ind_series = "GetIndicatorSeries" in body
    
    if not (has_rates or has_ind_val or has_ind_series or "SymbolInfo" in body or "TimeGMT" in body):
        issues.append((bname, "No data fetching found!"))

print(f"Total undefined handle issues: {len([x for x in issues if 'Undefined handle' in x[1]])}")
print(f"Total zero data fetching issues: {len([x for x in issues if 'No data fetching' in x[1]])}")
print(f"Potential un-guarded denominator warnings: {len(zero_division_risks)}")
for zd in zero_division_risks:
    print(f"  {zd[0]}: {zd[1]}")
