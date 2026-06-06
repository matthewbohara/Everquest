# Everquest
Various python scripts that might be helpful
The first batch of which are to help with tradeskills to go from 300 - 350
If you want to skip the build database option, you can use things like SoulBanshee's tool, but i wanted to make this as independent as possible;.
The final goal of this is just one spreadsheet that you can see everything you need , or if you already have the stuff to make the various recipes. 

Please reach out with any questions/comments
In game name is Darkmorte on The Rathe - Prexus

Full technical details below.

# EverQuest Tradeskill 350 Toolkit

A set of Python scripts to help EverQuest players identify missing tradeskill recipes needed to reach skill level 350, complete with ingredient lists and where to find them.

Built by the EQ community. Recipe data sourced from [EQTraders Corner](https://www.eqtraders.com) — huge thanks to Niami Denmother and all contributors there. Adetia's Path to 350 spreadsheets (Township Rebellion, Luclin server) were also invaluable in understanding the recipe structure.

---

## What This Does

1. **Builds a local recipe database** from EQTraders (run once, ~2-4 hours)
2. **Finds your missing recipes** by comparing against your EQ outputfiles (no third-party tools needed)
3. **Scrapes ingredient details** for every missing recipe (~8 hours, run overnight)
4. **Scrapes ingredient sources** — where to buy, drop, forage, fish, or craft each ingredient
5. **Uploads everything to Claude** (or any AI) to build a personalized Excel spreadsheet

---

## Requirements

- Python 3.8+
- `pip install requests beautifulsoup4 openpyxl`
- EverQuest (Live server)

---

## Quick Start

### Step 1 — Get your recipe outputfiles from EverQuest

In EverQuest, type these commands (one per tradeskill):
```
/outputfile recipes alchemy
/outputfile recipes baking
/outputfile recipes blacksmithing
/outputfile recipes brewing
/outputfile recipes fishing
/outputfile recipes fletching
/outputfile recipes jewelcrafting
/outputfile recipes poisonmaking
/outputfile recipes pottery
/outputfile recipes research
/outputfile recipes tailoring
/outputfile recipes tinkering
```

Find the output files in your EQ folder (usually `C:\Users\Public\Daybreak Game Company\Installed Games\EverQuest`). They'll be named like:
```
CharacterName_Server-Baking-Recipes.txt
CharacterName_Server-Alchemy-Recipes.txt
```

Copy all of them into the same folder as these scripts.

---

### Step 2 — Build the recipe database (one-time, ~2-4 hours)

```bash
python eq_build_database.py
```

This scrapes all tradeskill recipes from EQTraders and saves them locally in `eq_recipe_db/`. You only need to do this once — re-run if a new EQ expansion drops.

Press **Ctrl+C** at any time to pause. Re-run to resume where you left off.

---

### Step 3 — Find your missing recipes

```bash
python eq_find_missing.py
```

Compares your outputfiles against the database and writes:
- `missing_recipes/missing_ALL.csv` — all missing recipes
- `missing_recipes/missing_Baking.csv` — per-skill files
- `missing_recipes/summary.txt` — quick progress summary

---

### Step 4 — Scrape ingredients for missing recipes (~8 hours, run overnight)

```bash
python eq_scraper.py
```

Looks up ingredient details for every missing recipe on EQTraders.

Output: `scraped_ingredients/ingredients_ALL.csv`

Press **Ctrl+C** to pause. Re-run to resume.

---

### Step 5 — Scrape ingredient sources (~1-2 hours)

```bash
python eq_ingredient_sources.py
```

Looks up each unique ingredient and records where to get it:
- Vendor sold (vendor name + zone)
- Dropped (zone)
- Foraged (zone)
- Fished (zone)
- Crafted (subcombine)

Output: `scraped_ingredients/ingredients_WITH_SOURCES.csv`

---

### Step 6 — Build your spreadsheet

Upload `ingredients_WITH_SOURCES.csv` and your inventory outputfile to Claude (or use the included `eq_build_spreadsheet.py`):

```bash
python eq_build_spreadsheet.py
```

This builds a full Excel file with:
- All missing recipes per skill (color coded)
- Ingredients with source information
- Your inventory cross-referenced (green = have it, red = need it)
- Vendor-learnable recipes highlighted for easy wins

---

## Script Reference

| Script | Purpose | Runtime |
|--------|---------|---------|
| `eq_build_database.py` | Build local recipe DB from EQTraders | ~2-4h (one-time) |
| `eq_find_missing.py` | Find your missing recipes | Seconds |
| `eq_scraper.py` | Get ingredients for missing recipes | ~8h overnight |
| `eq_ingredient_sources.py` | Get where to find each ingredient | ~1-2h |
| `eq_build_spreadsheet.py` | Build final Excel spreadsheet | Seconds |

---

## Tips

- **All scripts resume automatically** if interrupted with Ctrl+C — just re-run
- **Progress is saved** after every recipe/item in the `scraped_ingredients/` folder
- **Multiple characters** are supported — just copy all their outputfiles into the folder
- **Re-run `eq_find_missing.py` anytime** after doing more combines to update your progress
- **Only re-run `eq_build_database.py`** when a new EQ expansion drops
- The scripts are **read-only** with respect to EverQuest — they don't touch any game files

---

## Notes on Data Accuracy

- Recipe data comes from EQTraders and may not include every recipe (especially very new ones)
- "Needed for 350" counts are estimates based on community research
- Some recipes are DNC (Do Not Count) or DNL (Do Not Learn) and won't help toward 350
- Alchemy recipes require a Shaman character (class-restricted)

---

## Contributing

PRs welcome! If EQTraders article IDs change with new expansions, update `SKILL_PAGES` in `eq_build_database.py`.

---

## Credits

- [EQTraders Corner](https://www.eqtraders.com) — Niami Denmother and contributors
- Adetia (Township Rebellion, Luclin) — Path to 350 spreadsheets
- Drewie (antonius server) — [EQRecipes site](http://eqrecipes.free.fr)
- Soulbanshee — original parser tool inspiration
