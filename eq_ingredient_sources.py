"""
EverQuest Ingredient Source Scraper — Round 2
===============================================
Run this AFTER eq_scraper.py has finished.
Reads ingredients_ALL.csv, finds all unique ingredients,
looks up each one on EQTraders, and records:
  - Vendor sold (yes/no + vendor name + zone)
  - Dropped (zone name)
  - Foraged (zone name)
  - Crafted (subcombine recipe)
  - Fished (zone name)

SETUP:  pip install requests beautifulsoup4
USAGE:  python eq_ingredient_sources.py
        Ctrl+C to pause, re-run to resume

OUTPUT: scraped_ingredients/ingredient_sources.csv
        scraped_ingredients/ingredients_WITH_SOURCES.csv  (combined final file)
"""

import csv, json, os, time, sys, re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Run: pip install requests beautifulsoup4")
    sys.exit(1)

# ── SETTINGS ────────────────────────────────────────────────────────────────
SCRIPT_FOLDER   = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV       = os.path.join(SCRIPT_FOLDER, 'scraped_ingredients', 'ingredients_ALL.csv')
OUTPUT_FOLDER   = os.path.join(SCRIPT_FOLDER, 'scraped_ingredients')
SOURCES_CSV     = os.path.join(OUTPUT_FOLDER, 'ingredient_sources.csv')
COMBINED_CSV    = os.path.join(OUTPUT_FOLDER, 'ingredients_WITH_SOURCES.csv')
PROGRESS_FILE   = os.path.join(OUTPUT_FOLDER, '_sources_progress.json')
DELAY_SECONDS   = 2.0
EQTRADERS_SEARCH = "https://www.eqtraders.com/search/search.php?searchfield={}&Search=Search&menustr=035000000000"
EQTRADERS_ITEM   = "https://www.eqtraders.com/items/show_item.php?item={}&printer=tree"

# ── EXTRACT UNIQUE INGREDIENTS ───────────────────────────────────────────────
def get_unique_ingredients(csv_path):
    """Read ingredients_ALL.csv and return unique ingredient names."""
    ingredients = set()
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found. Run eq_scraper.py first!")
        sys.exit(1)

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for i in range(1, 9):
                ingr = row.get(f'ingredient_{i}', '').strip()
                if ingr:
                    # Remove quantity info like " (4)" at end
                    ingr_clean = re.sub(r'\s*\(\d+\)\s*$', '', ingr).strip()
                    if ingr_clean and len(ingr_clean) > 2:
                        ingredients.add(ingr_clean)

    return sorted(ingredients)

# ── SEARCH EQTRADERS FOR ITEM ────────────────────────────────────────────────
def search_item(item_name, session):
    """Search EQTraders for an item name and return item ID."""
    try:
        url = EQTRADERS_SEARCH.format(requests.utils.quote(item_name))
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Look for exact match in search results
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'show_item.php?item=' in href:
                link_text = link.get_text(strip=True)
                if link_text.lower() == item_name.lower():
                    m = re.search(r'item=(\d+)', href)
                    if m:
                        return m.group(1)

        # Fallback: first result
        for link in soup.find_all('a', href=True):
            if 'show_item.php?item=' in link['href']:
                m = re.search(r'item=(\d+)', link['href'])
                if m:
                    return m.group(1)

        return None
    except:
        return None

