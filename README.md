# Privacy Sentinel

A Python-based tool for comparing and scoring privacy labels across iOS and Android platforms. Built as part of a BSc Cyber Security final year project at De Montfort University.

---

## What it does

Privacy labels — the short summaries apps publish on the App Store and Google Play — are often incomplete, vague, or inconsistent between platforms. Privacy Sentinel lets you enter label data for both platforms side by side, then scores them on three criteria:

- **Completeness** — are all the required fields filled in?
- **Specificity** — are the data types described in meaningful terms, or just vague catch-alls?
- **Consistency** — how much do the iOS and Android labels actually agree with each other?

Results are shown with a transparency score, a risk rating, and a breakdown of exactly where the two labels differ.

---

## Getting started

**1. Clone the repo and set up a virtual environment**
```bash
git clone https://github.com/masteribro/privacy-sentinel.git
cd privacy-sentinel
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the app**
```bash
streamlit run app.py
```

Opens at `http://localhost:8501` in your browser.

---

## Pages

| Page | What it does |
|---|---|
| Dashboard | Overview of all apps analysed — KPI cards, average score by category, recent submissions |
| Submit | Enter iOS and Android label data side by side and run the analysis |
| Results | Transparency score, radar chart, discrepancy list, and CSV export |
| History | Browse, search, and filter all past submissions |
| Settings | Adjust the High / Medium risk score thresholds |

---

## Project structure

```
privacy_sentinel/
    db_setup.py       — creates and migrates the SQLite database
    comparator.py     — compares two labels using Jaccard similarity
    scoring.py        — calculates completeness, specificity, consistency scores
    data_manager.py   — handles all database reads and writes
app.py                — Streamlit interface
requirements.txt
tests/
    test_comparator.py
    test_scoring.py
```

---

## Running tests

```bash
pytest
```

---

## Built with

- Python 3.11
- Streamlit
- Plotly Express
- SQLite3
- pandas
