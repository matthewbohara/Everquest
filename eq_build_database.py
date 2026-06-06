"""
EverQuest Recipe Database Builder
===================================
Scrapes ALL recipes from EQTraders.com by tradeskill and expansion,
building a local JSON database. Run this ONCE to create the database,
then use eq_find_missing.py to compare against your outputfiles.

No Soulbanshee parser needed after this!

SETUP:  pip install requests beautifulsoup4
USAGE:  python eq_build_database.py
        Ctrl+C to pause, re-run to resume

OUTPUT: eq_recipe_db/recipes_ALL.json
        eq_recipe_db/recipes_Baking.json  (one per skill)

NOTES:
  - Run once, database stays valid until a new EQ expansion drops
  - Takes ~2-4 hours (lots of pages but fewer than individual items)
  - Respects EQTraders with 2s delay between requests
"""

import json, os, time, sys, re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Run: pip install requests beautifulsoup4")
    sys.exit(1)

SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER     = os.path.join(SCRIPT_FOLDER, 'eq_recipe_db')
PROGRESS_FILE = os.path.join(DB_FOLDER, '_db_progress.json')
DELAY_SECONDS = 2.0
BASE_URL      = "https://www.eqtraders.com"

# ── EXPANSION PAGE URLS ───────────────────────────────────────────────────────
# Each skill has multiple expansion sub-pages on EQTraders
# Format: (article_id, expansion_name)
# These cover all expansions from Classic through current

