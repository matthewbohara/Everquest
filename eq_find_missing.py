"""
EverQuest Missing Recipe Finder
=================================
Replaces the Soulbanshee parser. Compares your EQ /outputfile recipes
against the local recipe database built by eq_build_database.py.

REQUIRES: eq_build_database.py to have been run first (builds eq_recipe_db/)

SETUP:
  1. In EverQuest, type: /outputfile recipes alchemy
     Repeat for each tradeskill (baking, blacksmithing, brewing, etc.)
  2. Find the output files in your EQ folder:
     <CharacterName>_<Server>-Alchemy-Recipes.txt etc.
  3. Copy them to this folder
  4. Run: python eq_find_missing.py

OUTPUT:
  missing_recipes/missing_ALL.csv        - all missing recipes combined
  missing_recipes/missing_Baking.csv     - per-skill missing recipes
  missing_recipes/summary.txt            - quick summary of progress

NOTES:
  - Character name and server are auto-detected from filenames
  - Works with multiple characters if you copy multiple outputfiles
  - Re-run anytime after making more combines to update progress
"""

import csv, json, os, sys, re, glob
from collections import defaultdict

SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER     = os.path.join(SCRIPT_FOLDER, 'eq_recipe_db')
OUTPUT_FOLDER = os.path.join(SCRIPT_FOLDER, 'missing_recipes')

DB_FILE       = os.path.join(DB_FOLDER, 'recipes_ALL.json')

SKILL_NAMES = [
    'Alchemy', 'Baking', 'Blacksmithing', 'Brewing', 'Fishing',
    'Fletching', 'Jewelry Making', 'Make Poison', 'Pottery',
    'Research', 'Tailoring', 'Tinkering'
]

# How many recipes needed for 350 per skill
NEEDED_FOR_350 = {
    'Alchemy': 562, 'Baking': 698, 'Blacksmithing': 1939, 'Brewing': 302,
    'Fishing': 122, 'Fletching': 876, 'Jewelry Making': 1279,
    'Make Poison': 543, 'Pottery': 2014, 'Research': 2570,
    'Tailoring': 2078, 'Tinkering': 791,
}

# ── FIND OUTPUTFILES ──────────────────────────────────────────────────────────
def find_outputfiles():
    """
    Auto-detect EQ recipe outputfiles in the script folder.
    Looks for files matching: *-Alchemy-Recipes.txt, *-Baking-Recipes.txt etc.
    Also accepts Soulbanshee parser output: Alchemy.txt, Baking.txt etc.
    """
    found = {}  # skill -> filepath

    # Pattern 1: EQ outputfiles (CharName_Server-Skill-Recipes.txt)
    for pattern in ['*-Recipes.txt', '*-recipes.txt']:
        for filepath in glob.glob(os.path.join(SCRIPT_FOLDER, pattern)):
            fname = os.path.basename(filepath)
            for skill in SKILL_NAMES:
                skill_slug = skill.replace(' ', '_').replace(' ', '')
                if (f'-{skill.replace(" ", "_")}-Recipes' in fname or
                    f'-{skill.replace(" ", "")}-Recipes' in fname or
                    f'-{skill.replace(" Making", "_Making")}-Recipes' in fname or
                    f'-Jewelry_Making-Recipes' in fname and skill == 'Jewelry Making' or
                    f'-Make_Poison-Recipes' in fname and skill == 'Make Poison'):
                    found[skill] = ('outputfile', filepath)

    # Pattern 2: Soulbanshee parser files (Alchemy.txt, Baking.txt etc.)
    for skill in SKILL_NAMES:
        slug = skill.replace(' ', '_')
        for fname in [f'{slug}.txt', f'{skill}.txt']:
            fpath = os.path.join(SCRIPT_FOLDER, fname)
            if os.path.exists(fpath) and skill not in found:
                found[skill] = ('parser', fpath)

    return found

# ── READ KNOWN RECIPES ────────────────────────────────────────────────────────
def read_known_recipes_outputfile(filepath):
    """Read EQ /outputfile recipes output — returns set of known recipe names."""
    known = set()
    with open(filepath, encoding='utf-8', errors='replace') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                name = parts[1].strip().lower()
                if name:
                    known.add(name)
    return known