# ── SCRAPE ITEM SOURCES ───────────────────────────────────────────────────────
def scrape_item_sources(item_id, session):
    """Get source information for an item from its EQTraders page."""
    url = EQTRADERS_ITEM.format(item_id)
    result = {
        'item_id': item_id,
        'url': url,
        'vendor_sold': '',
        'vendor_zone': '',
        'dropped_zones': '',
        'foraged_zones': '',
        'fished_zones': '',
        'crafted': '',
        'notes': '',
        'error': ''
    }

    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator='\n')
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        vendor_zones = []
        dropped_zones = []
        foraged_zones = []
        fished_zones = []
        crafted_recipes = []

        in_sources = False
        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Detect sources section
            if 'sources:' in line_lower:
                in_sources = True
                continue

            # Stop at Full Recipe List section
            if 'full recipe list' in line_lower and in_sources:
                break

            if not in_sources:
                continue

            # Vendor sold
            if 'sold by' in line_lower or 'vendor' in line_lower or 'merchant' in line_lower:
                # Try to get vendor name and zone from this line or nearby
                vendor_zones.append(line)

            # Dropped
            elif 'dropped' in line_lower or 'looted' in line_lower:
                # Extract zone names
                zones = re.findall(r'in\s+([A-Z][^,\n]+?)(?:,|$)', line)
                if zones:
                    dropped_zones.extend(z.strip() for z in zones)
                else:
                    dropped_zones.append(line)

            # Foraged
            elif 'foraged' in line_lower or 'forage' in line_lower:
                zones = re.findall(r'in\s+([A-Z][^,\n]+?)(?:,|$)', line)
                if zones:
                    foraged_zones.extend(z.strip() for z in zones)
                else:
                    foraged_zones.append(line)

            # Fished
            elif 'fished' in line_lower or 'fishing' in line_lower:
                zones = re.findall(r'in\s+([A-Z][^,\n]+?)(?:,|$)', line)
                if zones:
                    fished_zones.extend(z.strip() for z in zones)
                else:
                    fished_zones.append(line)

        # Also check if it's crafted (has recipe)
        for line in lines:
            if 'to make' in line.lower() and not crafted_recipes:
                # Extract the crafting info
                m = re.search(r'To make .+?\((.+?trivial\s*\d+)\)', line, re.IGNORECASE)
                if m:
                    crafted_recipes.append(m.group(1))

        # Check if vendor sold (marked with * in recipe lists)
        page_text = soup.get_text()
        if '(*)' in page_text or 'vendor sold' in page_text.lower() or 'sold by' in page_text.lower():
            # Extract vendor names from links in Sources section
            sources_section = False
            for tag in soup.find_all(['p', 'li', 'td', 'div']):
                tag_text = tag.get_text(strip=True).lower()
                if 'sources' in tag_text:
                    sources_section = True
                if sources_section:
                    links_in_tag = tag.find_all('a')
                    for link in links_in_tag:
                        lt = link.get_text(strip=True)
                        if lt and len(lt) > 2 and len(lt) < 60:
                            if any(kw in tag.get_text().lower() for kw in ['vendor','merchant','sold','shop']):
                                vendor_zones.append(lt)

        # Compile results
        result['vendor_sold'] = 'Yes' if vendor_zones else ''
        result['vendor_zone'] = ' | '.join(dict.fromkeys(vendor_zones))[:200]  # dedupe, limit length
        result['dropped_zones'] = ' | '.join(dict.fromkeys(dropped_zones))[:200]
        result['foraged_zones'] = ' | '.join(dict.fromkeys(foraged_zones))[:200]
        result['fished_zones']  = ' | '.join(dict.fromkeys(fished_zones))[:200]
        result['crafted'] = ' | '.join(dict.fromkeys(crafted_recipes))[:200]

        # Determine primary source for quick reference
        sources = []
        if vendor_zones: sources.append('Vendor')
        if dropped_zones: sources.append('Dropped')
        if foraged_zones: sources.append('Foraged')
        if fished_zones: sources.append('Fished')
        if crafted_recipes: sources.append('Crafted')
        result['notes'] = ', '.join(sources) if sources else 'Check EQTraders'

        return result

    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
        return result

# ── PROGRESS ──────────────────────────────────────────────────────────────────
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

# ── CSV ───────────────────────────────────────────────────────────────────────
SOURCE_FIELDS = ['ingredient_name', 'item_id', 'primary_source',
                 'vendor_sold', 'vendor_zone',
                 'dropped_zones', 'foraged_zones', 'fished_zones',
                 'crafted', 'url', 'error']

def save_source(ingredient_name, data):
    file_exists = os.path.exists(SOURCES_CSV)
    with open(SOURCES_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=SOURCE_FIELDS)
        if not file_exists:
            writer.writeheader()
        row = {'ingredient_name': ingredient_name,
               'item_id': data.get('item_id',''),
               'primary_source': data.get('notes',''),
               'vendor_sold': data.get('vendor_sold',''),
               'vendor_zone': data.get('vendor_zone',''),
               'dropped_zones': data.get('dropped_zones',''),
               'foraged_zones': data.get('foraged_zones',''),
               'fished_zones': data.get('fished_zones',''),
               'crafted': data.get('crafted',''),
               'url': data.get('url',''),
               'error': data.get('error','')}
        writer.writerow(row)

