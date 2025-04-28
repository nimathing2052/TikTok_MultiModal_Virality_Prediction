"""
Script Name: metadata_collection_improved.py (Modified v2)
Authors: Nima (Modified by AI Assistant)
Date: 2025/03/19 (Modified: 2024/08/03, v2: 2024/08/03)

Description:
    This script performs metadata video collection using the TikTok Research API.

Usage:
    Requires a text file of keywords and hashtags, contained in /supplementary_file/keywords_hashtags_phase<#>.txt
    Requires the file path to your main CSV file or the file path of where you want the script to be created.
    How to run the script: python3 metadata_collection_improved.py

Environment Variables:
    TIKTOK_CLIENT_KEY: Your TikTok API client key.
    TIKTOK_CLIENT_SECRET: Your TikTok API client secret.

Output Files:
    - JSON files in 'updated_local_election/' directory: Daily JSON responses from TikTok API.
    - CSV files:
        - 'Updated_LocalElection_22.csv': Combined CSV file containing all collected data (appended to).

Dependencies:
    Required libraries or modules are listed in requirements.txt
"""

import sys
import requests
import json
from datetime import datetime, timedelta, timezone # Import timezone from datetime
import time
import csv
import pandas as pd
import os
from requests.exceptions import ChunkedEncodingError
from urllib3.exceptions import ProtocolError

# --- Configuration from Environment Variables ---
CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET")

if not CLIENT_KEY or not CLIENT_SECRET:
    print("Error: Please set TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET environment variables.")
    sys.exit(1)

OUTPUT_DIRECTORY_JSON = "updated_local_election"
COMBINED_CSV_FILENAME = "Updated_LocalElection_22.csv"
KEYWORDS_HASHTAGS_FILE = "supplementary_files/keywords_hashtags_nepal.txt"


def append_to_existing_or_create_new(df, combined_df_path): # Removed daily_csv_filename_prefix
    """
    Appends the data returned from the API to the combined CSV file.
    Daily CSV files are no longer created.

    Args:
        df (pd.DataFrame): DataFrame containing TikTok video metadata for a specific date.
        combined_df_path (str): File path for the combined CSV file.
    """
    # Load the existing combined DataFrame
    if os.path.exists(combined_df_path):
        combined_df = pd.read_csv(combined_df_path)
    else:
        combined_df = pd.DataFrame()

    # No longer iterating through dates to create daily CSVs, directly append to combined

    # Append the new data to the combined DataFrame
    combined_df = pd.concat([combined_df, df], ignore_index=True) # Append the whole df directly

    # Drop duplicates in the combined DataFrame and save it
    combined_df = combined_df.drop_duplicates(subset=['id'], keep='first')
    print("Length of final/combined/elections CSV file:", len(combined_df))
    combined_df.to_csv(combined_df_path, index=False) # Save the combined CSV


