"""
Debug script - Test video download and frame extraction
"""
import cv2
from pathlib import Path
import yt_dlp

# Test URL
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print("Testing video extraction...")
print(f"URL: {url}\n")

# Create temp directory
temp_dir = Path("backend/temp/test_debug")
temp_dir.mkdir(parents=True, exist_ok=True)

# Download video
print("1. Downloading video...")
ydl_opts = {
    'format': 'best[ext=mp4]/best',
    'outtmpl': str(temp_dir / 'video.%(ext)s'),
    'quiet': False,
    'no_warnings': False,
    'nocheckcertificate': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'player_skip': ['webpage', 'configs'],
        }
    },
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = Path(ydl.prepare_filename(info))
    
    print(f"✓ Downloaded: {video_path}")
    print(f"✓ File size: {video_path.stat().st_size} bytes")
    
    # Extract frames
    print("\n2. Extracting frames...")
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print("✗ Failed to open video!")
        exit(1)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"✓ FPS: {fps}")
    print(f"✓ Total frames: {total_frames}")
    print(f"✓ Duration: {duration:.1f} seconds")
    
    frames = []
    interval = int(fps)
    count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % interval == 0:
            frames.append(frame)
            # Save first frame as test
            if len(frames) == 1:
                test_img = temp_dir / "test_frame.jpg"
                cv2.imwrite(str(test_img), frame)
                print(f"✓ Saved test frame: {test_img}")
        count += 1
    
    cap.release()
    
    print(f"✓ Extracted {len(frames)} frames")
    
    # Test unique detection
    print("\n3. Testing unique detection...")
    import imagehash
    from PIL import Image
    
    unique = []
    last_hash = None
    
    for i, frame in enumerate(frames):
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        h = imagehash.phash(pil, hash_size=8)
        
        if last_hash is None or (h - last_hash) > 10:
            unique.append(frame)
            last_hash = h
            print(f"  Frame {i}: UNIQUE (hash: {h})")
        else:
            print(f"  Frame {i}: duplicate (diff: {h - last_hash})")
    
    print(f"\n✓ Found {len(unique)} unique frames")
    
    # Save all unique frames
    print("\n4. Saving unique frames...")
    for i, frame in enumerate(unique):
        img_path = temp_dir / f"unique_{i+1:03d}.jpg"
        cv2.imwrite(str(img_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"  Saved: {img_path.name}")
    
    print(f"\n✅ SUCCESS!")
    print(f"✅ Check folder: {temp_dir}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
