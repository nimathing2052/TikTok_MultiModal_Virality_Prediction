# TikTok Virality Analysis During Nepal Local Election 2022

## Overview

This repository contains the code, data, and documentation for a thesis project analyzing TikTok video virality during the Nepal Local Election 2022. The project consists of two main components:

1. **TikTok Scraper**: A modular toolkit to collect, download, and process TikTok data related to the election.
2. **Analysis**: A series of Jupyter Notebooks performing Exploratory Data Analysis (EDA) and addressing two research questions (RQ1 and RQ2) to understand virality patterns, predict virality using multimodal data, and examine the impact of communication styles and content themes.

**Author**: Nima Thing  
**Date**: April 2025

### Research Objectives
- **Data Collection**: Gather TikTok video metadata, videos, and user information relevant to the Nepal Local Election 2022.
- **EDA**: Explore engagement patterns, temporal trends, and hashtag usage during the election period.
- **RQ1**: Identify factors predicting TikTok video virality using multimodal features (audio, image, text, metadata) and machine learning models.
- **RQ2**: Analyze how communication styles and content themes influence virality, with a focus on political content.

## Repository Structure

```
NEP_LOCAL_ELECTION/
├── Analysis/
│   └── EDA/                              # Outputs from Exploratory Data Analysis
│       ├── heatmap_post_count.jpg        # Heatmap of post counts
│       ├── tiktok_video_counts_election_period.jpg  # TikTok video counts during election
│       ├── top_100_hashtags.csv          # Top 100 hashtags from analysis
│       └── ...                           # Additional EDA outputs
├── Communication/                        # (Not used in this analysis)
├── data/                                 # Datasets
│   ├── NPL_TikTok_3k_with_Embeddings.csv # TikTok dataset (3k rows) with embeddings
│   ├── NPL_TikTok_3k.csv                # TikTok dataset (3k rows) without embeddings
│   └── NPL_TikTok_Full_28k.csv          # Full TikTok dataset (28k rows)
├── env/                                  # Environment setup (if applicable)
├── PreProcessing/                        # Preprocessing scripts (if applicable)
├── supplementary_files/                  # Supporting files for TikTok Scraper
│   └── keywords_hashtags_nepal.txt       # Keywords and hashtags for metadata collection
├── TikTok_Scrapper/                      # Scripts for TikTok data collection
│   ├── download_videos.py                # Download TikTok videos from URL list
│   ├── metadata_collection.py            # Collect TikTok video metadata via Research API
│   ├── users_official_api_with_client_auth.py  # Fetch user info via official API
│   ├── users_parallel.py                 # Parallel user scraping (Unofficial API)
│   ├── users_unofficial_api.py           # Sequential user scraping (Unofficial API)
│   ├── video_comments_official_api.py    # (Optional) Video comment collection (Official API)
│   ├── video_comments_unofficial_api.py  # (Optional) Video comment collection (Unofficial API)
├── EDA_Analysis_Full_Dataset.ipynb       # Notebook for Exploratory Data Analysis
├── hashtags_plot.png                     # Plot of top hashtags from EDA
├── model_summary.tex                     # LaTeX output of OLS model summary (RQ2)
├── RQ_1_Prediction.ipynb                 # Notebook for RQ1: Virality prediction with ML
├── RQ_2_Analysis.ipynb                   # Notebook for RQ2: Impact of styles/themes on virality
├── xgb_model.pkl                         # Saved XGBoost model from RQ1
└── README.md                             # Project documentation
```

# 🇳🇵 TikTok Political Virality Analysis - Nepal 2022 Local Elections

This project analyzes TikTok video virality during Nepal’s 2022 Local Elections using multimodal features (audio, image, text, metadata).  
It provides a full pipeline from **data collection** to **virality prediction** and **statistical analysis**.

---

## 📦 Required Packages

Install the following Python libraries:

```bash
pip install pandas numpy matplotlib seaborn scikit-learn xgboost lightgbm shap statsmodels scipy emoji nltk transformers sentence_transformers playwright TikTokApi
```

### Install Browsers for TikTokApi Scraping
```bash
playwright install
```

### Download NLTK Data
Some scripts require additional NLTK resources:

```python
import nltk
nltk.download('vader_lexicon')
```

---

## 📋 Data Collection Toolkit

