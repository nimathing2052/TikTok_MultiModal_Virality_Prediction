# users_official_api_with_client_auth.py
import requests
import json
import csv
import os
import pandas as pd
import time

# --- Configuration ---
API_BASE_URL = "https://open.tiktokapis.com/v2/research/user/info/"
DESIRED_FIELDS = "display_name,bio_description,avatar_url,is_verified,follower_count,following_count,likes_count,video_count,bio_url"
REQUEST_DELAY = 2  # Delay in seconds between requests to avoid rate limiting

CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY") # Get client key from environment variable
CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET") # Get client secret from environment variable
ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN")  # Try to get access token from environment variable first


def get_access_token(client_key, client_secret):
    """
    Fetches the Research API access token using client key and secret.

    Args:
        client_key (str): Key is copied from TikTok's developer portal
        client_secret (str): Secret is copied from TikTok's developer portal

    Returns:
        str or None: Access token string if successful, None otherwise.
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
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
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


def fetch_user_info_official_api(username, access_token):
    """
    Fetches user information from TikTok Official API for a given username using provided access token.

    Args:
        username (str): TikTok username.
        access_token (str): TikTok API access token.

    Returns:
        dict or None: User data as a dictionary if successful, None otherwise.
                      Returns also None if the response indicates an error or private account.
    """
    if not access_token:
        print("Error: No access token provided.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "fields": DESIRED_FIELDS
    }
    data = {
        "username": username
    }

    try:
        response = requests.post(API_BASE_URL, headers=headers, params=params, json=data)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        response_json = response.json()

        if response_json.get("error") and response_json["error"]["code"] != "ok":
            print(f"API Error for {username}: {response_json['error']['message']}")
            if response_json["error"]["code"] == "user_not_found" or "private" in response_json["error"]["message"].lower():
                 return None # Treat as private/not found for our purpose, log it later.
            return None # General API error

        if response_json.get("data"):
            return response_json["data"]
        else:
            print(f"No 'data' found in API response for {username}. Response: {response_json}")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error for {username}: {http_err}, Response: {response.text}")
        if response.status_code == 404: # Handle 404 as potentially private/deleted account
            return None
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error for {username}: {req_err}")
        return None
    except json.JSONDecodeError as json_err:
        print(f"JSON decode error for {username}: {json_err}, Response: {response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for {username}: {e}")
        return None



def process_usernames(usernames, output_file, error_file, private_account_file, access_token):
    """
    Processes a list of usernames to fetch user information and save it to CSV files.

    Args:
        usernames (list): List of TikTok usernames.
        output_file (str): Path to the output CSV file for user information.
        error_file (str): Path to the error CSV file for usernames with errors.
        private_account_file (str): Path to the CSV file for private or not found accounts.
        access_token (str): TikTok API access token.
    """
    print("Starting to fetch user information using Official TikTok API...")

    with open(output_file, mode='w', newline='', encoding='utf-8') as output_csvfile, \
         open(error_file, mode='w', newline='', encoding='utf-8') as error_csvfile, \
         open(private_account_file, mode='a', newline='', encoding='utf-8') as private_csvfile:

        output_writer = csv.writer(output_csvfile)
        error_writer = csv.writer(error_csvfile)
        private_writer = csv.writer(private_csvfile)

        # Write headers if files are newly created or empty (optional, but good practice)
        if os.stat(output_file).st_size == 0:
            output_writer.writerow(['display_name', 'bio_description', 'avatar_url', 'is_verified', 'follower_count', 'following_count', 'likes_count', 'video_count', 'bio_url', 'username'])
        if os.stat(error_file).st_size == 0:
            error_writer.writerow(['username', 'error_message'])
        if os.stat(private_account_file).st_size == 0: # Only write header if the file is empty at the beginning.
            private_writer.writerow(['username'])


        for username in usernames:
            print(f"Fetching information for: {username}")
            user_data = fetch_user_info_official_api(username, access_token)

            if user_data:
                output_writer.writerow([
                    user_data.get('display_name'),
                    user_data.get('bio_description'),
                    user_data.get('avatar_url'),
                    user_data.get('is_verified'),
                    user_data.get('follower_count'),
                    user_data.get('following_count'),
                    user_data.get('likes_count'),
                    user_data.get('video_count'),
                    user_data.get('bio_url'),
                    username # Add username for reference
                ])
                print(f"Information fetched and saved for: {username}")
            elif user_data is None: # Explicitly check for None, meaning error or private
                 private_writer.writerow([username]) # Log as private/error
                 print(f"Could not fetch public information for or private account: {username}. Logged to private account file.")
            else: # Should ideally not reach here, but for completeness
                error_writer.writerow([username, "Unknown error fetching user info"]) # Log general errors if any.
                print(f"Error fetching information for {username}. Check error file.")


            time.sleep(REQUEST_DELAY) # Delay to be respectful to the API


# --- Modified process_csv_files function ---
def process_csv_files(csv_files, access_token):
    """
    Processes CSV files, resumes from previous runs by checking output file,
    and fetches user information.

    Args:
        csv_files (list): List of paths to CSV files containing usernames.
        access_token (str): TikTok API access token.
    """
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        all_usernames = df['username'].unique().tolist() # All usernames from input CSV
        print(f"Processing CSV file: {csv_file}")
        print(f"Total unique users in input CSV: {len(all_usernames)}")

        output_file = f"Final_user_info_official_api_{os.path.basename(csv_file)}"
        error_file = f"final_errors_official_api_{os.path.basename(csv_file)}"
        private_account_file = "final_private_accounts_official_api.csv" # Consistent private account file name

        # --- Check for already processed usernames ---
        processed_usernames = set() # Use a set for efficient lookup
        if os.path.exists(output_file) and os.stat(output_file).st_size > 0: # Check if output file exists and is not empty
            try:
                output_df = pd.read_csv(output_file)
                processed_usernames = set(output_df['username'].tolist()) # Get usernames from output file
                print(f"Resuming from previous run. Found {len(processed_usernames)} already processed users in {output_file}.")
            except pd.errors.EmptyDataError:
                print(f"Output file {output_file} is empty. Starting from scratch.")
            except FileNotFoundError: # Should not happen as we checked os.path.exists, but for robustness.
                print(f"Output file {output_file} not found (though existence was checked). Starting from scratch.")


        # --- Filter out already processed usernames ---
        usernames_to_process = [username for username in all_usernames if username not in processed_usernames]
        print(f"Number of users to process in this run: {len(usernames_to_process)}")

        if not usernames_to_process:
            print("All usernames from input CSV have already been processed (or are in output/private/error files). Nothing to do.")
            continue # Skip to next CSV file if no users to process


        # --- Create error and private account files and write headers if they don't exist or are empty ---
        if not os.path.exists(error_file) or os.stat(error_file).st_size == 0:
            with open(error_file, mode='w', newline='', encoding='utf-8') as error_header_file:
                error_writer_header = csv.writer(error_header_file)
                error_writer_header.writerow(['username', 'error_message'])

        if not os.path.exists(private_account_file) or os.stat(private_account_file).st_size == 0:
            with open(private_account_file, mode='w', newline='', encoding='utf-8') as private_header_file:
                private_writer_header = csv.writer(private_header_file)
                private_writer_header.writerow(['username'])


        process_usernames(usernames_to_process, output_file, error_file, private_account_file, access_token)
        print(f"Finished processing {csv_file}. Output saved to {output_file}, errors to {error_file}, private accounts to {private_account_file}")


if __name__ == "__main__":
    # --- Get Access Token ---
    if ACCESS_TOKEN: # If access token is already in environment variable, use it.
        print("Using access token from environment variable TIKTOK_ACCESS_TOKEN.")
    elif CLIENT_KEY and CLIENT_SECRET: # If client key and secret are in environment variables, fetch token.
        print("Fetching access token using client key and secret from environment variables...")
        ACCESS_TOKEN = get_access_token(CLIENT_KEY, CLIENT_SECRET)
        if not ACCESS_TOKEN:
            print("Failed to retrieve access token. Please check your client key and secret, and ensure environment variables TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET are set correctly.")
            exit()
        print("Access token retrieved successfully.")
    else: # If none are available, exit with instructions.
        print("Error: No access token, client key, or client secret provided.")
        print("Please set either the TIKTOK_ACCESS_TOKEN environment variable, or both TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET environment variables.")
        exit()


    # --- Process CSV files ---
    csv_files = ["split_csv_files/split_part_5.csv"] # Replace with your CSV file(s)
    process_csv_files(csv_files, ACCESS_TOKEN)
    print("Script execution completed.")