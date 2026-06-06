"""
EverQuest Recipe Ingredient Scraper v4
SETUP:  pip install requests beautifulsoup4
USAGE:  python eq_scraper.py  |  Ctrl+C to pause, re-run to resume
OUTPUT: scraped_ingredients/ingredients_ALL.csv
"""

import csv, json, os, time, sys, re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Run: pip install requests beautifulsoup4")
    sys.exit(1)

PARSER_FOLDER  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER  = os.path.join(PARSER_FOLDER, 'scraped_ingredients')
PROGRESS_FILE  = os.path.join(OUTPUT_FOLDER, '_progress.json')
DELAY_SECONDS  = 2.5
EQTRADERS_BASE = "https://www.eqtraders.com/items/show_item.php?item={}&printer=tree"

SKILL_FILES = {
    'Alchemy':        'Alchemy.txt',
    'Baking':         'Baking.txt',
    'Blacksmithing':  'Blacksmithing.txt',
    'Brewing':        'Brewing.txt',
    'Fishing':        'Fishing.txt',
    'Fletching':      'Fletching.txt',
    'Jewelry Making': 'Jewelry_Making.txt',
    'Make Poison':    'Make_Poison.txt',
    'Pottery':        'Pottery.txt',
    'Research':       'Research.txt',
    'Tailoring':      'Tailoring.txt',
    'Tinkering':      'Tinkering.txt',
}

