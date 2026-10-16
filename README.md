# Pantry Cooking Assistant

A local Streamlit cooking app that combines pantry tracking, AI recipes, reminders, shopping, favorites, meal planning, and a food memory game.

Search for any dish, even with an empty pantry, or use your ingredients as inspiration. Recipes are generated locally through Ollama and appear progressively as they are written.

## Version 1 features

- **My Pantry:** searchable grocery categories, ingredient aliases, saved ingredients, and editable dates.
- **Reminders:** Fresh items default to 7 days and Dry goods to 10 days after the added date. Due reminders appear inside the app and can be postponed.
- **AI Chef:** cuisine and food preferences, a 10–120 minute preferred cooking-time slider, beginner instructions, quantities, and estimated nutrition.
- **Streaming:** recipe text appears while Ollama generates it. Tools become available after the response finishes.
- **Recipe actions:** Markdown download, one YouTube search action, and an editable shopping draft.
- **Favorites:** persistent recipes with name search, food type, cuisine, and gluten-status filters; labels and names can be corrected and recipes removed.
- **Meal Planner:** choose any date for breakfast, lunch, or dinner. Add a custom meal, your latest AI recipe, or a favorite. Edit, replace, remove, and download the weekly plan.
- **Food Match:** 4 × 4 memory game with randomized food categories, revealed food names, move tracking, a best-moves display, jokes, and balloons.
- **Design:** cooking colors, grocery category tabs, a top emoji row, and decorative floating groceries.

## What makes this project different

The app connects recipe discovery to everyday kitchen organization. Users can remember what they own, prioritize compatible ingredients with due reminders, review a shopping draft, and schedule a meal without saving it to Favorites first. The food game also helps children recognize food names.

Pantry availability is a reference, not a strict recipe gate. A request for mutton curry should remain a mutton recipe even when mutton must be purchased. These behaviors are requested through the prompt; model output still needs review.

## Technology

Python · Streamlit · SQLite · Requests · Ollama · Qwen 2.5 7B · HTML/CSS · Git

The old curated `recipes.json` is no longer required. The searchable grocery catalog remains in Python.


# Pantry Cooking Assistant

A local Streamlit cooking app that combines pantry tracking, AI recipes, reminders, shopping, favorites, meal planning, and a food memory game.

Search for any dish, even with an empty pantry, or use your ingredients as inspiration. Recipes are generated locally through Ollama and appear progressively as they are written.

## Version 1 features

- **My Pantry:** searchable grocery categories, ingredient aliases, saved ingredients, and editable dates.
- **Reminders:** Fresh items default to 7 days and Dry goods to 10 days after the added date. Due reminders appear inside the app and can be postponed.
- **AI Chef:** cuisine and food preferences, a 10–120 minute preferred cooking-time slider, beginner instructions, quantities, and estimated nutrition.
- **Streaming:** recipe text appears while Ollama generates it. Tools become available after the response finishes.
- **Recipe actions:** Markdown download, one YouTube search action, and an editable shopping draft.
- **Favorites:** persistent recipes with name search, food type, cuisine, and gluten-status filters; labels and names can be corrected and recipes removed.
- **Meal Planner:** choose any date for breakfast, lunch, or dinner. Add a custom meal, your latest AI recipe, or a favorite. Edit, replace, remove, and download the weekly plan.
- **Food Match:** 4 × 4 memory game with randomized food categories, revealed food names, move tracking, a best-moves display, jokes, and balloons.
- **Design:** cooking colors, grocery category tabs, a top emoji row, and decorative floating groceries.

## What makes this project different

The app connects recipe discovery to everyday kitchen organization. Users can remember what they own, prioritize compatible ingredients with due reminders, review a shopping draft, and schedule a meal without saving it to Favorites first. The food game also helps children recognize food names.

Pantry availability is a reference, not a strict recipe gate. A request for mutton curry should remain a mutton recipe even when mutton must be purchased. These behaviors are requested through the prompt; model output still needs review.

## Technology

Python · Streamlit · SQLite · Requests · Ollama · Qwen 2.5 7B · HTML/CSS · Git

The old curated `recipes.json` is no longer required. The searchable grocery catalog remains in Python.

## Local setup on Windows

Install Python, Git, and Ollama first. The project was developed using a Windows PowerShell virtual environment.

```powershell
git clone https://github.com/jayanthkota20/Pantry-cooking-assistant.git
cd Pantry-cooking-assistant
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen2.5:7b
```

Using the virtual environment's Python directly avoids requiring PowerShell activation.

### Start Ollama

Open the Ollama desktop app **or** run the server in a separate terminal. Do not run two servers on the same port.

```powershell
ollama serve
```

