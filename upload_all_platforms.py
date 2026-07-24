import os, sys, glob
from upload.upload_instagram import upload_to_instagram
from upload.upload_facebook import upload_to_facebook

def main():
    print("Starting Multi-Platform Video Publisher...")
    processed_dir = "Processed_Videos"
    videos = []
    if os.path.exists(processed_dir):
        videos = [os.path.join(processed_dir, f) for f in os.listdir(processed_dir) if f.endswith(".mp4")]
    if not videos:
        # Search output temp
        videos = glob.glob("output/**/*.mp4", recursive=True)
    
    if not videos:
        print("No videos found to upload.")
        return

    latest_video = max(videos, key=os.path.getmtime)
    print(f"Selected Video: {latest_video}")

    caption = "Daily automated video release #viral #reels"
    
    print("\n1. Uploading to Instagram...")
    upload_to_instagram(latest_video, caption=caption)
    
    print("\n2. Uploading to Facebook...")
    upload_to_facebook(latest_video, caption=caption)

if __name__ == "__main__":
    main()