def parse_skill_file(filepath):
    recipes = []
    if not os.path.exists(filepath): return recipes
    with open(filepath, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                parts = list(csv.reader([line], delimiter='\t'))[0]
                name      = parts[0].strip('"') if len(parts) > 0 else ''
                trivial   = parts[1].strip('"') if len(parts) > 1 else ''
                item_id   = parts[2].strip('"') if len(parts) > 2 else ''
                expansion = parts[5].strip('"') if len(parts) > 5 else ''
                vendor    = parts[7].strip('"') if len(parts) > 7 else ''
                if name and item_id:
                    recipes.append({'name': name, 'trivial': trivial, 'item_id': item_id,
                                    'expansion': expansion, 'vendor': vendor})
            except: pass
    return recipes

def scrape_recipe(item_id, session):
    url = EQTRADERS_BASE.format(item_id)
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        result = {'url': url, 'container': '', 'trivial_site': '',
                  'ingredients': [], 'error': ''}

        # Parse from HTML directly — find the recipe list items
        # EQTraders structure in the Recipe(s) section:
        # <li>Alchemy Components: <a>Item1</a>, <a>Item2</a>
        # In: <a>Container</a>
        # Trivial at: N

        # Find all list items in the page
        for li in soup.find_all('li'):
            li_text = li.get_text(separator=' ', strip=True)
            
            # Match "Alchemy Components:" or "Baking Components:" etc
            comp_match = re.match(
                r'^[\-\*\s]*(\w[\w\s]*?)\s+components?\s*:\s*(.+)',
                li_text, re.IGNORECASE)
            
            if comp_match and not result['ingredients']:
                skill_name = comp_match.group(1).strip()
                comp_text  = comp_match.group(2).strip()
                
                # Get ingredient names from links within this li
                links = li.find_all('a')
                if links:
                    for link in links:
                        name = link.get_text(strip=True)
                        if name and len(name) < 80:
                            # Check for quantity in parentheses after link
                            next_sib = link.next_sibling
                            qty = ''
                            if next_sib and isinstance(next_sib, str):
                                qty_match = re.search(r'\((\d+)\)', next_sib)
                                if qty_match:
                                    qty = f" ({qty_match.group(1)})"
                            result['ingredients'].append(f"{name}{qty}")
                else:
                    # Fallback: split text by comma
                    parts = re.split(r',\s*(?![^()]*\))', comp_text)
                    for p in parts:
                        p = re.sub(r'\s+', ' ', p).strip()
                        if p and len(p) < 80:
                            result['ingredients'].append(p)
                
                # Look for "In:" and "Trivial" in sibling elements or next text
                # Check next siblings
                parent = li.parent
                if parent:
                    siblings = list(parent.children)
                    try:
                        idx = siblings.index(li)
                        for sib in siblings[idx+1:idx+8]:
                            sib_text = sib.get_text(strip=True) if hasattr(sib, 'get_text') else str(sib).strip()
                            if sib_text.startswith('In:') and not result['container']:
                                result['container'] = sib_text[3:].strip().split(',')[0].strip()
                            if 'Trivial at:' in sib_text and not result['trivial_site']:
                                m = re.search(r'Trivial at:\s*(\d+)', sib_text)
                                if m: result['trivial_site'] = m.group(1)
                    except (ValueError, TypeError):
                        pass

            if result['ingredients']:
                break  # Got first recipe, stop

        # Fallback: parse plain text if HTML approach failed
        if not result['ingredients']:
            text = soup.get_text(separator='\n')
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                # Look for "Components:" anywhere in line
                if 'components:' in line.lower() and not result['ingredients']:
                    # Extract everything after "Components:"
                    after = re.split(r'components?:', line, flags=re.IGNORECASE, maxsplit=1)
                    if len(after) > 1:
                        comp_text = after[1].strip()
                        parts = re.split(r',\s*(?![^()]*\))', comp_text)
                        for p in parts:
                            p = re.sub(r'\s+', ' ', p).strip()
                            if p and len(p) < 80 and p.lower() not in ['','none']:
                                result['ingredients'].append(p)
                
                if 'in:' == line.lower()[:3] and not result['container']:
                    result['container'] = line[3:].strip().split(',')[0].strip()
                
                if 'trivial at:' in line.lower() and not result['trivial_site']:
                    m = re.search(r'trivial at:\s*(\d+)', line, re.IGNORECASE)
                    if m: result['trivial_site'] = m.group(1)

                if result['ingredients'] and result['container'] and result['trivial_site']:
                    break

        return result

    except requests.exceptions.RequestException as e:
        return {'url': url, 'container': '', 'trivial_site': '',
                'ingredients': [], 'error': str(e)}

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

FIELDNAMES = ['skill','name','trivial','item_id','expansion','vendor',
              'container','trivial_site',
              'ingredient_1','ingredient_2','ingredient_3','ingredient_4',
              'ingredient_5','ingredient_6','ingredient_7','ingredient_8',
              'url','error']

def get_csv_path(skill):
    return os.path.join(OUTPUT_FOLDER, f'ingredients_{skill.replace(" ","_")}.csv')

def append_to_csv(skill, row_data):
    filepath = get_csv_path(skill)
    file_exists = os.path.exists(filepath)
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists: writer.writeheader()
        ingredients = row_data.get('ingredients', [])
        row = {k: row_data.get(k, '') for k in
               ['skill','name','trivial','item_id','expansion','vendor',
                'container','trivial_site','url','error']}
        for i in range(1, 9):
            row[f'ingredient_{i}'] = ingredients[i-1] if i-1 < len(ingredients) else ''
        writer.writerow(row)

def combine_csvs():
    combined = os.path.join(OUTPUT_FOLDER, 'ingredients_ALL.csv')
    rows = []
    for skill in SKILL_FILES:
        path = get_csv_path(skill)
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                rows.extend(list(csv.DictReader(f)))
    if rows:
        with open(combined, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            w.writeheader(); w.writerows(rows)
        print(f"  Combined: {combined} ({len(rows)} recipes)")

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print("=" * 60)
    print("  EQ Recipe Scraper v4 — HTML list item parser")
    print("=" * 60)

    progress = load_progress()
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.eqtraders.com/',
    })

    all_recipes = {}
    total_done = total_remaining = 0
    for skill, filename in SKILL_FILES.items():
        recipes = parse_skill_file(os.path.join(PARSER_FOLDER, filename))
        all_recipes[skill] = recipes
        done_ids = set(progress.get(skill, {}).keys())
        remaining = [r for r in recipes if r['item_id'] not in done_ids]
        total_done += len(done_ids)
        total_remaining += len(remaining)
        print(f"  {skill:20s}: {len(recipes):4d} total | {len(done_ids):4d} done | {len(remaining):4d} remaining")

    print(f"\n  Remaining: {total_remaining} | ~{round(total_remaining*DELAY_SECONDS/3600,1)}h")
    print(f"  Ctrl+C to pause, re-run to resume\n{'─'*60}\n")

    if total_remaining == 0:
        print("All done!")
        combine_csvs()
        return

    try:
        count = 0
        for skill, recipes in all_recipes.items():
            done_ids = set(progress.get(skill, {}).keys())
            remaining = [r for r in recipes if r['item_id'] not in done_ids]
            if not remaining: continue

            print(f"\n[{skill}] {len(remaining)} remaining...")
            for recipe in remaining:
                count += 1
                pct = round((total_done + count) / (total_done + total_remaining) * 100, 1)
                print(f"  [{pct}%] ({count}/{total_remaining}) {recipe['name'][:45]}", end='', flush=True)

                result = scrape_recipe(recipe['item_id'], session)
                append_to_csv(skill, {**recipe, 'skill': skill, **result})

                if skill not in progress: progress[skill] = {}
                progress[skill][recipe['item_id']] = True
                save_progress(progress)

                n = len(result['ingredients'])
                if result['error']:
                    print(f" -> ERR: {result['error'][:35]}")
                elif n:
                    print(f" -> {n} ingr: {', '.join(result['ingredients'][:3])}{'...' if n>3 else ''}")
                else:
                    print(f" -> (not found)")

                time.sleep(DELAY_SECONDS)

        print("\nAll done! Combining...")
        combine_csvs()

    except KeyboardInterrupt:
        print("\n\n[PAUSED] Saved. Re-run to continue.")
        save_progress(progress)
        sys.exit(0)

if __name__ == '__main__':
    main()