SKILL_PAGES = {
    'Alchemy': [
        (33,   'Old World'), (114, 'Kunark'), (115, 'Velious'), (116, 'Luclin'),
        (117,  'PoP'), (118, 'GoD'), (119, 'OoW'), (120, 'DoD'), (121, 'PoR'),
        (122,  'TSS'), (123, 'TBS'), (124, 'SoF'), (125, 'SoD'), (126, 'HoT'),
        (127,  'VoA'), (128, 'RoF'), (129, 'CoTF'), (130, 'TDS'), (131, 'TBM'),
        (132,  'EoK'), (133, 'RoS'), (134, 'TBL'), (135, 'ToV'), (136, 'CoV'),
        (137,  'ToL'), (138, 'NoS'), (139, 'LS'),  (1713,'SoR'),
    ],
    'Baking': [
        (147,  'Old World'), (148, 'Kunark'), (149, 'Velious'), (150, 'Luclin'),
        (151,  'PoP'), (152, 'GoD'), (153, 'OoW'), (154, 'DoD'), (155, 'PoR'),
        (156,  'TSS'), (157, 'TBS'), (158, 'SoF'), (159, 'SoD'), (160, 'HoT'),
        (161,  'VoA'), (162, 'RoF'), (163, 'CoTF'),(164, 'TDS'), (165, 'TBM'),
        (166,  'EoK'), (167, 'RoS'), (168, 'TBL'), (169, 'ToV'), (170, 'CoV'),
        (171,  'ToL'), (172, 'NoS'), (173, 'LS'),  (1712,'SoR'), (378, 'Other'),
    ],
    'Blacksmithing': [
        (179,  'Old World'), (180, 'Kunark'), (181, 'Velious'), (182, 'Luclin'),
        (183,  'PoP'), (184, 'GoD'), (185, 'OoW'), (186, 'DoD'), (187, 'PoR'),
        (188,  'TSS'), (189, 'TBS'), (190, 'SoF'), (191, 'SoD'), (192, 'HoT'),
        (193,  'VoA'), (194, 'RoF'), (195, 'CoTF'),(196, 'TDS'), (197, 'TBM'),
        (198,  'EoK'), (199, 'RoS'), (200, 'TBL'), (201, 'ToV'), (202, 'CoV'),
        (203,  'ToL'), (204, 'NoS'), (205, 'LS'),  (206, 'SoR'),
    ],
    'Brewing': [
        (211,  'Old World'), (212, 'Kunark'), (213, 'Velious'), (214, 'Luclin'),
        (215,  'PoP'), (216, 'GoD'), (217, 'OoW'), (218, 'DoD'), (219, 'PoR'),
        (220,  'TSS'), (221, 'TBS'), (222, 'SoF'), (223, 'SoD'), (224, 'HoT'),
        (225,  'VoA'), (226, 'RoF'), (227, 'CoTF'),(228, 'TDS'), (229, 'TBM'),
        (230,  'EoK'), (231, 'RoS'), (232, 'TBL'), (233, 'ToV'), (234, 'CoV'),
        (235,  'ToL'), (236, 'NoS'), (237, 'LS'),  (238, 'SoR'),
    ],
    'Fishing': [
        (243,  'Old World'), (244, 'Kunark'), (245, 'Velious'), (246, 'Luclin'),
        (247,  'PoP'), (248, 'GoD'), (249, 'OoW'), (250, 'DoD'), (251, 'PoR'),
        (252,  'TSS'), (253, 'TBS'), (254, 'SoF'), (255, 'SoD'), (256, 'HoT'),
        (257,  'VoA'), (258, 'RoF'), (259, 'CoTF'),(260, 'TDS'), (261, 'TBM'),
        (262,  'EoK'), (263, 'RoS'), (264, 'TBL'), (265, 'ToV'), (266, 'CoV'),
        (267,  'ToL'), (268, 'NoS'), (269, 'LS'),  (270, 'SoR'),
    ],
    'Fletching': [
        (275,  'Old World'), (276, 'Kunark'), (277, 'Velious'), (278, 'Luclin'),
        (279,  'PoP'), (280, 'GoD'), (281, 'OoW'), (282, 'DoD'), (283, 'PoR'),
        (284,  'TSS'), (285, 'TBS'), (286, 'SoF'), (287, 'SoD'), (288, 'HoT'),
        (289,  'VoA'), (290, 'RoF'), (291, 'CoTF'),(292, 'TDS'), (293, 'TBM'),
        (294,  'EoK'), (295, 'RoS'), (296, 'TBL'), (297, 'ToV'), (298, 'CoV'),
        (299,  'ToL'), (300, 'NoS'), (301, 'LS'),  (302, 'SoR'),
    ],
    'Jewelry Making': [
        (307,  'Old World'), (308, 'Kunark'), (309, 'Velious'), (310, 'Luclin'),
        (311,  'PoP'), (312, 'GoD'), (313, 'OoW'), (314, 'DoD'), (315, 'PoR'),
        (316,  'TSS'), (317, 'TBS'), (318, 'SoF'), (319, 'SoD'), (320, 'HoT'),
        (321,  'VoA'), (322, 'RoF'), (323, 'CoTF'),(324, 'TDS'), (325, 'TBM'),
        (326,  'EoK'), (327, 'RoS'), (328, 'TBL'), (329, 'ToV'), (330, 'CoV'),
        (331,  'ToL'), (332, 'NoS'), (333, 'LS'),  (334, 'SoR'),
    ],
    'Make Poison': [
        (339,  'Old World'), (340, 'Kunark'), (341, 'Velious'), (342, 'Luclin'),
        (343,  'PoP'), (344, 'GoD'), (345, 'OoW'), (346, 'DoD'), (347, 'PoR'),
        (348,  'TSS'), (349, 'TBS'), (350, 'SoF'), (351, 'SoD'), (352, 'HoT'),
        (353,  'VoA'), (354, 'RoF'), (355, 'CoTF'),(356, 'TDS'), (357, 'TBM'),
        (358,  'EoK'), (359, 'RoS'), (360, 'TBL'), (361, 'ToV'), (362, 'CoV'),
        (363,  'ToL'), (364, 'NoS'), (365, 'LS'),  (366, 'SoR'),
    ],
    'Pottery': [
        (371,  'Old World'), (372, 'Kunark'), (373, 'Velious'), (374, 'Luclin'),
        (375,  'PoP'), (376, 'GoD'), (377, 'OoW'), (378, 'DoD'), (379, 'PoR'),
        (380,  'TSS'), (381, 'TBS'), (382, 'SoF'), (383, 'SoD'), (384, 'HoT'),
        (385,  'VoA'), (386, 'RoF'), (387, 'CoTF'),(388, 'TDS'), (389, 'TBM'),
        (390,  'EoK'), (391, 'RoS'), (392, 'TBL'), (393, 'ToV'), (394, 'CoV'),
        (395,  'ToL'), (396, 'NoS'), (397, 'LS'),  (398, 'SoR'),
    ],
    'Research': [
        (403,  'Old World'), (404, 'Kunark'), (405, 'Velious'), (406, 'Luclin'),
        (407,  'PoP'), (408, 'GoD'), (409, 'OoW'), (410, 'DoD'), (411, 'PoR'),
        (412,  'TSS'), (413, 'TBS'), (414, 'SoF'), (415, 'SoD'), (416, 'HoT'),
        (417,  'VoA'), (418, 'RoF'), (419, 'CoTF'),(420, 'TDS'), (421, 'TBM'),
        (422,  'EoK'), (423, 'RoS'), (424, 'TBL'), (425, 'ToV'), (426, 'CoV'),
        (427,  'ToL'), (428, 'NoS'), (429, 'LS'),  (430, 'SoR'),
    ],
    'Tailoring': [
        (435,  'Old World'), (436, 'Kunark'), (437, 'Velious'), (438, 'Luclin'),
        (439,  'PoP'), (440, 'GoD'), (441, 'OoW'), (442, 'DoD'), (443, 'PoR'),
        (444,  'TSS'), (445, 'TBS'), (446, 'SoF'), (447, 'SoD'), (448, 'HoT'),
        (449,  'VoA'), (450, 'RoF'), (451, 'CoTF'),(452, 'TDS'), (453, 'TBM'),
        (454,  'EoK'), (455, 'RoS'), (456, 'TBL'), (457, 'ToV'), (458, 'CoV'),
        (459,  'ToL'), (460, 'NoS'), (461, 'LS'),  (462, 'SoR'),
    ],
    'Tinkering': [
        (467,  'Old World'), (468, 'Kunark'), (469, 'Velious'), (470, 'Luclin'),
        (471,  'PoP'), (472, 'GoD'), (473, 'OoW'), (474, 'DoD'), (475, 'PoR'),
        (476,  'TSS'), (477, 'TBS'), (478, 'SoF'), (479, 'SoD'), (480, 'HoT'),
        (481,  'VoA'), (482, 'RoF'), (483, 'CoTF'),(484, 'TDS'), (485, 'TBM'),
        (486,  'EoK'), (487, 'RoS'), (488, 'TBL'), (489, 'ToV'), (490, 'CoV'),
        (491,  'ToL'), (492, 'NoS'), (493, 'LS'),  (494, 'SoR'),
    ],
}

