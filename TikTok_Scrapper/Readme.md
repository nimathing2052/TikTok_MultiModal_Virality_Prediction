# TikTok Scrapper for Nepal Local Election Analysis

---

## Overview

This repository provides a modular and reproducible toolkit to collect, download, and process TikTok data related to Nepal's 2022 Local Elections. It extends and enhances functionalities originally adapted from [`gabbypinto/US2024PresElectionTikToks`](https://github.com/gabbypinto/US2024PresElectionTikToks).

Developed and maintained by **Nima Thing**.

---

## Features

- **Metadata Collection**: Fetch TikTok video metadata using the official TikTok Research API.
- **Video Download**: Download TikTok videos based on URLs with validation and logging.
- **User Info Collection**:
  - **Official API Mode**: Fetch user profiles using TikTok Research API.
  - **Unofficial API Mode**: Scrape user info using TikTokApi with both sequential and parallel execution.
- **Error Handling**: Retry logic, resume support, detailed logging.
- **Extensibility**: Modular scripts ready for future additions like comment scraping.

---

## Repository Structure

```
TikTok_Scrapper/
├── download_videos.py                # Download TikTok videos from URL list
├── metadata_collection.py            # Collect TikTok video metadata via Research API
├── users_official_api_with_client_auth.py  # Fetch user info via official API
├── users_parallel.py                  # Parallel user scraping (Unofficial API)
├── users_unofficial_api.py            # Sequential user scraping (Unofficial API)
├── video_comments_official_api.py     # (Optional) Video comment collection (Official API)
├── video_comments_unofficial_api.py   # (Optional) Video comment collection (Unofficial API)
├── filter.py                          # (Optional) Helper functions
├── README_scripts.md                  # Documentation (this file)
```

---

## Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
playwright install  # Install browsers for TikTokApi scraping
```

---

## Usage Guide

### 1. Metadata Collection

```bash
python metadata_collection.py
```
Requires environment variables:
- `TIKTOK_CLIENT_KEY`
- `TIKTOK_CLIENT_SECRET`

Keywords/hashtags must be listed in:
```
supplementary_files/keywords_hashtags_nepal.txt
```

---

### 2. Video Download

```bash
python download_videos.py <csv_file_name>
```
Downloads videos into structured subdirectories, logs download status, and validates MP4 files.

---

### 3. User Info Collection

**Official API Mode**
```bash
python users_official_api_with_client_auth.py
```

**Unofficial API Mode (Parallel)**
```bash
python users_parallel.py split_csv_files/split_part_5.csv
```

**Unofficial API Mode (Sequential)**
```bash
python users_unofficial_api.py
```

Unofficial API requires `ms_token` environment variable.

---

## Environment Variables

```bash
export TIKTOK_CLIENT_KEY="your_client_key"
export TIKTOK_CLIENT_SECRET="your_client_secret"
export ms_token="your_ms_token"
```

Optional:
```bash
export TIKTOK_ACCESS_TOKEN="your_access_token"
```

---

## Requirements

See [requirements.txt](./requirements.txt) for a full list.

---

## License

This project is licensed under the **MIT License**.

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

## Acknowledgements

- Core inspiration: [gabbypinto/US2024PresElectionTikToks](https://github.com/gabbypinto/US2024PresElectionTikToks)
- TikTok Research API team
- TikTokApi Python library contributors

---

> Developed with passion for TikTok and Social Media research and transparency by **Nima Thing**, 2025.