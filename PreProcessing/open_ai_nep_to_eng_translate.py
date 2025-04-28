import pandas as pd
import re
import openai
import os
from tqdm import tqdm
import time
import random

# Setup OpenAI client (latest SDK)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load data
df = pd.read_csv("Ktm_Election_Non_English.csv")
df = df.reset_index(drop=True)
#df = df.head(10000)  # Limit if needed for testing

# Regex for mentions and hashtags
mention_hashtag_pattern = r'([#@]\w+)'

def mask_special_tokens(text):
    tokens = re.findall(mention_hashtag_pattern, text)
    masked_text = re.sub(mention_hashtag_pattern, '[[MASK]]', text)
    return masked_text.strip(), tokens

def unmask_special_tokens(translated_text, tokens):
    for token in tokens:
        translated_text = translated_text.replace('[[MASK]]', token, 1)
    return translated_text.strip()

# GPT-4o call with retry logic
def translate_batch(prompt_text, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a translation assistant."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.3,
                max_tokens=1200  # Adjust for batch size
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Retry {attempt+1}/{retries} failed: {e}")
            time.sleep(random.uniform(2, 5))
    return ""

# Prepare translation list
translated_descriptions = []

batch_size = 10
for i in tqdm(range(0, len(df), batch_size)):
    batch = df.iloc[i:i+batch_size]
    masked_batch = []
    tokens_batch = []

    for desc in batch["video_description"].fillna(""):
        masked_text, tokens = mask_special_tokens(desc)
        masked_batch.append(masked_text)
        tokens_batch.append(tokens)

    # Prepare prompt
    prompt_lines = [
        f"[{j+1}] {text}" for j, text in enumerate(masked_batch)
    ]
    full_prompt = (
        "Translate the following texts to English while preserving hashtags and mentions like #tag and @user. "
        "Return them in the same format [1] ..., [2] ..., etc.:\n\n" +
        "\n".join(prompt_lines)
    )

    # Get response
    response_text = translate_batch(full_prompt)

    # Parse response into individual translations
    translations = []
    for line in response_text.split("\n"):
        match = re.match(r"\[\d+\]\s+(.*)", line.strip())
        if match:
            translations.append(match.group(1))
    # Fallback if formatting fails
    if len(translations) != len(masked_batch):
        print("⚠️ Warning: Response length mismatch, using empty strings for unmatched rows.")
        translations = [""] * len(masked_batch)

    # Unmask and store
    for translated, tokens in zip(translations, tokens_batch):
        final_text = unmask_special_tokens(translated, tokens)
        translated_descriptions.append(final_text)

    # Save checkpoint every 100 batches
    if i % 100 == 0 and i > 0:
        df_partial = df.iloc[:i+batch_size].copy()
        df_partial["translated_description"] = translated_descriptions
        df_partial.to_csv("checkpoint_translation_batching.csv", index=False)
        print(f"💾 Checkpoint saved at row {i+batch_size}")

# Save final result
df["translated_description"] = translated_descriptions
df.to_csv("KTM_Election_Translated_English.csv", index=False)
print("✅ Final translations saved to 'KTM_Election_Translated_English.csv'")
