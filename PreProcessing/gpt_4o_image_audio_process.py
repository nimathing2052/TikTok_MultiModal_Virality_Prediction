import os
import base64
import csv
import time
from pathlib import Path
from openai import OpenAI
from moviepy.editor import VideoFileClip
from PIL import Image
import numpy as np

# --- Setup ---
VIDEO_DIR = "./videos"
AUDIO_DIR = "./audio"
IMAGE_DIR = "./images"
OUTPUT_CSV = "./results/gpt4o_analysis.csv"

Path(AUDIO_DIR).mkdir(exist_ok=True)
Path(IMAGE_DIR).mkdir(exist_ok=True)
Path("./results").mkdir(exist_ok=True)

client = OpenAI()

# --- Helper Functions ---
def extract_audio_and_image(video_path, video_id):
    audio_path = os.path.join(AUDIO_DIR, f"{video_id}.wav")
    image_path = os.path.join(IMAGE_DIR, f"{video_id}.jpg")

    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path, logger=None)

    frame = clip.get_frame(3.0)  # Extract frame at 3 seconds
    Image.fromarray(np.uint8(frame)).save(image_path)

    return audio_path, image_path

def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file
        )
    return transcription.text

def analyze_image(image_path):
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    { "type": "text", "text": "What is in this image?" },
                    { "type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}" } }
                ],
            }
        ],
    )
    return completion.choices[0].message.content

# --- Load processed video IDs if CSV exists ---
processed_ids = set()
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            processed_ids.add(row["video_id"])

# --- Process Videos ---
video_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]

with open(OUTPUT_CSV, "a", newline='', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["video_id", "audio_transcript", "image_analysis"])
    if os.stat(OUTPUT_CSV).st_size == 0:
        writer.writeheader()  # Write headers if file is empty

    for video_file in video_files:
        try:
            video_id = video_file.split("_")[1]
            if video_id in processed_ids:
                print(f"Skipping {video_id} (already processed)")
                continue

            print(f"Processing {video_id}...")

            video_path = os.path.join(VIDEO_DIR, video_file)
            audio_path, image_path = extract_audio_and_image(video_path, video_id)

            audio_text = transcribe_audio(audio_path)
            image_desc = analyze_image(image_path)

            writer.writerow({
                "video_id": video_id,
                "audio_transcript": audio_text,
                "image_analysis": image_desc
            })

            processed_ids.add(video_id)
            time.sleep(1.5)  # Optional: rate limit

        except Exception as e:
            print(f"Error processing {video_file}: {e}")
