# users_resume_improved_single_retry_split.py
# step 1
# install TikTokApi
# pip install playwright==1.37.0
# run playwright install
#step 2
#add the below code in : ../.venv/lib/python3.9/site-packages/TikTokApi/api/user.py
# if "userInfo" in keys and not data["userInfo"]:
#     # If userInfo is empty, save the username to a CSV file and exit
#     with open('empty_user_info.csv', mode='a', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         writer.writerow([self.username])
#     return
# Step 3
# To increase the timeout, you’ll need to modify the TikTokApi package directly,
# specifically where the wait_for_function is called within the generate_x_bogus method in the tiktok.py file.
# modify await session.page.wait_for_function("window.byted_acrawler !== undefined") to ->  await session.page.wait_for_function("window.byted_acrawler !== undefined", timeout=60000)  # 60 seconds timeout


from TikTokApi import TikTokApi
import asyncio
import os
import csv
import pandas as pd
import time
import random  # For introducing randomness in delays
import sys # For command line arguments

# Retrieve the ms_token from environment variables
ms_token = os.environ.get("ms_token", None)

# --- Configuration ---
BASE_DELAY = 5  # Base delay in seconds, increased from 2 seconds
MAX_RETRIES = 1    # Maximum retries for fetching user info - REDUCED TO 1
INITIAL_RETRY_DELAY = 10 # Initial retry delay in seconds


# Function to fetch user information and save it to a CSV file
async def fetch_user_info(usernames, output_file, error_file, private_account_file):
    print("function called")
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, headless=False, override_browser_args=["--incognito"])

        with open(output_file, mode='a', newline='', encoding='utf-8') as output_csvfile: # Renamed file object to output_csvfile
            writer = csv.writer(output_csvfile)
            # Write header only if the file is empty
            if os.stat(output_file).st_size == 0:
                writer.writerow(['display_name', 'followers', 'following', 'Like_count', 'Video_count', 'nickname', 'verified'])  # Write header
            print(f"Output file opened successfully: {output_file}") # Modified message to include filename

            # Open error file to log usernames that cause errors
            with open(error_file, mode='a', newline='', encoding='utf-8') as error_csvfile: # Renamed file object to error_csvfile
                error_writer = csv.writer(error_csvfile)
                # Write header only if the file is empty
                if os.stat(error_file).st_size == 0:
                    error_writer.writerow(['username', 'error'])  # Header for error file
                print(f"Error file opened successfully: {error_file}") # Added print statement

                # Open private accounts file to log private/empty user info usernames
                with open(private_account_file, mode='a', newline='', encoding='utf-8') as private_csvfile: # Renamed file object to private_csvfile
                    private_writer = csv.writer(private_csvfile)
                    # (Optional: Write header for private_accounts.csv only if file is newly created)
                    if os.stat(private_account_file).st_size == 0:
                        private_writer.writerow(['username'])
                    print(f"Private account file opened successfully: {private_account_file}") # Added print statement


                    for username in usernames:
                        retries = 0
                        retry_delay = INITIAL_RETRY_DELAY

                        while retries <= MAX_RETRIES: # Now MAX_RETRIES is 1
                            try:
                                user = api.user(username)
                                user_data = await user.info()

                                # Check if userInfo is empty
                                    # Check if userInfo is empty (likely private account)
                                if not user_data.get("userInfo"):
                                    print(f"Skipping private/empty user info for: {username}") # Optional print
                                    private_writer.writerow([username]) # Log username to private_accounts.csv
                                    break # Move to next username

                                # Extract relevant information
                                display_name = username
                                followers = user_data['userInfo']['stats']['followerCount']
                                following = user_data['userInfo']['stats']['followingCount']
                                like = user_data['userInfo']['stats']['heart']
                                video = user_data['userInfo']['stats']['videoCount']
                                nickname = user_data['userInfo']['user']['nickname']
                                verified = user_data['userInfo']['user']['verified']
                                print("user fetched successfully", display_name)

                                # Write user data to CSV
                                writer.writerow([display_name, followers, following, like, video, nickname, verified])
                                break # Success, move to next username

                            except Exception as e:
                                print(f"Error fetching data for {username} (Retry {retries+1}/{MAX_RETRIES}): {e}") # Message adjusted for single retry
                                if retries < MAX_RETRIES: # Will only retry once now
                                    retries += 1
                                    wait_time = retry_delay + random.uniform(0, retry_delay) # Introduce randomness
                                    print(f"Waiting {wait_time:.2f} seconds before retrying once...") # Adjusted message
                                    time.sleep(wait_time)
                                    retry_delay *= 2 # Exponential backoff for retry delay (still applied for the single retry)
                                else:
                                    # Log the username and error message to the error file after max retries
                                    error_writer.writerow([username, str(e)])
                                    print(f"Single retry failed for {username}. Logging error and moving to next username.") # Adjusted message
                                    break # Move to next username after max retries (explicit break here)
                        else: # else block for the while loop, executed if the loop completes without break (which should not happen in current logic, but for safety)
                            print(f"Retry loop completed without success or explicit break for {username}. This should not happen, check logic.") # Unchanged

                        time.sleep(BASE_DELAY + random.uniform(0, BASE_DELAY)) # Introduce randomness to base delay