The `TikTok_Scrapper` directory provides a modular scraper, extending [gabbypinto/US2024PresElectionTikToks](https://github.com/gabbypinto/US2024PresElectionTikToks).

### Features
- **Metadata Collection**: Fetch TikTok video metadata using the official TikTok Research API.
- **Video Download**: Download TikTok videos based on URLs with validation and logging.
- **User Info Collection**:
  - *Official API Mode*: Fetch user profiles using TikTok Research API.
  - *Unofficial API Mode*: Scrape user info using TikTokApi (sequential or parallel).
- **Error Handling**: Retry logic, resume support, detailed logging.
- **Extensibility**: Modular scripts ready for future features (e.g., comment scraping).

---

## 🚀 Usage Guide (ONLY IF YOU WANT TO DOWNLOAD NEW VIDEO METADATA/THE DATA IS ALREADY PRESENT IN DATA FOLDER)

### 1. Setup Environment Variables

```bash
export TIKTOK_CLIENT_KEY="your_client_key"
export TIKTOK_CLIENT_SECRET="your_client_secret"
export ms_token="your_ms_token"
export TIKTOK_ACCESS_TOKEN="your_access_token"  # Optional
```

### 2. Metadata Collection

```bash
cd TikTok_Scrapper
python metadata_collection.py
```

- Requires `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET`.
- Input: Keywords/hashtags from `supplementary_files/keywords_hashtags_nepal.txt`.
- Output: Metadata CSV files in the `data/` directory.

### 3. Video Download

```bash
python download_videos.py <csv_file_name>
```
- Downloads videos into structured folders.
- Logs download status and validates `.mp4` files.

### 4. User Info Collection

#### Official API Mode:
```bash
python users_official_api_with_client_auth.py
```

#### Unofficial API Mode (Parallel):
```bash
python users_parallel.py split_csv_files/split_part_5.csv
```

#### Unofficial API Mode (Sequential):
```bash
python users_unofficial_api.py
```
- Note: Unofficial API requires `ms_token`.

---

## 📚 Datasets

- `NPL_TikTok_Full_28k.csv`: Full dataset of ~28,000 TikTok videos for EDA.
- `NPL_TikTok_3k.csv`: Subset of 3,000 classified videos for RQ1 and RQ2.
- `NPL_TikTok_3k_with_Embeddings.csv`: Subset with precomputed embeddings for RQ1.

> ⚠️ **Note**: Due to TikTok data usage policies, datasets are not publicly shared.  
> Contact the author for access.

---

## 📈 Analysis Notebooks

Run the notebooks in this order:

### 1. Exploratory Data Analysis (EDA)

```bash
jupyter notebook EDA_Analysis_Full_Dataset.ipynb
```
- Analyzes the full 28k dataset: trends, hashtags, temporal patterns.
- Outputs: Heatmaps, plots, CSV files in `Analysis/EDA/`.

### 2. Research Question 1: Virality Prediction

```bash
jupyter notebook RQ_1_Prediction.ipynb
```
- Predicts virality using multimodal features.
- Models: Random Forest, XGBoost, LightGBM.
- Outputs: Trained model (`xgb_model.pkl`), SHAP values, metrics.

### 3. Research Question 2: Styles and Themes Impact

```bash
jupyter notebook RQ_2_Analysis.ipynb
```
- Analyzes the effect of communication styles and political themes.
- Outputs: OLS regression results (`model_summary.tex`), visualizations.

---

## 🧠 Key Findings

- **EDA**:
  - Peak posting around campaign period (May 1–10, 2022).
  - Viral peaks on Saturdays.
  - Popular hashtags: #nepal2022, #vote, etc.

- **RQ1 (Virality Prediction)**:
  - XGBoost achieved best AUC-ROC (~0.85).
  - Top predictors: Follower count, author verification, hashtag count.
  - Positive sentiment (from audio/text) correlated with higher virality.

- **RQ2 (Styles & Themes)**:
  - Music/Entertainment and Charisma/Leadership boosted engagement.
  - Independent candidates often used comedic styles.
  - Style-theme interactions had significant effects (e.g., music + independent themes).

---

## ⚙️ Notes

- **File Paths**: Adjust paths if necessary (`data/`, `Analysis/EDA/`, etc.).
- **Computational Resources**: At least 16GB RAM recommended.
- **Devanagari Font**: Optional font setup for Nepali text rendering.
- **Reproducibility**: Assumes datasets are already collected under `data/`.

---

## 📄 License

MIT License

```
MIT License

Copyright (c) 2025 Nima Thing

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- TikTok Research API Team: For official API access.
- TikTokApi Contributors: For enabling unofficial scraping.
- [gabbypinto/US2024PresElectionTikToks](https://github.com/gabbypinto/US2024PresElectionTikToks): Inspiration for scraper design.
- xAI's Grok: Assisted in organizing and commenting code.

---