The development machine produced unrelated and repetitive output with its Intel Arc integrated GPU through Vulkan. CPU mode produced more relevant output in comparison tests. To reproduce that working setup, quit the desktop server first, then run:

```powershell
$env:OLLAMA_VULKAN = "0"
$env:OLLAMA_IGPU_ENABLE = "0"
ollama serve
```

These variables apply to that terminal session. This is a machine-specific workaround, not a claim that all Intel GPUs fail.

### Start Streamlit

In another terminal, from the project folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

### Configuration

The current AI configuration is in `ai_chef.py`:

```python
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"
```

`requirements.txt` should include `streamlit` and `requests`. SQLite and the other Python utilities used here are included with Python. Ollama and its model are installed separately.

## Main files

| File | Responsibility |
| --- | --- |
| `app.py` | Main tabs, grocery catalog, pantry operations, reminders, and UI styling |
| `ai_chef.py` | Prompt, streamed Ollama response, recipe title, download, YouTube, shopping handoff |
| `favorites.py` | Favorite storage, automatic labels, filters, corrections, and removal |
| `meal_planner.py` | Custom/AI/favorite meal snapshots, calendar dates, editing, weekly download |
| `shopping.py` | Persistent shopping checklist |
| `food_game.py` | Randomized matching game and session score |
| `.streamlit/config.toml` | Streamlit theme |
| `pantry.db` | Locally created application data; do not commit |

## Everyday workflow

1. Add pantry ingredients and review their reminder dates.
2. Open AI Chef and name a dish or describe a meal. Select a compatible food preference.
3. Read the streamed answer after generation finishes. Review its ingredients, quantities, and steps.
4. Download or save the recipe; review the shopping draft before adding items.
5. In Meal Planner, choose Custom meal, Latest AI recipe, or Favorite. Pick any date and meal slot.
6. Save, edit, or remove meals. Saving a date outside the displayed week opens that date's week.

## Data and persistence

Pantry, shopping, favorites, and meal plans are stored locally in `pantry.db`. Meal plans save independent recipe copies, so deleting a favorite does not delete an already-planned meal.

The current AI answer and game state use Streamlit session state. They may reset after a browser/session or server restart. Best moves is a session record, not a permanent leaderboard.

The app is a local single-user prototype without accounts or per-user data isolation.

## Validation and limitations

The developer reported completing functional checks on October 16, 2026. Helper checks during development covered recipe-title formats, stream completion/error cases, and planner persistence, replacement, deletion, downloads, and week boundaries. This is not a comprehensive automated test suite or independent safety assessment.

- On the development laptop, Qwen 2.5 7B on CPU took roughly 90 seconds for a detailed app recipe. Streaming improves visibility, not necessarily total generation speed.
- Prompts cannot guarantee that a recipe respects every dietary, timing, quantity, or cooking constraint.
- Nutrition is estimated by the language model, not calculated from a verified ingredient database.
- Gluten status defaults to Not checked. Automatic food/cuisine labels are suggestions that users can correct.
- Reminder dates are organizational prompts, not expiry dates or a food-safety assessment. Notifications appear only while using the app.
- YouTube opens search results; it does not provide a verified matching video.
- Shopping extraction depends on recipe formatting. The draft includes all ingredients and requires review. Marking an item purchased does not add it to the pantry.
- A finished stream means the server completed its response; it does not prove the recipe is correct.

## Troubleshooting

| Problem | Check |
| --- | --- |
| Cannot connect to Ollama | Keep the server running; test `Invoke-RestMethod http://localhost:11434/api/tags` |
| Model not found | Run `ollama list` and install the model named in `ai_chef.py` |
| Repetition, unrelated output, or HTTP 500 | Read the actual server error; compare a short direct Ollama request on the working CPU setup |
| Slow generation | Run `ollama ps`; inspect processor usage and avoid simultaneous generations |
| Missing module import | Save the matching `.py` file beside `app.py`; read the final traceback line |
| Stream interrupted | Retry; partial output is not stored as a completed recipe |
| Old favorite has a generic name | Correct the name in Favorites; new title handling does not rename old database rows |

## Documentation and demo

See `docs/DEMO_GUIDE.md` for the screenshot list, recording script, and final release checks. The project report includes architecture and workflow diagrams.

## Future improvements

Verified nutrition lookup, stronger structured recipe consistency checks, persistent game scores, recipe reuse/cache, and measured generation-speed improvements are future work. Multi-user hosting would require authentication and separate data storage.


## Local setup on Windows

Install Python, Git, and Ollama first. The project was developed using a Windows PowerShell virtual environment.

```powershell
git clone https://github.com/jayanthkota20/Pantry-cooking-assistant.git
cd Pantry-cooking-assistant
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen2.5:7b
```

