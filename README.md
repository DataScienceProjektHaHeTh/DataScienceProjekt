# Trump, Tariffs & Trade-Turbulence
### Does Trump-related news move financial markets?

**CAU Kiel · Data Science Project · Group 11**
Jan Ole Hansen · Fridjoff Hempel · Nico Thielert

---

## 1. Introduction

This project examines whether Trump-related political news coverage in *The Guardian* predicts short-term price movements in three major asset classes: **MSCI World** (global equities), **Gold** (safe-haven commodity), and **Bitcoin** (speculative crypto asset).

We focus on Donald Trump's second presidential term, beginning with his inauguration on 20 January 2025. The working hypothesis is that politically sensitive news — particularly around trade policy — triggers measurable "flight-to-safety" rotations in financial markets.

### Research Questions

We investigate seven research questions across three analytical themes:

| # | Question |
|---|----------|
| **RQ1** | Does daily news *frequency* in a category correlate with x-day asset returns following a coverage spike? |
| **RQ2** | How do MSCI World, Gold, and Bitcoin differ in direction and magnitude of abnormal returns following identical news spikes? |
| **RQ3** | Does the average daily VADER sentiment score of Guardian articles predict the direction and magnitude of x-day returns? |
| **RQ4** | Do simultaneous spikes across multiple news categories amplify returns compared to isolated single-category spikes? |
| **RQ5** | At what article volume threshold does news coverage begin to trigger a measurable market reaction? |
| **RQ6** | Which asset class reacts fastest (in days) to a news spike, and does the reaction speed differ by news category? |
| **RQ7** | Does the category with the most daily coverage also produce the strongest market correlation — or does content specificity beat volume? |

### Key Finding

Only **Trade Policy** coverage produces a statistically significant, reproducible market signal. On spike days (article count > 30-day rolling mean + 1 standard deviation), a clear **flight-to-safety** rotation emerges at a 7-day return window with 30-day z-score normalization:

- **MSCI World**: r = −0.45, p < 0.001 (equities fall)
- **Gold**: r = +0.40, p = 0.005 (safe haven rises)
- **Bitcoin**: r = −0.38, p = 0.003 (crypto falls with equities)

Geopolitics and Domestic Politics show no significant signal under any parameter configuration. News tone (VADER sentiment) carries no measurable short-term predictive power for any asset or category.

### Data Sources

| Source | Content | Period |
|--------|---------|--------|
| **The Guardian Open Platform API** | Daily article counts and full body text for three Trump-related categories: *Trade Policy*, *Geopolitics*, *Domestic Politics* | 01 Jan 2025 – present |
| **Yahoo Finance (yfinance)** | Daily closing prices for MSCI World ETF (URTH), Gold Futures (GC=F), Bitcoin (BTC-USD) | 20 Jan 2025 – present |

---

## 2. Data Pipeline

The pipeline runs in five sequential stages. Processed artefacts are cached in `data/processed/` so the website can load pre-computed results without re-running expensive computations on every request.

```
data/raw/news/          data/raw/market/
  *.json (Guardian)       *.csv (yfinance)
        |                       |
        v                       v
  guardian_fetcher.py     market_fetcher.py
        |                       |
        +----------+------------+
                   |
                   v
          src/processing/sentiment.py
          (VADER scoring per article -> daily mean per category)
                   |
                   v
          src/analysis_rq1_rq3_rq7/data_prep.py
          (merge counts + sentiment + prices -> master.csv)
                   |
          +--------+------------------+
          |                           |
          v                           v
   rq1_correlation.py       analysis_rq5.py
   rq2_spikedays.py         analysis_rq6.py
   rq3_sentiment.py         (-> master_rq5.csv,
   rq4_spikedays.py             master_rq6.csv)
   rq7_ranking.py
```

### Stage 1 — Data Collection

**`src/data_collection/guardian_fetcher.py`**
Queries The Guardian Open Platform API with three category-specific search terms (trade policy, geopolitics, domestic politics). Articles are fetched with full `bodyText`, paginated at 200 articles per request and sorted oldest-first. Results are stored as JSON files under `data/raw/news/`.

**`src/data_collection/market_fetcher.py`**
Downloads daily OHLCV data for URTH (MSCI World), GC=F (Gold Futures), and BTC-USD (Bitcoin) via `yfinance`. Closing prices are stored as CSVs under `data/raw/market/`.