async def process_csv_files(csv_file): # Modified to take single csv_file as argument
    df = pd.read_csv(csv_file) # csv_file is now directly a file path
    all_usernames = df['username'].unique()
    print(f"Total unique users in {csv_file} are:", all_usernames.shape[0]) # Modified print statement
    output_file_base = "user_info_Updated_LocalElection_22" # Base name for output file
    output_file = f"{output_file_base}_{os.path.basename(csv_file)}" # Output file name now includes split file name
    error_file = f"errors_{os.path.basename(csv_file)}"
    private_account_file = f"private_accounts_{os.path.basename(csv_file)}" # Private account file also specific to split

    # --- Resume Logic ---
    processed_usernames = set()
    if os.path.exists(output_file):
        try:
            output_df = pd.read_csv(output_file)
            processed_usernames = set(output_df['display_name'].tolist()) # Assuming 'display_name' is username in output
            print(f"Resuming from previous run. Found {len(processed_usernames)} already processed users in {output_file}.") # Modified message to include filename
        except pd.errors.EmptyDataError:
            print(f"Output file {output_file} is empty. Starting from scratch.") # Modified message to include filename
        except FileNotFoundError: # Should not happen as we checked os.path.exists, but for robustness.
            print(f"Output file {output_file} not found (though existence was checked). Starting from scratch.") # Modified message to include filename

    usernames_to_process = [username for username in all_usernames if username not in processed_usernames]
    print(f"Number of users to process in this run (from {csv_file}): {len(usernames_to_process)}") # Modified message to include csv_file
    # --- End Resume Logic ---


    # Write headers for error and private account files ONCE per CSV file processing
    if not os.path.exists(error_file) or os.stat(error_file).st_size == 0: # Check if error file needs header
        with open(error_file, mode='w', newline='', encoding='utf-8') as error_file_header_check: # Open in write mode for header check
            error_writer_header = csv.writer(error_file_header_check)
            error_writer_header.writerow(['username', 'error']) # Write header for error file
            print(f"Header written to error file: {error_file}") # Added print statement

    if not os.path.exists(private_account_file) or os.stat(private_account_file).st_size == 0: # Check if private account file needs header
        with open(private_account_file, mode='w', newline='', encoding='utf-8') as private_file_header_check: # Open in write mode for header check
            private_writer_header = csv.writer(private_file_header_check)
            private_writer_header.writerow(['username']) # Write header for private account file
            print(f"Header written to private account file: {private_account_file}") # Added print statement


    await fetch_user_info(usernames_to_process, output_file, error_file, private_account_file) # Process only remaining usernames
    print(f"Finished processing CSV file: {csv_file}. Output saved to {output_file}, errors to {error_file}, private accounts to {private_account_file}") # Added completion message


if __name__ == "__main__":
    csv_file_path = sys.argv[1] if len(sys.argv) > 1 else None # Get CSV file path from command line

    if csv_file_path:
        csv_files = [csv_file_path] # List containing only the provided CSV file
        asyncio.run(process_csv_files(csv_files[0])) # Pass single csv_file path to process_csv_files
    else:
        print("Error: Please provide the split CSV file path as a command line argument.")
        print("Usage: python users_resume_improved_single_retry_split.py <split_csv_file_path>")