def read_known_recipes_parser(filepath):
    """Read Soulbanshee parser output — returns set of known recipe names."""
    # Parser files list MISSING recipes, so we need the DB to invert
    # Actually for parser files, col 0 is the recipe name of MISSING recipes
    missing = set()
    with open(filepath, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                parts = list(csv.reader([line], delimiter='\t'))[0]
                name = parts[0].strip('"').lower()
                if name:
                    missing.add(name)
            except: pass
    return missing  # These are MISSING, not known

# ── LOAD DATABASE ─────────────────────────────────────────────────────────────
def load_database():
    if not os.path.exists(DB_FILE):
        print(f"ERROR: Database not found at {DB_FILE}")
        print("Run eq_build_database.py first!")
        sys.exit(1)
    with open(DB_FILE) as f:
        all_recipes = json.load(f)
    # Index by skill
    by_skill = defaultdict(list)
    for r in all_recipes:
        by_skill[r['skill']].append(r)
    return by_skill

# ── FIND MISSING ──────────────────────────────────────────────────────────────
def find_missing(skill, db_recipes, known_names, missing_names=None):
    """
    Compare database recipes against known recipes.
    Returns (missing, known) lists.
    """
    missing = []
    known_found = []

    for recipe in db_recipes:
        name_lower = recipe['name'].lower().strip()
        if not name_lower:
            continue

        if missing_names is not None:
            # Parser mode: missing_names contains what parser says is missing
            is_missing = name_lower in missing_names
        else:
            # Outputfile mode: known_names contains what you know
            is_missing = name_lower not in known_names

        if is_missing:
            missing.append(recipe)
        else:
            known_found.append(recipe)

    return missing, known_found

# ── WRITE CSV ─────────────────────────────────────────────────────────────────
FIELDS = ['skill', 'name', 'trivial', 'expansion', 'container',
          'ingredient_1', 'ingredient_2', 'ingredient_3', 'ingredient_4',
          'ingredient_5', 'ingredient_6', 'ingredient_7', 'ingredient_8',
          'recipe_id', 'notes']

def write_csv(filepath, recipes):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for r in recipes:
            ingredients = r.get('ingredients', [])
            row = {
                'skill':      r.get('skill', ''),
                'name':       r.get('name', ''),
                'trivial':    r.get('trivial', ''),
                'expansion':  r.get('expansion', ''),
                'container':  r.get('container', ''),
                'recipe_id':  r.get('recipe_id', ''),
                'notes':      r.get('notes', ''),
            }
            for i in range(1, 9):
                row[f'ingredient_{i}'] = ingredients[i-1] if i-1 < len(ingredients) else ''
            writer.writerow(row)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print("=" * 60)
    print("  EQ Missing Recipe Finder")
    print("=" * 60)

    # Load database
    print(f"\nLoading recipe database from {DB_FOLDER}...")
    db = load_database()
    total_in_db = sum(len(v) for v in db.values())
    print(f"  {total_in_db} total recipes in database")

    # Find outputfiles
    print(f"\nSearching for recipe outputfiles...")
    outputfiles = find_outputfiles()

    if not outputfiles:
        print("\nERROR: No recipe outputfiles found!")
        print("Make sure these files are in the same folder as this script:")
        print("  Option A (EQ outputfiles): CharName_Server-Baking-Recipes.txt etc.")
        print("  Option B (Soulbanshee):    Baking.txt, Alchemy.txt etc.")
        sys.exit(1)

    for skill, (ftype, fpath) in outputfiles.items():
        print(f"  Found [{skill}]: {os.path.basename(fpath)} ({ftype})")

    # Process each skill
    print(f"\nComparing against database...\n{'─'*60}")

    all_missing = []
    summary_lines = []
    summary_lines.append("EQ TRADESKILL 350 PROGRESS SUMMARY")
    summary_lines.append("=" * 50)

    for skill in SKILL_NAMES:
        db_recipes = db.get(skill, [])
        if not db_recipes:
            print(f"  [{skill}] No database entries — skipping")
            continue

        if skill not in outputfiles:
            print(f"  [{skill}] No outputfile found — skipping")
            summary_lines.append(f"{skill:20s}: no outputfile")
            continue

        ftype, fpath = outputfiles[skill]

        if ftype == 'outputfile':
            known = read_known_recipes_outputfile(fpath)
            missing, known_found = find_missing(skill, db_recipes, known)
        else:
            # Parser mode — missing_names is what parser says is missing
            missing_from_parser = read_known_recipes_parser(fpath)
            missing, known_found = find_missing(skill, db_recipes,
                                                known_names=None,
                                                missing_names=missing_from_parser)

        needed = NEEDED_FOR_350.get(skill, 0)
        learned = len(known_found)
        pct = round(learned / needed * 100, 1) if needed else 0
        still_need = max(0, needed - learned)

        print(f"  [{skill}]")
        print(f"    DB recipes:  {len(db_recipes)}")
        print(f"    You know:    {learned}")
        print(f"    Missing:     {len(missing)}")
        print(f"    Need for 350:{needed} ({pct}% there, need {still_need} more)")

        summary_lines.append(
            f"{skill:20s}: {learned:4d}/{needed:4d} learned ({pct:5.1f}%) | "
            f"{still_need:4d} still needed | {len(missing):4d} in DB missing"
        )

        # Write per-skill CSV
        skill_path = os.path.join(OUTPUT_FOLDER,
                                  f'missing_{skill.replace(" ","_")}.csv')
        write_csv(skill_path, missing)
        all_missing.extend(missing)

    # Write combined CSV
    combined_path = os.path.join(OUTPUT_FOLDER, 'missing_ALL.csv')
    write_csv(combined_path, all_missing)

    # Write summary
    summary_path = os.path.join(OUTPUT_FOLDER, 'summary.txt')
    summary_lines.append(f"\nTotal missing across all skills: {len(all_missing)}")
    with open(summary_path, 'w') as f:
        f.write('\n'.join(summary_lines))

    print(f"\n{'─'*60}")
    print(f"  Total missing recipes: {len(all_missing)}")
    print(f"  Output folder: {OUTPUT_FOLDER}")
    print(f"  Summary: {summary_path}")
    print(f"\nNext steps:")
    print(f"  1. Run eq_scraper.py to get ingredients for missing recipes")
    print(f"  2. Run eq_ingredient_sources.py to get where to find ingredients")
    print(f"  3. Upload the final CSV to Claude for the full spreadsheet!")

if __name__ == '__main__':
    main()
