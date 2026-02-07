# Production Server Implementation Plan

## Current Status
✅ Simplified server working perfectly
✅ Extension UI functioning correctly
✅ Progress updates working

## Next: Enable Full Processing

### Step 1: Fix Dependencies (5 minutes)
We need to resolve the protobuf/TensorFlow conflicts:

```powershell
# Option A: Remove problematic dependencies (Recommended)
pip uninstall mediapipe tensorflow -y

# Option B: Fix versions (Advanced)
pip install protobuf==3.20.3 tensorflow==2.12.0 mediapipe==0.10.9
```

### Step 2: Make Services Synchronous (10 minutes)
The async/await mismatch needs fixing. Services should be sync, called from async wrapper.

### Step 3: Test Full Pipeline (15 minutes)
1. Download video with yt-dlp
2. Extract frames with OpenCV
3. Detect unique pages
4. Clean frames (Haar Cascade only, no Mediapipe)
5. OCR with Tesseract
6. Generate PDF

### Step 4: Gradual Rollout
Start with basic features, add complexity later:
- ✅ Phase 1: Video download + frame extraction
- ✅ Phase 2: Page detection
- ✅ Phase 3: Basic cleaning (no face detection)
- ✅ Phase 4: OCR
- ✅ Phase 5: PDF generation
- 🔜 Phase 6: Face detection (Haar only)
- 🔜 Phase 7: Re-enable Mediapipe (optional)

## Recommended Approach

### Quick Win: Minimal Production Version
Remove Mediapipe entirely, use only:
- yt-dlp for download
- OpenCV for frames
- Perceptual hashing for deduplication
- Tesseract for OCR
- ReportLab for PDF

This avoids ALL dependency conflicts!

### Files to Modify
1. `backend/requirements.txt` - Remove mediapipe, tensorflow
2. `backend/services/frame_cleaner.py` - Already done (Mediapipe disabled)
3. `backend/main.py` - Fix async/sync calls
4. `backend/services/*.py` - Remove async decorators

## Decision Point

**Option 1: Minimal (Recommended)**
- Remove Mediapipe/TensorFlow completely
- Use only Haar Cascades for face detection
- Faster, more stable, fewer dependencies
- ✅ Works on all systems
- ⚠️ Slightly less accurate face detection

**Option 2: Full Featured**
- Keep Mediapipe/TensorFlow
- Fix version conflicts
- Better face detection
- ⚠️ Complex dependencies
- ⚠️ May have compatibility issues

## Your Choice

Which approach would you like?

1. **Minimal Production** (recommended) - Remove Mediapipe, get it working now
2. **Full Featured** - Fix dependencies, keep all features
3. **Hybrid** - Start minimal, add Mediapipe later

Let me know and I'll implement it!
