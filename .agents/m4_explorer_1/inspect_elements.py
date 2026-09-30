import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

with open('results/web_verification_failures.json', 'r', encoding='utf-8') as f:
    failures_data = json.load(f)

tested = failures_data.get('tested_elements', [])
print(f"Total tested elements in JSON: {len(tested)}")

selectors_count = {}
for el in tested:
    sel = el['selector']
    selectors_count[sel] = selectors_count.get(sel, 0) + 1

for sel, count in sorted(selectors_count.items()):
    print(f"  {sel}: {count}")

print("\nDetailed tested elements list:")
for i, el in enumerate(tested):
    print(f"{i+1:2d}. selector={el['selector']:<18} bbox={el['bounding_box']} text={repr(el['text'][:35])}")

with open('web/syndicate_3d_visualizer.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

print("\n--- Interactive Elements in syndicate_3d_visualizer.html ---")
buttons = soup.find_all('button')
print(f"Total <button> tags in HTML: {len(buttons)}")
for b in buttons:
    parent = b.parent.name if b.parent else 'None'
    grandparent = b.parent.parent.name if b.parent and b.parent.parent else 'None'
    in_plaque = bool(b.find_parent(id='curatorial-plaque'))
    print(f"  button: id={b.get('id')} class={b.get('class')} in_plaque={in_plaque} text={repr(b.get_text(strip=True))}")

inputs = soup.find_all('input')
print(f"\nTotal <input> tags in HTML: {len(inputs)}")
for inp in inputs:
    print(f"  input: id={inp.get('id')} type={inp.get('type')} class={inp.get('class')}")

target_classes = [
    'hud-btn', 'health-chip', 'tag-chip', 'stage-pill', 'kpi-card', 
    'alert-card', 'telemetry-row', 'deck-toggle-btn', 'plaque-close-btn', 
    'action-btn', 'backlink-pill'
]

print("\n=== ALL ELEMENTS WITH ID ===")
ids = [el.get('id') for el in soup.find_all(id=True)]
print(f"Total unique IDs: {len(set(ids))}")
for el_id in sorted(set(ids)):
    el = soup.find(id=el_id)
    cls_str = " ".join(el.get('class', []))
    print(f"  #{el_id:<25} tag={el.name:<10} class={cls_str}")

