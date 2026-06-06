# EverQuest Tradeskill 350 Toolkit

> A set of Python scripts to help EverQuest players identify missing tradeskill recipes needed to reach skill level 350 — complete with ingredient lists and where to find them.
>
> Built by the EQ community. Recipe data sourced from [EQTraders Corner](https://www.eqtraders.com) — huge thanks to Niami Denmother and all contributors there. Adetia's Path to 350 spreadsheets (Township Rebellion, Luclin server) were also invaluable in understanding the recipe structure.
>
> Questions? Reach out to **Darkmorte** on The Rathe/Prexus server, or open an issue here.

---

## ⚠️ Work in Progress

| Script | Status |
|---|---|
| `eq_scraper.py` | ✅ Verified working |
| `eq_ingredient_sources.py` | ✅ Ready |
| `eq_build_database.py` | 🧪 In active testing |
| `eq_find_missing.py` | 🧪 In active testing |
| `eq_build_spreadsheet.py` | ✅ Ready |

Bug reports and contributions are very welcome — open an issue or PR!

---

## Pipeline Overview

The scripts must run in a specific order, but some can run **in parallel** to save time. Here's the full picture:

```
┌─────────────────────────────┐     ┌──────────────────────────────┐
│   eq_build_database.py      │     │      eq_scraper.py           │
│   (~2-4 hours, one-time)    │     │      (~8 hours, overnight)   │
│                             │     │                              │
│   → eq_recipe_db/           │     │   → scraped_ingredients/     │
│                             │     │     ingredients_ALL.csv      │
└────────────┬────────────────┘     └──────────────┬───────────────┘
             │                                      │
             │  ✅ Can run simultaneously            │
             │     (different output folders)       │
             │                                      │
             ▼                                      ▼
┌─────────────────────────────┐     ┌──────────────────────────────┐
│   eq_find_missing.py        │     │   eq_ingredient_sources.py   │
│   (seconds)                 │     │   (~1-2 hours)               │
│                             │     │                              │
│   → missing_recipes/        │     │   → ingredients_WITH_        │
│     missing_ALL.csv etc.    │     │     SOURCES.csv              │
└─────────────────────────────┘     └──────────────┬───────────────┘
                                                   │
                          ┌────────────────────────┘
                          │
                          ▼
             ┌────────────────────────┐
             │   eq_build_spreadsheet │
             │   (seconds)            │
             │                        │
             │   → YourName_          │
             │     Tradeskills.xlsx   │
             └────────────────────────┘
```

### Parallel running rules

| Can run together? | Scripts |
|---|---|
| ✅ Yes | `eq_build_database.py` + `eq_scraper.py` |
| ✅ Yes | `eq_build_database.py` + `eq_ingredient_sources.py` |
| ❌ No | `eq_scraper.py` must finish **before** `eq_ingredient_sources.py` |
| ❌ No | `eq_ingredient_sources.py` must finish **before** `eq_build_spreadsheet.py` |
| ❌ No | `eq_build_database.py` must finish **before** `eq_find_missing.py` |

### Recommended terminal layout

**Terminal 1** and **Terminal 2** — start these at the same time:
```
Terminal 1: python eq_build_database.py
Terminal 2: python eq_scraper.py
```

**After both finish**, start these (can also run simultaneously):
```
Terminal 1: python eq_find_missing.py
Terminal 2: python eq_ingredient_sources.py
```

**After sources finish:**
```
python eq_build_spreadsheet.py
```

> **Tip:** If running `eq_build_database.py` and `eq_scraper.py` simultaneously, consider increasing the delay in `eq_build_database.py` from `2.0` to `3.0` seconds to be polite to EQTraders (open the script and change `DELAY_SECONDS = 2.0` near the top).

---

## Requirements

### Python

Python 3.8 or higher — [download from python.org](https://www.python.org/downloads/)

- During install on Windows, check **"Add Python to PATH"**
- Verify install: open a terminal and type `python --version`

### Python packages

Install all dependencies in one command:

```
pip install requests beautifulsoup4 openpyxl
```

| Package | Version | Purpose |
|---|---|---|
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

> **Tip — Including your Tradeskill Depot in inventory:** When running `/outputfile inventory`, your Tradeskill Depot will automatically be included if you have it open at the time. To ensure it's loaded, visit a bank, open your Tradeskill Depot window, then run the command. This gives the most complete inventory cross-reference when building your spreadsheet.

---

### Step 2 — Build the recipe database (one-time, ~2-4 hours)

```
python eq_build_database.py
```

Scrapes all tradeskill recipes from EQTraders and saves them locally in `eq_recipe_db/`. You only need to do this once — re-run if a new EQ expansion drops.

Press `Ctrl+C` at any time to pause. Re-run to resume where you left off.

---

### Step 3 — Find your missing recipes

```
python eq_find_missing.py
```

Compares your outputfiles against the database and writes:

- `missing_recipes/missing_ALL.csv` — all missing recipes
- `missing_recipes/missing_Baking.csv` — per-skill files
- `missing_recipes/summary.txt` — quick progress summary

---

### Step 4 — Scrape ingredients for missing recipes (~8 hours, run overnight)

```
python eq_scraper.py
```

Looks up ingredient details for every missing recipe on EQTraders.

**Output:** `scraped_ingredients/ingredients_ALL.csv`

Press `Ctrl+C` to pause. Re-run to resume.

---

### Step 5 — Scrape ingredient sources (~1-2 hours)

```
python eq_ingredient_sources.py
```

Looks up each unique ingredient and records where to get it:

- Vendor sold (vendor name + zone)
- Dropped (zone)
- Foraged (zone)
- Fished (zone)
- Crafted (subcombine)

**Output:** `scraped_ingredients/ingredients_WITH_SOURCES.csv`

---

### Step 6 — Build your spreadsheet

```
python eq_build_spreadsheet.py
```

Builds a full Excel file with:

- All missing recipes per skill (color coded)
- Ingredients with source information
- Your inventory cross-referenced (green = have it, red = need it)
- Vendor-learnable recipes highlighted for easy wins

---

## Script Reference

| Script | Purpose | Runtime |
|---|---|---|
| `eq_build_database.py` | Build local recipe DB from EQTraders | ~2-4h (one-time) |
| `eq_find_missing.py` | Find your missing recipes | Seconds |
| `eq_scraper.py` | Get ingredients for missing recipes | ~8h overnight |
| `eq_ingredient_sources.py` | Get where to find each ingredient | ~1-2h |
| `eq_build_spreadsheet.py` | Build final Excel spreadsheet | Seconds |

---

## Tips

- All scripts resume automatically if interrupted with `Ctrl+C` — just re-run
- Progress is saved after every recipe/item in the `scraped_ingredients/` folder
- Multiple characters are supported — just copy all their outputfiles into the folder
- Re-run `eq_find_missing.py` anytime after doing more combines to update your progress
- Only re-run `eq_build_database.py` when a new EQ expansion drops
- The scripts are read-only with respect to EverQuest — they don't touch any game files

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
- **Adetia** (Township Rebellion, Luclin) — Path to 350 spreadsheets
- **Drewie** (Antonius server) — EQRecipes site
- **Soulbanshee** — original parser tool inspiration
