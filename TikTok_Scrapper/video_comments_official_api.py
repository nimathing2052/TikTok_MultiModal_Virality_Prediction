# video_comments_official_api_with_client_auth.py
import requests
import json
import csv
import os
import pandas as pd
import time

# --- Configuration ---
API_BASE_URL = "https://open.tiktokapis.com/v2/research/video/comment/list/"
DESIRED_FIELDS = "id,video_id,text,like_count,reply_count,parent_comment_id,create_time"
REQUEST_DELAY = 2  # Delay in seconds between requests to avoid rate limiting
MAX_COMMENTS_PER_REQUEST = 100 # Maximum allowed by API

CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET")
ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN")


def get_access_token(client_key, client_secret):
    """
    Fetches the Research API access token using client key and secret.
    (Same function as in users_official_api_with_client_auth.py)
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
        return response_json.get('access_token')
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


def fetch_video_comments_official_api(video_id, access_token):
    """
    Fetches all comments for a given video ID using TikTok Official API, handling pagination.

    Args:
        video_id (str or int): TikTok video ID.
        access_token (str): TikTok API access token.

    Returns:
        list or None: List of comment dictionaries if successful, None otherwise.
    """
    if not access_token:
        print("Error: No access token provided.")
        return None

    all_comments = []
    cursor = 0
    has_more = True

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "fields": DESIRED_FIELDS
    }

    while has_more:
        data = {
            "video_id": int(video_id), # Ensure video_id is integer
            "max_count": MAX_COMMENTS_PER_REQUEST,
            "cursor": cursor
        }

        try:
            response = requests.post(API_BASE_URL, headers=headers, params=params, json=data)
            response.raise_for_status()
            response_json = response.json()

            if response_json.get("error") and response_json["error"]["code"] != "ok":
                print(f"API Error for video_id {video_id}: {response_json['error']['message']}")
                return None # Indicate error fetching comments for this video

            if response_json.get("data") and response_json["data"].get("comments"):
                comments = response_json["data"]["comments"]
                all_comments.extend(comments)
                cursor = response_json["data"].get("cursor", 0) # Get next cursor, default to 0 if not present
                has_more = response_json["data"].get("has_more", False) # Check if there are more comments
            else:
                has_more = False # No comments or 'data'/'comments' in response, stop pagination

            time.sleep(REQUEST_DELAY) # Respect rate limit

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error for video_id {video_id}: {http_err}, Response: {response.text}")
            return None # Indicate error fetching comments for this video
        except requests.exceptions.RequestException as req_err:
            print(f"Request error for video_id {video_id}: {req_err}")
            return None # Indicate error fetching comments for this video
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error for video_id {video_id}: {json_err}, Response: {response.text}")
            return None # Indicate error fetching comments for this video
        except Exception as e:
            print(f"An unexpected error occurred for video_id {video_id}: {e}")
            return None # Indicate error fetching comments for this video

    return all_comments


def process_video_ids(video_ids, output_file, error_file, no_comments_file, access_token):
    """
    Processes a list of video IDs to fetch comments and save them to CSV files.

    Args:
        video_ids (list): List of TikTok video IDs.
        output_file (str): Path to the output CSV file for comments.
        error_file (str): Path to the error CSV file for video IDs with errors.
        no_comments_file (str): Path to the CSV file for video IDs with no comments.
        access_token (str): TikTok API access token.
    """
    print("Starting to fetch video comments using Official TikTok API...")

    with open(output_file, mode='a', newline='', encoding='utf-8') as output_csvfile, open(error_file, mode='a', newline='', encoding='utf-8') as error_csvfile, open(no_comments_file, mode='a', newline='', encoding='utf-8') as no_comments_csvfile: 

        output_writer = csv.writer(output_csvfile)
        error_writer = csv.writer(error_csvfile)
        no_comments_writer = csv.writer(no_comments_csvfile)

        # Write headers if files are newly created or empty (optional, but good practice)
        if os.stat(output_file).st_size == 0:
            output_writer.writerow(['comment_id', 'video_id', 'text', 'like_count', 'reply_count', 'parent_comment_id', 'create_time'])
        if os.stat(error_file).st_size == 0:
            error_writer.writerow(['video_id', 'error_message'])
        if os.stat(no_comments_file).st_size == 0:
            no_comments_writer.writerow(['video_id'])


        for video_id in video_ids:
            print(f"Fetching comments for video ID: {video_id}")
            comments = fetch_video_comments_official_api(video_id, access_token)

            if comments:
                if comments: # Check if comments list is not empty
                    print(f"Fetched {len(comments)} comments for video ID: {video_id}")
                    for comment in comments:
                        output_writer.writerow([
                            comment.get('id'),
                            comment.get('video_id'),
                            comment.get('text'),
                            comment.get('like_count'),
                            comment.get('reply_count'),
                            comment.get('parent_comment_id'),
                            comment.get('create_time')
                        ])
                else:
                    no_comments_writer.writerow([video_id]) # Log video IDs with no comments (empty list returned)
                    print(f"No comments found for video ID: {video_id}. Logged to no_comments file.")

            elif comments is None: # Explicitly check for None, meaning error
                error_writer.writerow([video_id, "Error fetching comments from API"])
                print(f"Error fetching comments for video ID: {video_id}. Check error file.")
            else: # Should ideally not reach here, but for completeness
                error_writer.writerow([video_id, "Unknown error during comment fetching"])
                print(f"Unknown error fetching comments for video ID: {video_id}. Check error file.")

            time.sleep(REQUEST_DELAY) # Respect rate limit


def process_csv_files(csv_files, access_token):
    """
    Processes a list of CSV files, extracts video IDs, and fetches comments.

    Args:
        csv_files (list): List of paths to CSV files containing video IDs.
        access_token (str): TikTok API access token.
    """
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        video_ids = df['video_id'].unique().astype(str).tolist() # Ensure video_ids are strings
        print(f"Processing CSV file: {csv_file}")
        print(f"Total unique video IDs to fetch comments for: {len(video_ids)}")

        output_file = f"video_comments_official_api_user_id_official.csv"
        error_file = f"errors_comments_official_api_user_id_official.csv"
        #no_comments_file = f"no_comments_official_api_{os.path.basename(csv_file)}" # File to log video IDs with no comments
        no_comments_file = f"no_comments_official_api_user_id_official.csv" # File to log video IDs with no comments

        # --- Check for already processed video IDs (resume logic) ---
        processed_video_ids = set()
        if os.path.exists(output_file) and os.stat(output_file).st_size > 0:
            try:
                output_df = pd.read_csv(output_file)
                processed_video_ids = set(output_df['video_id'].astype(str).tolist()) # Video IDs from output, ensure string
                print(f"Resuming from previous run. Found comments already fetched for {len(processed_video_ids)} video IDs in {output_file}.")
            except pd.errors.EmptyDataError:
                print(f"Output file {output_file} is empty. Starting from scratch.")
            except FileNotFoundError:
                print(f"Output file {output_file} not found (though existence was checked). Starting from scratch.")

        video_ids_to_process = [video_id for video_id in video_ids if video_id not in processed_video_ids]
        print(f"Number of video IDs to process in this run: {len(video_ids_to_process)}")

        if not video_ids_to_process:
            print("All video IDs from input CSV have already been processed (or are in output/error/no_comments files). Nothing to do.")
            continue


        # --- Create error and no_comments files and write headers if they don't exist or are empty ---
        if not os.path.exists(error_file) or os.stat(error_file).st_size == 0:
            with open(error_file, mode='w', newline='', encoding='utf-8') as error_header_file:
                error_writer_header = csv.writer(error_header_file)
                error_writer_header.writerow(['video_id', 'error_message'])

        if not os.path.exists(no_comments_file) or os.stat(no_comments_file).st_size == 0:
            with open(no_comments_file, mode='w', newline='', encoding='utf-8') as no_comments_header_file:
                no_comments_writer_header = csv.writer(no_comments_header_file)
                no_comments_writer_header.writerow(['video_id'])


        process_video_ids(video_ids_to_process, output_file, error_file, no_comments_file, access_token)
        print(f"Finished processing {csv_file}. Comments saved to {output_file}, errors to {error_file}, no comments video IDs to {no_comments_file}")


if __name__ == "__main__":
    # --- Get Access Token ---
    if ACCESS_TOKEN:
        print("Using access token from environment variable TIKTOK_ACCESS_TOKEN.")
    elif CLIENT_KEY and CLIENT_SECRET:
        print("Fetching access token using client key and secret from environment variables...")
        ACCESS_TOKEN = get_access_token(CLIENT_KEY, CLIENT_SECRET)
        if not ACCESS_TOKEN:
            print("Failed to retrieve access token. Please check your client key and secret, and ensure environment variables TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET are set correctly.")
            exit()
        print("Access token retrieved successfully.")
    else:
        print("Error: No access token, client key, or client secret provided.")
        print("Please set either the TIKTOK_ACCESS_TOKEN environment variable, or both TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET environment variables.")
        exit()

    # --- Process CSV files ---
    csv_files = ["filtered_video_ids_part_official.csv"] # Replace with your CSV file(s) containing 'video_id' column
    process_csv_files(csv_files, ACCESS_TOKEN)
    print("Script execution completed.")