### Stage 2 — Sentiment Scoring

**`src/processing/sentiment.py`**
Applies the VADER (Valence Aware Dictionary and sEntiment Reasoner) rule-based sentiment analyser to every article body. The VADER compound score (range −1 to +1) is computed per article and then averaged per category per day. Results are saved to `data/processed/daily_sentiment.csv` and per-category files in `data/processed/articles_with_sentiment/`.

### Stage 3 — Master Dataset Construction

**`src/analysis_rq1_rq3_rq7/data_prep.py`**
Loads article counts and sentiment scores, aligns them with market closing prices on a common trading-day index, computes x-day forward returns for each asset, and applies 30-day rolling z-score normalization to article counts. The merged DataFrame is persisted as `data/processed/master.csv`.

### Stage 4 — Per-RQ Analysis

Each research question has a dedicated analysis module:

| File | Analysis |
|------|----------|
| `rq1_correlation.py` | Spearman correlation between (normalized) article counts on spike days and x-day forward returns; produces r and p-value matrices |
| `rq2_spikedays.py` | Event-study: abnormal returns (actual minus 5-day trend prediction) around shared spike days per asset |
| `rq3_sentiment.py` | Sentiment bucket analysis: mean returns and ±1 SE bars across negative / neutral / positive VADER days |
| `rq4_spikedays.py` | Compares abnormal returns on single-category vs. multi-category spike days |
| `src/analysis/analysis_rq5.py` | Volume threshold analysis: % of days exceeding a 1% movement threshold, binned by article count |
| `src/analysis/analysis_rq6.py` | Lag profile: mean cumulative return at each day +1 through +5 after a spike, per asset and category |
| `rq7_ranking.py` | Compares volume ranking (avg articles/day) with correlation-strength ranking (avg |r| across assets) |

### Stage 5 — Processed Data

All results are cached in `data/processed/` as CSV files. The website reads these at startup rather than re-running the full pipeline, ensuring fast page loads on the cloud host.

---

## 3. Website — Architecture & Deployment

### Framework

The web application is built with **Plotly Dash** (v4), a Python framework that renders interactive React-based UIs from pure Python. Dash is built on top of **Flask**, which serves as the underlying WSGI application.

```
website/
├── app.py                       # App entry point, layout, navbar, footer
├── assets/
│   ├── style.css                # Global Guardian-inspired stylesheet
│   ├── mathjax_retypeset.js     # Re-triggers MathJax on React navigation
│   └── donald-trump-home.png    # Hero image
└── pages/
    ├── home.py                  # Landing page (newspaper-style layout)
    ├── analysis_and_results.py  # All 7 RQs with interactive charts
    ├── about_project.py         # Approach & Assumptions (definitions, formulas)
    └── about_team.py            # Meet the team
```

**Multi-page routing** is handled by `dash.register_page()` with URL-based parameter passing (e.g. `/visualizations?rq=rq3`). Dash callbacks keep charts reactive to parameter changes (return window, spike threshold, normalization mode) without full page reloads.

