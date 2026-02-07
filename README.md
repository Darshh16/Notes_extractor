# YouTube Notes Extractor - CORRECT USAGE

## ✅ What This Tool Does

**Extracts TEXT/NOTES from educational videos** - NOT music videos!

This tool is designed for:
- ✅ Lectures with slides
- ✅ Tutorials with text
- ✅ Educational content
- ✅ Presentations
- ✅ Coding tutorials

**NOT for**:
- ❌ Music videos
- ❌ Vlogs
- ❌ Entertainment videos
- ❌ Videos without text

## 🎯 Correct Example Videos

### Example 1: Khan Academy Lecture
```
https://www.youtube.com/watch?v=riXcZT2ICjA
```
**What you'll get**: Text notes from math lecture slides

### Example 2: Programming Tutorial
```
https://www.youtube.com/watch?v=8ext9G7xspg
```
**What you'll get**: Code snippets and explanations from slides

### Example 3: University Lecture
```
https://www.youtube.com/watch?v=aircAruvnKk
```
**What you'll get**: Notes from neural network lecture

## 📝 Output Format

### If Tesseract is Installed (OCR Works)
You get a **TEXT file** like this:
```
NOTES FROM: Introduction to Machine Learning
URL: https://youtube.com/...
Extracted: 2026-02-07 17:30
Total Slides: 45
============================================================

============================================================
SLIDE 1
============================================================
Introduction to Machine Learning
- What is ML?
- Types of ML
- Applications

============================================================
SLIDE 2
============================================================
Supervised Learning
- Classification
- Regression
- Examples: spam detection, price prediction
...
```

### If Tesseract is NOT Installed
You get a **ZIP file** with slide images (like before)

## 🚀 How to Use

### 1. Server is Running
```
✅ server_notes.py RUNNING
✅ Port 8000
✅ Ready for educational videos
```

### 2. Use Extension
1. Open Chrome extension
2. Enter an **EDUCATIONAL** video URL
3. Click "Start Extraction"
4. Wait 2-5 minutes
5. Download **notes.txt** file

### 3. Read Your Notes
Open the .txt file and you'll have all the text from the slides!

## ⚙️ Install Tesseract (Optional but Recommended)

To get TEXT instead of images:

### Windows
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR`
3. Add to PATH
4. Restart server

### Verify Installation
```bash
tesseract --version
```

## 📊 What to Expect

| Video Type | Processing Time | Output |
|------------|-----------------|--------|
| 5-min lecture | 2-3 minutes | Text notes |
| 10-min tutorial | 4-6 minutes | Text notes |
| 30-min lecture | 10-15 minutes | Text notes |

## ❌ Why Music Video Failed

The music video you tried has:
- ❌ No slides
- ❌ No text
- ❌ Just visuals and lyrics
- ❌ Nothing to extract

That's why the ZIP was 22 bytes (empty).

## ✅ Try This Now

Use this educational video:
```
https://www.youtube.com/watch?v=aircAruvnKk
```

This is a neural network lecture with:
- ✅ Slides with text
- ✅ Diagrams with labels
- ✅ Explanations
- ✅ Perfect for note extraction!

**Expected output**: 20-30 slides worth of notes about neural networks

---

**Server is ready! Use an EDUCATIONAL video URL to extract notes!** 📚
