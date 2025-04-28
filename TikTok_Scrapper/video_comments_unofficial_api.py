# video_comments_unofficial_api_resume.py
from TikTokApi import TikTokApi
import asyncio
import os
import csv
import pandas as pd
import time
import random

# --- Configuration ---
ms_token = os.environ.get("ms_token", None)  # Retrieve the ms_token from environment variables
BASE_DELAY = 5  # Base delay in seconds
MAX_RETRIES = 1    # Maximum retries for fetching comments
INITIAL_RETRY_DELAY = 3 # Initial retry delay in seconds
OUTPUT_COMMENTS_FILE = "video_comments_unofficial_api_user_id_output.csv" # Output file for comments
ERROR_COMMENTS_FILE = "video_comments_unofficial_api_user_id_error.csv" # Error file
NO_COMMENTS_FILE = "video_comments_unofficial_api_user_id_No_comments.csv" # File for videos with no comments

async def fetch_video_comments(video_id, output_file, error_file, no_comments_file):
    print(f"Fetching comments for video ID: {video_id}")
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, headless=False, override_browser_args=["--incognito", "--window-position=-1440,-447","--windows-size=800,600"])

        with open(output_file, mode='a', newline='', encoding='utf-8') as output_csvfile:
            comment_writer = csv.writer(output_csvfile)
            if os.stat(output_file).st_size == 0:
                comment_writer.writerow(['comment_id', 'video_id', 'text', 'like_count', 'reply_count', 'create_time', 'author_username', 'author_nickname', 'author_user_id'])

            with open(error_file, mode='a', newline='', encoding='utf-8') as error_csvfile:
                error_writer = csv.writer(error_csvfile)
                if os.stat(error_file).st_size == 0:
                    error_writer.writerow(['video_id', 'error_message'])

                with open(no_comments_file, mode='a', newline='', encoding='utf-8') as no_comments_csvfile:
                    no_comments_writer = csv.writer(no_comments_csvfile)
                    if os.stat(no_comments_file).st_size == 0:
                        no_comments_writer.writerow(['video_id'])

                    retries = 0
                    retry_delay = INITIAL_RETRY_DELAY

                    while retries <= MAX_RETRIES:
                        try:
                            video = api.video(id=video_id)
                            comments = []
                            async for comment in video.comments(count=30): # Adjust count if needed, but 30 is reasonable
                                comments.append(comment.as_dict)

                            if comments:
                                print(f"Fetched {len(comments)} comments for video ID: {video_id}")
                                for comment_data in comments:
                                            comment_writer.writerow([
                                                comment_data.get('cid'),          # Corrected: Use 'cid' to get comment ID
                                                video_id,
                                                comment_data.get('text'),
                                                comment_data.get('like_count'),
                                                comment_data.get('reply_count'),
                                                comment_data.get('create_time'),
                                                comment_data.get('author', {}).get('username'),
                                                comment_data.get('author', {}).get('nickname'),
                                                comment_data.get('author', {}).get('user_id')
                                            ])
                                break # Success, move to next video

                            else:
                                no_comments_writer.writerow([video_id])
                                print(f"No comments found for video ID: {video_id}. Logged to no_comments file.")
                                break # No comments, move to next video

                        except Exception as e:
                            print(f"Error fetching comments for video ID {video_id} (Retry {retries+1}/{MAX_RETRIES}): {e}")
                            if retries < MAX_RETRIES:
                                retries += 1
                                wait_time = retry_delay + random.uniform(0, retry_delay)
                                print(f"Waiting {wait_time:.2f} seconds before retrying...")
                                time.sleep(wait_time)
                                retry_delay *= 2
                            else:
                                error_writer.writerow([video_id, str(e)])
                                print(f"Max retries reached for video ID {video_id}. Logging error and moving to next video.")
                                break
                        time.sleep(BASE_DELAY + random.uniform(0, BASE_DELAY)) # Delay after each video


async def process_csv_files(csv_files):
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        all_video_ids = df['video_id'].unique().astype(str).tolist() # Ensure video_ids are strings and convert to list
        print(f"Total unique video IDs are:", len(all_video_ids)) # Use len() for list

        output_file = OUTPUT_COMMENTS_FILE
        error_file = ERROR_COMMENTS_FILE
        no_comments_file = NO_COMMENTS_FILE

        # --- Resume Logic ---
        processed_video_ids = set()
        if os.path.exists(output_file):
            try:
                output_df = pd.read_csv(output_file)
                processed_video_ids = set(output_df['video_id'].astype(str).tolist())
                print(f"Resuming from previous run. Found {len(processed_video_ids)} already processed video IDs in {output_file}.")
            except pd.errors.EmptyDataError:
                print(f"Output file {output_file} is empty. Starting from scratch.")
            except FileNotFoundError:
                print(f"Output file {output_file} not found (though existence was checked). Starting from scratch.")

        video_ids_to_process = [video_id for video_id in all_video_ids if video_id not in processed_video_ids]
        print(f"Number of video IDs to process in this run: {len(video_ids_to_process)}")
        # --- End Resume Logic ---

        # Write headers if files are newly created
        if not os.path.exists(error_file) or os.stat(error_file).st_size == 0:
            with open(error_file, 'w', newline='', encoding='utf-8') as error_header_check:
                error_writer_header = csv.writer(error_header_check)
                error_writer_header.writerow(['video_id', 'error_message'])

        if not os.path.exists(no_comments_file) or os.stat(no_comments_file).st_size == 0:
            with open(no_comments_file, 'w', newline='', encoding='utf-8') as no_comments_header_check:
                no_comments_writer_header = csv.writer(no_comments_header_check)
                no_comments_writer_header.writerow(['video_id'])

        # --- Corrected: Iterate and call fetch_video_comments for each video_id ---
        for video_id in video_ids_to_process: # Iterate through the list
            await fetch_video_comments(video_id, output_file, error_file, no_comments_file) # Call for each video_id

if __name__ == "__main__":
    csv_files = ["filtered_video_ids_part1.csv"] # Replace with your CSV file containing 'video_id' column
    asyncio.run(process_csv_files(csv_files))
    print("Script execution completed.")