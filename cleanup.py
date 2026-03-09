import os
import glob

deleted = 0
for f in glob.glob("**/*.mp3", recursive=True):
    try:
        os.remove(f)
        print(f"Deleted: {f}")
        deleted += 1
    except Exception as e:
        print(f"Could not delete {f}: {e}")

print(f"\nDone — {deleted} MP3 files removed.")