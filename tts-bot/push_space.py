"""Create HF Space and push Kokoro files."""
import os
from huggingface_hub import HfApi

TOKEN = os.getenv("HF_TOKEN")
if not TOKEN:
    print("HF_TOKEN env variable required!")
    exit(1)

SPACE_NAME = "omonill/kokoro-tts"
LOCAL_DIR = os.path.join(os.path.dirname(__file__), "kokoro-space")

api = HfApi(token=TOKEN)

print(f"Creating Space: {SPACE_NAME}")
api.create_repo(
    SPACE_NAME,
    repo_type="space",
    space_sdk="docker",
    exist_ok=True,
)
print("Space created!")

print("Uploading files...")
for fname in ["main.py", "Dockerfile", "requirements.txt", "README.md"]:
    fpath = os.path.join(LOCAL_DIR, fname)
    print(f"  Uploading {fname}...")
    api.upload_file(
        path_or_fileobj=fpath,
        path_in_repo=fname,
        repo_id=SPACE_NAME,
        repo_type="space",
    )

print("Done! All files uploaded.")
print(f"Space URL: https://huggingface.co/spaces/{SPACE_NAME}")