def save_to_json_file(data, filename):
    """
    Save data to a JSON file.

    Args:
        data (dict): The response from the API and additional attributes.
        filename (str): Path to the JSON file to be created.
    """
    os.makedirs(OUTPUT_DIRECTORY_JSON, exist_ok=True)  # Ensure output directory exists
    filepath = os.path.join(OUTPUT_DIRECTORY_JSON, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to JSON file: {filepath}")


def create_tiktok_url(username, videoid):
    """
    Create the URL to a TikTok post.

    Args:
        username (str): Username of the TikTok video poster.
        videoid (int): 'id' of the video.

    Returns:
        str: The URL to the TikTok post.
    """
    return f"https://www.tiktok.com/@{username}/video/{videoid}"


def convert_epoch_to_datetime(input_time):
    """
    Convert Epoch/Unix time to UTC datetime components.
    Addresses DeprecationWarning by using timezone-aware datetime object.

    Args:
        input_time (int): The time the video was created in Epoch/UNIX time.

    Returns:
        pd.Series: Series containing year, month, day, hour, minute, second, date_string (YYYY-MM-DD),
                   and time_string (HH:MM:SS) in UTC.
    """
    utc_time_stamp = datetime.fromtimestamp(input_time, timezone.utc) # Use timezone-aware object

    # Extract date and time components
    year = utc_time_stamp.year
    month = utc_time_stamp.month
    day = utc_time_stamp.day
    hour = utc_time_stamp.hour
    minute = utc_time_stamp.minute
    second = utc_time_stamp.second
    date_string = utc_time_stamp.strftime("%Y-%m-%d")
    time_string = utc_time_stamp.strftime("%H:%M:%S")

    return pd.Series([year, month, day, hour, minute, second, date_string, time_string])


def get_access_token(client_key, client_secret):
    """
    Fetches the Research API access token using client key and secret from environment variables.

    Args:
        client_key (str): Client key for TikTok API.
        client_secret (str): Client secret for TikTok API.

    Returns:
        dict or None: Dictionary containing access token information ('access_token', 'expires_in', 'token_type')
                       or None if token retrieval fails.
    """
    endpoint_url = "https://open.tiktokapis.com/v2/oauth/token/"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'client_key': client_key,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    try:
        response = requests.post(endpoint_url, headers=headers, data=data)
        response.raise_for_status()
        response_json = response.json()
        keys = ['access_token', 'expires_in', 'token_type']
        access_token_dict = {key: response_json[key] for key in keys if key in response_json}
        return access_token_dict
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error during access token retrieval: {http_err}, Response: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error during access token retrieval: {req_err}")
        return None
    except json.JSONDecodeError as json_err:
        print(f"JSON decode error during access token retrieval: {json_err}, Response: {response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error during access token retrieval: {e}")
        return None


def fetch_tiktok_data(start_date, end_date, keywordsList, hashtagsList, token_info):
    """
    Fetch metadata of TikTok posts/videos within a date range, using keywords and hashtags.

    Args:
        start_date (str): Start date in YYYYMMDD format.
        end_date (str): End date in YYYYMMDD format.
        keywordsList (list): List of keywords for the query.
        hashtagsList (list): List of hashtags for the query.
        token_info (dict): Dictionary containing access token information.

    Returns:
        tuple: (full_json_response, total_count) - JSON response and number of videos collected.
               Returns empty JSON and 0 count in case of errors or no data.
    """
    full_json_response = {'data': {'videos': []}} # Initialize properly
    total_count = 0

    access_token = token_info["access_token"]
    headers = {
        'authorization': f"Bearer {access_token}",
    }

    url = 'https://open.tiktokapis.com/v2/research/video/query/?fields=id,like_count,create_time,region_code,share_count,view_count,comment_count,music_id,hashtag_names,username,effect_ids,playlist_id,video_description,voice_to_text'

    data = {
        "query": {
            "and": [
                {"operation": "IN", "field_name": "region_code", "field_values": ["NP"]}
            ],
            "or": [
                {"operation": "IN", "field_name": "keyword", "field_values": keywordsList},
                {"operation": "IN", "field_name": "hashtag_name", "field_values": hashtagsList},
            ]
        },
        "start_date": start_date,
        "end_date": end_date,
        "max_count": 100  # Max videos per request from TikTok Research API
    }
    print("API Request Data:", data)
    max_retries = 3  # Reduced retries for daily quota limit context

    retries = 0
    data['cursor'] = 0 # Initialize cursor for pagination if needed
    data['search_id'] = None # Initialize search_id

    while True:
        if time.time() > token_info["expires_at"]:
            token_info = get_access_token(CLIENT_KEY, CLIENT_SECRET)
            if not token_info: # Handle token refresh failure
                print("Failed to refresh access token. Exiting data fetching.")
                return full_json_response, total_count # Return current data, could be partial
            token_info['expires_at'] = time.time() + token_info['expires_in']
            access_token = token_info["access_token"]
            headers["authorization"] = f"Bearer {access_token}"
            print("Token expired, new token generated.")

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                response_json = response.json()
                videos = response_json['data'].get('videos', []) # Safely get videos, handle missing key
                full_json_response['data']['videos'].extend(videos)

                total_count += len(videos)
                print(f"Current data fetch: {len(videos)} videos, Total Count: {total_count}")

                if response_json['data'].get('has_more'): # Safely check for 'has_more'
                    next_cursor = response_json['data'].get('cursor')
                    next_search_id = response_json['data'].get('search_id')
                    data['cursor'] = next_cursor
                    data['search_id'] = next_search_id
                    print(f"Fetching next page, cursor: {next_cursor}, search_id: {next_search_id}")
                    time.sleep(40) # Rate limit delay
                    if total_count >= 5000: # Added a safety limit to avoid very large fetches
                        print("Reached 5000 video limit (safety stop). Returning current data.")
                        return full_json_response, total_count
                else:
                    print("No more data (has_more is False). Returning fetched data.")
                    return full_json_response, total_count # No more pages
            elif response.status_code == 400:
                print(f"HTTP 400 Error: Bad Request. Response: {response.text}")
                time.sleep(50) # Wait and retry, might be temporary issue
            elif response.status_code == 401:
                print(f"HTTP 401 Error: Unauthorized (Token expired or invalid). Response: {response.text}")
                print("Will attempt to refresh token in next iteration.") # Token refresh logic is in the loop
            elif response.status_code == 429:
                print(f"HTTP 429 Error: Too Many Requests (Rate Limit Exceeded). Response: {response.text}")
                print("Stopping data fetching due to rate limit. Please try again later.")
                return full_json_response, total_count # Stop fetching, respect rate limit
            elif response.status_code in [500, 503, 504]: # Server side errors, retry with backoff
                print(f"HTTP {response.status_code} Error: Server error. Response: {response.text}")
                retries += 1
                if retries >= max_retries:
                    print(f"Max retries ({max_retries}) reached for server error. Stopping.")
                    return full_json_response, total_count # Stop after max retries
                wait_time = 2**retries * 5  # Exponential backoff (5, 10, 20 seconds...)
                print(f"Waiting {wait_time} seconds before retrying (Retry {retries}/{max_retries})...")
                time.sleep(wait_time)
            elif response.status_code == 504:
                # 504 error: Request timed out error
                print("HTTP 504 Error: Request timed out error. Response: {response.text}")
                time.sleep(50)
            else: # Unexpected status code
                print(f"HTTP Error: Unexpected status code {response.status_code}. Response: {response.text}")
                return full_json_response, total_count # Stop on unexpected error

        except (ChunkedEncodingError, ProtocolError) as e:
            retries += 1
            if retries >= max_retries:
                print(f"Max retries ({max_retries}) reached for network error. Last error: {e}")
                return full_json_response, total_count
            wait_time = 2**retries * 10 # Exponential backoff for network errors
            print(f"Encountered network error: {e}. Retrying in {wait_time} seconds ({retries}/{max_retries})...")
            time.sleep(wait_time)
        except Exception as e: # Catch-all for other exceptions
            print(f"Unexpected error during API request: {e}")
            return full_json_response, total_count # Stop on unexpected error


if __name__ == "__main__":
    start_date = "20220415"
    end_date = "20220513"  # Modified End Date

    # Convert the string to datetime objects
    start_date_obj = datetime.strptime(start_date, "%Y%m%d")
    end_date_obj = datetime.strptime(end_date, "%Y%m%d")

    # Load keywords and hashtags from file
    try:
        with open(KEYWORDS_HASHTAGS_FILE, 'r') as file:
            lines = [line.strip() for line in file if line.strip()]
        keywordsList = lines
        hashtagsList = lines # Using same list for both as per original script
    except FileNotFoundError:
        print(f"Error: Keyword/Hashtag file not found: {KEYWORDS_HASHTAGS_FILE}")
        sys.exit(1)

    # --- Obtain Access Token ---
    token_info = get_access_token(CLIENT_KEY, CLIENT_SECRET)
    if not token_info:
        print("Failed to obtain access token. Please check your client key and secret environment variables.")
        sys.exit(1)
    token_info['expires_at'] = time.time() + token_info['expires_in']
    print("Access token obtained successfully.")


    current_date_obj = start_date_obj  # Start date for loop
    while current_date_obj <= end_date_obj:  # Loop through the date range
        start_date_str = current_date_obj.strftime("%Y%m%d")
        next_date_obj = current_date_obj + timedelta(days=1)
        end_date_str = next_date_obj.strftime("%Y%m%d")
        print(f"\n--- Fetching data for date range: {start_date_str} to {end_date_str} ---")

        data, total = fetch_tiktok_data(start_date_str, end_date_str, keywordsList=keywordsList,
                                        hashtagsList=hashtagsList, token_info=token_info)
        print(f"Total videos fetched for {start_date_str}: {total}")

        # Save data only if videos were fetched
        if data and data['data']['videos']:
            json_filename = f'{start_date_str}_{end_date_str}_elections.json'
            save_to_json_file(data, json_filename)

            df = pd.DataFrame(data['data']['videos'])
            df['tiktokurl'] = df.apply(lambda row: create_tiktok_url(row['username'], row['id']), axis=1)
            df[['utc_year', 'utc_month', 'utc_day', 'utc_hour', 'utc_minute', 'utc_second', 'utc_date_string',
                'utc_time_string']] = df['create_time'].apply(convert_epoch_to_datetime)

            append_to_existing_or_create_new(df, COMBINED_CSV_FILENAME) # Removed daily_csv_filename_prefix
        else:
            print(f"No data found for {start_date_str}.")

        current_date_obj = next_date_obj # Increment date for next iteration
        print("Waiting before next date range...")
        time.sleep(60) # Added delay between date ranges, consider adjusting


    print("\n--- Script Completed. ---")