# ── PAGE SCRAPER ──────────────────────────────────────────────────────────────
def scrape_recipe_page(article_id, skill, expansion, session):
    """Scrape one EQTraders recipe page and return list of recipe dicts."""
    url = (f"{BASE_URL}/recipes/recipe_page.php"
           f"?article={article_id}&rsa={skill.replace(' ','%20')}"
           f"&sb=item&menustr=080020000000")
    recipes = []

    try:
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator='\n')

        # EQTraders recipe pages list recipes in a table or as structured text
        # Each recipe block contains:
        # - Item name (in a link or bold)
        # - Components: Item1, Item2...
        # - In: Container
        # - Trivial at: N
        # - EQRecipeID: N (when available)

        current_recipe = None

        for line in [l.strip() for l in text.split('\n') if l.strip()]:

            # Detect EQRecipeID line — marks start of a recipe
            recipe_id_match = re.search(r'EQRecipeID:\s*(\d+)', line)
            if recipe_id_match:
                if current_recipe:
                    recipes.append(current_recipe)
                current_recipe = {
                    'recipe_id': recipe_id_match.group(1),
                    'name': '',
                    'trivial': '',
                    'expansion': expansion,
                    'skill': skill,
                    'container': '',
                    'ingredients': [],
                    'notes': ''
                }
                # Extract "Learned as: Name" if present
                learned_match = re.search(r'Learned as:\s*(.+?)(?:\s*·|$)', line)
                if learned_match:
                    current_recipe['name'] = learned_match.group(1).strip()
                continue

            if current_recipe is None:
                continue

            # Recipe name — look for it before components line
            comp_match = re.match(
                r'^(?:' + '|'.join(['Alchemy','Baking','Blacksmithing','Brewing',
                'Fishing','Fletching','Jewelry','Poison','Pottery',
                'Research','Tailoring','Tinkering']) + r')\s+[Cc]omponents?:\s*(.+)',
                line, re.IGNORECASE)

            if comp_match:
                comp_text = comp_match.group(1)
                # Split on comma but not inside parens
                parts = re.split(r',\s*(?![^()]*\))', comp_text)
                for p in parts:
                    p = p.strip()
                    if p and len(p) < 80:
                        current_recipe['ingredients'].append(p)
                continue

            if line.lower().startswith('in:') and not current_recipe['container']:
                current_recipe['container'] = line[3:].strip().split(',')[0].strip()
                continue

            if 'trivial at:' in line.lower() and not current_recipe['trivial']:
                m = re.search(r'trivial at:\s*(\d+)', line, re.IGNORECASE)
                if m:
                    current_recipe['trivial'] = m.group(1)
                continue

            # Try to get recipe name from item name lines (before components)
            if (not current_recipe['ingredients'] and
                not current_recipe['name'] and
                len(line) < 80 and
                not any(skip in line.lower() for skip in
                    ['click','sort','trivial','class','race','wt:','size:',
                     'recipe','component','yield','notes','effect','required',
                     'charges','recommended','stackable','magic','lore','nodrop'])):
                # Likely a recipe name
                current_recipe['name'] = line

        # Don't forget last recipe
        if current_recipe and current_recipe.get('ingredients'):
            recipes.append(current_recipe)

        return recipes, url

    except requests.exceptions.RequestException as e:
        return [], url

