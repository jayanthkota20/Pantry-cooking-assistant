# Version 1 demo and release guide

## Screenshots to capture

Capture the real running app. Use sample pantry and recipe data rather than personal information. Save files in the repository's `assets` folder.

| Filename | Show |
| --- | --- |
| `pantry-overview.png` | Top grocery row, category tabs, and a few saved ingredients |
| `pantry-reminder.png` | A reminder set to today and the reminder popup |
| `ai-chef-recipe.png` | A completed recipe with its name, ingredients, and action buttons |
| `favorites.png` | Named favorites and the food/cuisine/gluten filters |
| `shopping-list.png` | A reviewed shopping list with one purchased item |
| `meal-planner.png` | Two planned meals, a chosen date, and weekly download |
| `food-match.png` | A partially played game with food names and move counts |

The README does not link these images yet, so it will not contain broken screenshot links. After capturing them, add relevant Markdown images such as `![Weekly meal planner](assets/meal-planner.png)`.

## Recording preparation

1. Start Ollama in the working CPU configuration and start Streamlit.
2. Have one completed AI recipe and a named favorite available.
3. Put a sample pantry item on today's reminder date; explain that this is a reminder, not an expiry assessment.
4. Check the planner, shopping list and game before recording.
5. Do not delete `pantry.db` to reset the demonstration; remove sample records through the app if needed.

## Three to four minute recording script

### Introduction and pantry

Say: "I built Pantry Cooking Assistant to connect meal ideas with pantry tracking and planning. It is a Python Streamlit app with local SQLite storage and a local Ollama model."

Show My Pantry. Search for an ingredient, add it, and point out saved ingredients. Say: "Users can search food categories and track added dates. Fresh items default to a seven-day reminder and dry goods to ten days. These are reminders, not food-expiry predictions."

Open the reminder popup briefly and close it.

### AI recipe

Show AI Chef. Say: "Users can request any dish, even when their pantry is empty. The pantry is optional context. Cuisine, food preference, and cooking-time preferences guide the recipe."

Submit a short request to show text arriving. Say: "The larger local model took around a minute and a half on my laptop, so I added streaming. Users can read while it generates. Streaming does not make the whole generation instant."

If recording time is limited, clearly announce a cut while generation finishes. Do not imply the edited recording is the measured response time.

Show the completed title, ingredients, steps, and nutrition. Say: "Nutrition values are AI estimates. This prototype does not calculate verified nutrition or guarantee recipe correctness."

Show Download recipe, Add to favorites, and the single YouTube search action. Do not open unrelated video playback.

### Favorites and shopping

Show a named favorite and filter by its cuisine. Say: "Saved recipes remain available without regenerating them, and users can correct their names and labels. Gluten status is separate and defaults to Not checked."

Show the recipe's editable shopping draft, remove an item already owned, add the rest, and mark one purchased in Shopping List.

### Meal planner

Show Custom meal. Enter a meal name and choose a date. Say: "The planner supports custom meals, the latest AI recipe, or a favorite. Users can save just a meal name and add details later."

Save the meal and show its week. Briefly open Edit meal and point out Remove meal and Download weekly plan. Say: "The planner saves its own recipe copy, so removing a favorite does not remove an already-planned meal."

### Game and closing

Reveal a food card and point out its name and move counter. Say: "The food matching game uses random categories and shows food names, so it can also help children recognize ingredients."

Close with: "This project helped me learn local API integration, streamed responses, SQLite storage, session state, date handling, reusable modules, and Git. Next I would improve recipe consistency and add verified nutrition data."

## Final release checks

The developer reported the app's functional checks complete on October 16, 2026. Before a public portfolio release, also confirm:

- The README setup matches `requirements.txt` and the actual project files.
- The recipe title fix is saved and committed.
- Screenshots are captured from the final app and added only after checking them.
- The demonstration is recorded; a script alone is not a recorded demo.
- `.gitignore` excludes `.venv/`, `__pycache__/`, `*.pyc`, `pantry.db`, `pantry.db-*`, and `ollama-debug.txt`.
- Review `git status` and stage only the intended source, documentation, and screenshots.
- Commit, push, and confirm the repository is up to date.

## Explain the project in thirty seconds

"I built a local AI cooking assistant using Python, Streamlit, Ollama, and SQLite. Users manage their pantry, get reminders, generate and save recipes, review shopping lists, and schedule custom or AI meals. I added streamed recipe output because local generation takes time, and I keep estimated nutrition and reminder dates clearly separate from verified nutrition and expiry information."