**MathJax** (v3, loaded via CDN in `app.py`'s `index_string`) renders LaTeX formulas in the Approach & Assumptions page. A MutationObserver in `mathjax_retypeset.js` re-triggers typesetting after React DOM updates on client-side navigation.

### Data Connection

On startup, `analysis_and_results.py` imports the analysis modules, which read the pre-processed CSVs from `data/processed/`. All chart computations happen server-side in Python/Pandas; Plotly serialises the resulting figure objects to JSON and sends them to the browser. Interactive parameter changes trigger Dash server-side callbacks that recompute and re-render only the affected chart.

### Deployment

The app is deployed on **Render.com** as a web service with auto-deploy on every push to the `main` branch.

- **Start command**: `gunicorn website.app:server`
- **Entry point**: `website/app.py` exposes `server = app.server` (the Flask WSGI object)
- **Port**: read from the `PORT` environment variable (set automatically by Render)
- **Dependencies**: installed from `requirements.txt` by Render's build step

Files in `data/processed/` are committed to the repository so the deployed instance can serve pre-computed results without API keys or a running data pipeline on the server.

---

## 4. Using the Web Application

### Navigation

A fixed navy sidebar on the right-hand side of every page provides navigation. The **Analysis & Results** dropdown lists all seven research questions (RQ1–RQ7) and navigates directly to the selected question. A small home icon at the top of each page navigates back to the landing page.

### Home Page (`/`)

The landing page gives a newspaper-style overview:
- **Left column**: project headline, brief motivation, and clickable research question cards — each links directly to the corresponding RQ analysis
- **Right column**: three Key Findings cards summarising the most important results

### Analysis & Results Page (`/visualizations?rq=rqN`)

The main interactive dashboard. Select any RQ via the blue button row at the top.

Each RQ section contains:
1. **Research question heading** with a description of what is measured
2. **Parameter controls** — adjust return window, spike threshold, normalization mode, and more to explore robustness
3. **Interactive Plotly charts** — hover for exact values, click legend items to toggle series, zoom by dragging
4. **Takeaway** — a concise interpretation of the main finding below each chart

**Highlights to explore:**
- **RQ1 Heatmap**: switch from *Raw count* to *30-day normalized* and increase the return window to 7 days to watch the Trade Policy flight-to-safety signal emerge
- **RQ2 Event Window**: select individual spike events and adjust the pre/post window to compare how each asset reacts to the same news day
- **RQ3 Bucket Chart**: tighten the VADER thresholds to see how isolating strongly negative days still produces no reliable return signal
- **RQ5 Radar**: toggle between *Average reactivity* and *Per asset* to see which news category consistently triggers movement across all assets

### Approach & Assumptions Page (`/about-project`)

Documents all core definitions (spike day, x-day return, VADER compound score, Spearman r, Standard Error) with LaTeX-rendered formulas. Essential vocabulary for interpreting the analysis.

---

## 5. LLM Usage and Code Attribution

We used AI language models — primarily **Claude** by Anthropic, accessed via Claude Code — as a development tool throughout this project. We are fully transparent about this.

### Our approach

Before each commit we checked our locally developed code with AI to ensure high software quality (comments, logic and simplifications) and also find possible side effects which we wanted to fix before pushing anything.

Beyond code review, AI was used for:

| Use case | Description |
|----------|-------------|
| **Debugging** | Diagnosing runtime errors in the Render deployment (e.g. missing processed files causing `KeyError`, incorrect colour names in Plotly) |
| **Frontend development** | CSS layout (Guardian colour scheme, responsive two-column grid, fixed navbar), Dash component trees |
| **Statistical sanity checks** | Confirming Spearman correlation is appropriate for non-normal return distributions, verifying the SE formula |
| **Documentation** | Drafting takeaway texts, core definitions, and this README |

### Attribution

Code that was **directly generated by or substantially co-written with an LLM** carries an inline comment at the top of the relevant function or block:

```python
# LLM-assisted: logic reviewed and simplified with Claude (Anthropic)
```

Code that was **developed by the team and only reviewed by AI** does not carry an LLM comment — the AI acted as a linter and sounding board, not as an author. The core statistical analysis logic (Spearman correlation, VADER pipeline, spike-day definition, event-study abnormal return calculation) was developed independently by the team.

---

## 6. Repository Structure

```
DataScienceProjekt/
├── data/
│   ├── raw/
│   │   ├── news/              # Guardian API JSON files (3 categories)
│   │   └── market/            # Yahoo Finance CSV files (3 assets)
│   └── processed/             # Pre-computed analysis outputs (committed)
├── src/
│   ├── data_collection/       # Guardian API & Yahoo Finance fetchers
│   ├── processing/            # VADER sentiment scoring pipeline
│   ├── analysis/              # RQ5 & RQ6 analysis modules
│   └── analysis_rq1_rq3_rq7/ # RQ1-RQ4 & RQ7 analysis modules + plots
├── website/
│   ├── app.py                 # Dash application entry point
│   ├── assets/                # CSS, JS, images
│   └── pages/                 # One Python file per page
├── presentation/              # LaTeX beamer slides + exported plot PNGs
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 7. Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/DataScienceProjektHaHeTh/DataScienceProjekt.git
cd DataScienceProjekt

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app locally (pre-processed data is already committed)
python website/app.py
# Open http://localhost:8080

# 5. Optional: re-fetch data (requires API keys in .env)
#    GUARDIAN_API_KEY=<your_key>
python -m src.data_collection.guardian_fetcher
python -m src.data_collection.market_fetcher
python -m src.processing.sentiment
```

---

*CAU Kiel · Data Science · WiSe 2025/26 · Group 11*