# ── PROGRESS ──────────────────────────────────────────────────────────────────
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

# ── DATABASE ──────────────────────────────────────────────────────────────────
def load_db(skill):
    path = os.path.join(DB_FOLDER, f'recipes_{skill.replace(" ","_")}.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def save_db(skill, recipes):
    path = os.path.join(DB_FOLDER, f'recipes_{skill.replace(" ","_")}.json')
    with open(path, 'w') as f:
        json.dump(recipes, f, indent=2)

def save_combined_db(all_recipes):
    path = os.path.join(DB_FOLDER, 'recipes_ALL.json')
    with open(path, 'w') as f:
        json.dump(all_recipes, f, indent=2)
    print(f"\n  Master database saved: {path}")
    print(f"  Total recipes: {len(all_recipes)}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(DB_FOLDER, exist_ok=True)
    print("=" * 60)
    print("  EQ Recipe Database Builder")
    print("  Scraping all recipes from EQTraders by expansion")
    print("=" * 60)
    print(f"\nDelay: {DELAY_SECONDS}s | Ctrl+C to pause | Re-run to resume\n")

    progress = load_progress()

    total_pages = sum(len(pages) for pages in SKILL_PAGES.values())
    done_pages  = sum(1 for k, v in progress.items()
                      if isinstance(v, bool) and v)
    print(f"  Total pages to scrape: {total_pages}")
    print(f"  Already done: {done_pages}")
    print(f"  Remaining: {total_pages - done_pages}")
    print(f"  Est. time: ~{round((total_pages - done_pages) * DELAY_SECONDS / 3600, 1)}h\n")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.eqtraders.com/',
    })

    all_recipes = []

    try:
        for skill, pages in SKILL_PAGES.items():
            skill_recipes = load_db(skill)  # load any already-saved recipes
            print(f"\n[{skill}] {len(pages)} expansion pages")

            for article_id, expansion in pages:
                page_key = f"{skill}_{article_id}"
                if progress.get(page_key):
                    print(f"  ✓ {expansion} (cached)")
                    continue

                print(f"  Scraping {expansion}...", end='', flush=True)
                recipes, url = scrape_recipe_page(article_id, skill, expansion, session)

                print(f" {len(recipes)} recipes")
                skill_recipes.extend(recipes)

                progress[page_key] = True
                save_progress(progress)
                save_db(skill, skill_recipes)

                time.sleep(DELAY_SECONDS)

            all_recipes.extend(skill_recipes)
            print(f"  [{skill}] total: {len(skill_recipes)} recipes")

        save_combined_db(all_recipes)
        print("\nDatabase complete! Run eq_find_missing.py next.")

    except KeyboardInterrupt:
        print("\n\n[PAUSED] Progress saved. Re-run to continue.")
        save_progress(progress)
        # Save what we have so far
        save_combined_db(all_recipes)
        sys.exit(0)

if __name__ == '__main__':
    main()