# ── COMBINE WITH RECIPES ──────────────────────────────────────────────────────
def build_combined_csv():
    """Merge ingredient_sources into ingredients_ALL to create final file."""
    print("\nBuilding combined CSV with sources...")

    # Load sources lookup
    sources = {}
    if os.path.exists(SOURCES_CSV):
        with open(SOURCES_CSV, encoding='utf-8') as f:
            for row in csv.DictReader(f):
                sources[row['ingredient_name'].lower()] = row

    # Load recipes
    if not os.path.exists(INPUT_CSV):
        print("ingredients_ALL.csv not found!")
        return

    combined_fields = [
        'skill','name','trivial','expansion','vendor','container','trivial_site',
        'ingredient_1','src_1',
        'ingredient_2','src_2',
        'ingredient_3','src_3',
        'ingredient_4','src_4',
        'ingredient_5','src_5',
        'ingredient_6','src_6',
        'ingredient_7','src_7',
        'ingredient_8','src_8',
        'url'
    ]

    rows_out = []
    with open(INPUT_CSV, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            new_row = {k: row.get(k,'') for k in
                      ['skill','name','trivial','expansion','vendor',
                       'container','trivial_site','url']}
            for i in range(1, 9):
                ingr = row.get(f'ingredient_{i}','').strip()
                ingr_clean = re.sub(r'\s*\(\d+\)\s*$', '', ingr).strip()
                src_info = sources.get(ingr_clean.lower(), {})

                # Build compact source string
                src_parts = []
                if src_info.get('vendor_sold') == 'Yes':
                    vz = src_info.get('vendor_zone','')
                    src_parts.append(f"Vendor: {vz[:40]}" if vz else "Vendor sold")
                if src_info.get('dropped_zones'):
                    src_parts.append(f"Dropped: {src_info['dropped_zones'][:60]}")
                if src_info.get('foraged_zones'):
                    src_parts.append(f"Foraged: {src_info['foraged_zones'][:60]}")
                if src_info.get('fished_zones'):
                    src_parts.append(f"Fished: {src_info['fished_zones'][:60]}")
                if src_info.get('crafted'):
                    src_parts.append(f"Crafted: {src_info['crafted'][:40]}")

                new_row[f'ingredient_{i}'] = ingr
                new_row[f'src_{i}'] = ' / '.join(src_parts) if src_parts else ('Unknown' if ingr else '')

            rows_out.append(new_row)

    with open(COMBINED_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=combined_fields)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"  Final combined file: {COMBINED_CSV}")
    print(f"  {len(rows_out)} recipes with ingredient sources")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  EQ Ingredient Source Scraper — Round 2")
    print("=" * 60)

    # Get unique ingredients
    print(f"\nReading {INPUT_CSV}...")
    ingredients = get_unique_ingredients(INPUT_CSV)
    print(f"Found {len(ingredients)} unique ingredients to look up")

    # Load progress
    progress = load_progress()
    done = set(progress.keys())
    remaining = [i for i in ingredients if i not in done]

    print(f"Already done: {len(done)} | Remaining: {len(remaining)}")
    print(f"Estimated time: ~{round(len(remaining) * DELAY_SECONDS / 3600, 1)}h")
    print(f"Ctrl+C to pause, re-run to resume\n{'─'*60}\n")

    if not remaining:
        print("All ingredients already scraped! Building combined CSV...")
        build_combined_csv()
        return

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.eqtraders.com/',
    })

    try:
        for i, ingredient in enumerate(remaining):
            pct = round((len(done) + i + 1) / len(ingredients) * 100, 1)
            print(f"  [{pct}%] ({i+1}/{len(remaining)}) {ingredient[:50]}", end='', flush=True)

            # Search for item ID
            item_id = search_item(ingredient, session)
            time.sleep(DELAY_SECONDS * 0.4)  # short delay after search

            if item_id:
                data = scrape_item_sources(item_id, session)
                src = data.get('notes', 'not found')
                print(f" -> {src[:60]}")
            else:
                data = {'item_id': '', 'notes': 'not found on EQTraders',
                        'vendor_sold': '', 'vendor_zone': '', 'dropped_zones': '',
                        'foraged_zones': '', 'fished_zones': '', 'crafted': '',
                        'url': '', 'error': 'item not found in search'}
                print(f" -> not found in search")

            save_source(ingredient, data)
            progress[ingredient] = True
            save_progress(progress)
            time.sleep(DELAY_SECONDS)

        print("\n\nAll ingredients done! Building combined CSV...")
        build_combined_csv()
        print("\nDone! Upload ingredients_WITH_SOURCES.csv to Claude.")

    except KeyboardInterrupt:
        print("\n\n[PAUSED] Progress saved. Re-run to continue.")
        save_progress(progress)
        sys.exit(0)

if __name__ == '__main__':
    main()
