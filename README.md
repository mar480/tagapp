# Tally

Tally is a dependency-free, interactive prototype for an accessible UK iXBRL tagging workspace. It demonstrates taxonomy browsing, drag-and-drop tagging, fact property editing, validation feedback, and a filing review flow.

## Run locally

```bash
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

## Prototype interactions

- Search and browse taxonomy concepts.
- Drag **Current assets**, **Cash at bank and in hand**, or **Net current assets** onto the untagged debtors value.
- Select tagged facts to update the inspector.
- Add a dimension and edit unit, scale, decimals, and balance properties.
- Run the validation review from **Validate** or **Review & file**.
