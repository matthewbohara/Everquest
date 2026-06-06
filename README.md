# Everquest
Various python scripts that might be helpful
The first batch of which are to help with tradeskills to go from 300 - 350
If you want to skip the build database option, you can use things like SoulBanshee's tool, but i wanted to make this as independent as possible;.
The final goal of this is just one spreadsheet that you can see everything you need , or if you already have the stuff to make the various recipes. 

Please reach out with any questions/comments
In game name is Darkmorte on The Rathe - Prexus

Full technical details below.

*** Note, some of these can run in parallel, this is mentioned below but i figured i would put it here as well
Terminal 1: eq_build_database.py
Terminal 2: eq_scraper.py          ← start at same time as above

(wait for both to finish)

Terminal 1: eq_find_missing.py     ← seconds, finishes instantly
Terminal 2: eq_ingredient_sources.py

(wait for sources to finish)

python eq_build_spreadsheet.py     ← seconds, finishes instantly

# EverQuest Tradeskill 350 Toolkit

> **⚠️ Work in Progress**
> | Script | Status |
> |--------|--------|
> | `eq_scraper.py` | ✅ Verified working |
> | `eq_ingredient_sources.py` | ✅ Ready (follows same pattern as scraper) |
> | `eq_build_database.py` | 🧪 In active testing |
> | `eq_find_missing.py` | 🧪 In active testing |
> | `eq_build_spreadsheet.py` | ✅ Ready |
>
> Bug reports and contributions are very welcome — open an issue or PR!

A set of Python scripts to help EverQuest players identify missing tradeskill recipes needed to reach skill level 350, complete with ingredient lists and where to find them.

Built by the EQ community. Recipe data sourced from [EQTraders Corner](https://www.eqtraders.com) — huge thanks to Niami Denmother and all contributors there. Adetia's Path to 350 spreadsheets (Township Rebellion, Luclin server) were also invaluable in understanding the recipe structure.

---

## What This Does

1. **Builds a local recipe database** from EQTraders (run once, ~2-4 hours)
2. **Finds your missing recipes** by comparing against your EQ outputfiles (no third-party tools needed)
3. **Scrapes ingredient details** for every missing recipe (~8 hours, run overnight)
4. **Scrapes ingredient sources** — where to buy, drop, forage, fish, or craft each ingredient
5. **Builds a personalized Excel spreadsheet** locally — no AI or external tools needed

---

## Requirements

### Python
- **Python 3.8 or higher** — download from [python.org](https://www.python.org/downloads/)
  - During install on Windows, check **"Add Python to PATH"**
  - Verify install: open a terminal and type `python --version`

### Python packages
Install all dependencies in one command:
```bash
pip install requests beautifulsoup4 openpyxl
```

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | 2.28.0+ | HTTP requests to EQTraders |
| `beautifulsoup4` | 4.11.0+ | HTML parsing of recipe pages |
| `openpyxl` | 3.0.10+ | Building the final Excel spreadsheet |

All other imports (`csv`, `json`, `os`, `sys`, `re`, `glob`, `time`) are part of Python's standard library — no extra install needed.

### Other
- EverQuest (Live server) with tradeskill outputfiles
- Internet connection (for scraping EQTraders)

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

> **Tip — Including your Tradeskill Depot in inventory:**
> When running `/outputfile inventory`, your Tradeskill Depot will automatically be included **if you have it open** at the time. To ensure it's loaded, visit a bank, open your Tradeskill Depot window, then run the command. This gives the most complete inventory cross-reference when building your spreadsheet.

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

### Running scripts in parallel
`eq_build_database.py` and `eq_scraper.py` can run **at the same time** in separate terminal windows — they write to different folders and don't interfere with each other:
- `eq_build_database.py` → `eq_recipe_db/`
- `eq_scraper.py` → `scraped_ingredients/`

If running both simultaneously, consider increasing the delay in `eq_build_database.py` from `2.0` to `3.0` seconds to be polite to EQTraders (open the script in a text editor and change `DELAY_SECONDS = 2.0` near the top).

Similarly, `eq_ingredient_sources.py` can run at the same time as `eq_build_database.py` once `eq_scraper.py` has finished.

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
