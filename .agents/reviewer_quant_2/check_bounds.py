import re

def check_array_bounds():
    with open(r'c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5', 'r', encoding='utf-8') as f:
        text = f.read()

    brain_func_pattern = re.compile(r'int\s+(Brain\d{3}_[A-Za-z0-9_]+)\s*\(\s*\)', re.MULTILINE)
    matches = list(brain_func_pattern.finditer(text))
    
    issues = []
    
    for i, m in enumerate(matches):
        bname = m.group(1)
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else text.find('CalculateEnsembleConsensusScore', start)
        body = text[start:end]
        
        # Check GetRatesSeries calls
        grs = re.findall(r'GetRatesSeries\s*\([^,]+,\s*([^,]+),\s*([^,]+),\s*([A-Za-z0-9_]+)\)', body)
        for g in grs:
            shift = int(g[0].strip())
            count = int(g[1].strip())
            arr_name = g[2].strip()
            
            # Check guard
            # Usually: if(GetRatesSeries(...) < count) return 0;
            # Find all accesses to arr_name[index]
            accesses = re.findall(r'\b' + arr_name + r'\[([^\]]+)\]', body)
            for acc in accesses:
                acc_clean = acc.strip()
                # If it's an integer
                try:
                    idx = int(acc_clean)
                    if idx >= count:
                        issues.append((bname, f"Index {idx} >= count {count} for {arr_name}"))
                    if idx < 0:
                        issues.append((bname, f"Negative index {idx} for {arr_name}"))
                except ValueError:
                    # It's an expression or variable, e.g. i, i+1
                    pass

        # Check GetIndicatorSeries calls
        gis = re.findall(r'GetIndicatorSeries\s*\([^,]+,\s*[^,]+,\s*([^,]+),\s*([^,]+),\s*([A-Za-z0-9_]+)\)', body)
        for g in gis:
            shift = int(g[0].strip())
            count = int(g[1].strip())
            arr_name = g[2].strip()
            accesses = re.findall(r'\b' + arr_name + r'\[([^\]]+)\]', body)
            for acc in accesses:
                acc_clean = acc.strip()
                try:
                    idx = int(acc_clean)
                    if idx >= count:
                        issues.append((bname, f"Index {idx} >= count {count} for indicator {arr_name}"))
                except ValueError:
                    pass

    print(f"Total bounds issues found: {len(issues)}")
    for iss in issues:
        print(f"  {iss[0]}: {iss[1]}")

if __name__ == '__main__':
    check_array_bounds()