Using the virtual environment's Python directly avoids requiring PowerShell activation.

### Start Ollama

Open the Ollama desktop app **or** run the server in a separate terminal. Do not run two servers on the same port.

```powershell
ollama serve
```

The development machine produced unrelated and repetitive output with its Intel Arc integrated GPU through Vulkan. CPU mode produced more relevant output in comparison tests. To reproduce that working setup, quit the desktop server first, then run:

```powershell
$env:OLLAMA_VULKAN = "0"
$env:OLLAMA_IGPU_ENABLE = "0"
ollama serve
```

These variables apply to that terminal session. This is a machine-specific workaround, not a claim that all Intel GPUs fail.

### Start Streamlit

In another terminal, from the project folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

### Configuration

The current AI configuration is in `ai_chef.py`:

```python
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"
```

`requirements.txt` should include `streamlit` and `requests`. SQLite and the other Python utilities used here are included with Python. Ollama and its model are installed separately.

## Main files

| File | Responsibility |
| --- | --- |
| `app.py` | Main tabs, grocery catalog, pantry operations, reminders, and UI styling |
| `ai_chef.py` | Prompt, streamed Ollama response, recipe title, download, YouTube, shopping handoff |
| `favorites.py` | Favorite storage, automatic labels, filters, corrections, and removal |
| `meal_planner.py` | Custom/AI/favorite meal snapshots, calendar dates, editing, weekly download |
| `shopping.py` | Persistent shopping checklist |
| `food_game.py` | Randomized matching game and session score |
| `.streamlit/config.toml` | Streamlit theme |
| `pantry.db` | Locally created application data; do not commit |

## Everyday workflow

1. Add pantry ingredients and review their reminder dates.
2. Open AI Chef and name a dish or describe a meal. Select a compatible food preference.
3. Read the streamed answer after generation finishes. Review its ingredients, quantities, and steps.
4. Download or save the recipe; review the shopping draft before adding items.
5. In Meal Planner, choose Custom meal, Latest AI recipe, or Favorite. Pick any date and meal slot.
6. Save, edit, or remove meals. Saving a date outside the displayed week opens that date's week.

## Data and persistence

Pantry, shopping, favorites, and meal plans are stored locally in `pantry.db`. Meal plans save independent recipe copies, so deleting a favorite does not delete an already-planned meal.

The current AI answer and game state use Streamlit session state. They may reset after a browser/session or server restart. Best moves is a session record, not a permanent leaderboard.

The app is a local single-user prototype without accounts or per-user data isolation.

## Validation and limitations

The developer reported completing functional checks on October 16, 2026. Helper checks during development covered recipe-title formats, stream completion/error cases, and planner persistence, replacement, deletion, downloads, and week boundaries. This is not a comprehensive automated test suite or independent safety assessment.

- On the development laptop, Qwen 2.5 7B on CPU took roughly 90 seconds for a detailed app recipe. Streaming improves visibility, not necessarily total generation speed.
- Prompts cannot guarantee that a recipe respects every dietary, timing, quantity, or cooking constraint.
- Nutrition is estimated by the language model, not calculated from a verified ingredient database.
- Gluten status defaults to Not checked. Automatic food/cuisine labels are suggestions that users can correct.
- Reminder dates are organizational prompts, not expiry dates or a food-safety assessment. Notifications appear only while using the app.
- YouTube opens search results; it does not provide a verified matching video.
- Shopping extraction depends on recipe formatting. The draft includes all ingredients and requires review. Marking an item purchased does not add it to the pantry.
- A finished stream means the server completed its response; it does not prove the recipe is correct.

## Troubleshooting

| Problem | Check |
| --- | --- |
| Cannot connect to Ollama | Keep the server running; test `Invoke-RestMethod http://localhost:11434/api/tags` |
| Model not found | Run `ollama list` and install the model named in `ai_chef.py` |
| Repetition, unrelated output, or HTTP 500 | Read the actual server error; compare a short direct Ollama request on the working CPU setup |
| Slow generation | Run `ollama ps`; inspect processor usage and avoid simultaneous generations |
| Missing module import | Save the matching `.py` file beside `app.py`; read the final traceback line |
| Stream interrupted | Retry; partial output is not stored as a completed recipe |
| Old favorite has a generic name | Correct the name in Favorites; new title handling does not rename old database rows |

## Documentation and demo

See `docs/DEMO_GUIDE.md` for the screenshot list, recording script, and final release checks. The project report includes architecture and workflow diagrams.

## Future improvements

Verified nutrition lookup, stronger structured recipe consistency checks, persistent game scores, recipe reuse/cache, and measured generation-speed improvements are future work. Multi-user hosting would require authentication and separate data storage.
