# FFmpeg Installation Guide for Windows

## Quick Installation Steps

### Method 1: Download Pre-built Binary (Recommended)

1. **Download FFmpeg**:
   - Visit: https://www.gyan.dev/ffmpeg/builds/
   - Download: `ffmpeg-release-essentials.zip` (smaller, recommended)
   - OR download: `ffmpeg-release-full.zip` (complete version)

2. **Extract the Archive**:
   - Extract the downloaded ZIP file
   - You'll get a folder like `ffmpeg-6.1-essentials_build`

3. **Move to Program Files**:
   - Move the extracted folder to: `C:\Program Files\`
   - Rename it to just `ffmpeg` for simplicity
   - Final path should be: `C:\Program Files\ffmpeg\`

4. **Add to System PATH**:
   
   **Option A: Using GUI**
   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click "Edit"
   - Click "New"
   - Add: `C:\Program Files\ffmpeg\bin`
   - Click "OK" on all dialogs
   
   **Option B: Using PowerShell (Admin)**
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\ffmpeg\bin", "Machine")
   ```

5. **Verify Installation**:
   - Open a NEW terminal window (important!)
   - Run: `ffmpeg -version`
   - You should see FFmpeg version information

### Method 2: Using Winget (Windows Package Manager)

If you have Windows 10/11 with winget:

```powershell
winget install ffmpeg
```

### Method 3: Using Scoop

If you have Scoop package manager:

```powershell
scoop install ffmpeg
```

## Quick Test

After installation, open a NEW terminal and run:

```bash
ffmpeg -version
```

You should see output like:
```
ffmpeg version 6.1-essentials_build
...
```

## Troubleshooting

### "ffmpeg is not recognized"
- Make sure you opened a NEW terminal after adding to PATH
- Verify the PATH was added correctly: `echo %PATH%` (should include ffmpeg\bin)
- Restart your computer if needed

### Still not working?
- Check that `ffmpeg.exe` exists in `C:\Program Files\ffmpeg\bin\`
- Try running the full path: `"C:\Program Files\ffmpeg\bin\ffmpeg.exe" -version`

## Alternative: Portable Installation

If you don't want to modify system PATH:

1. Download and extract FFmpeg
2. Place the `bin` folder contents in your project directory
3. Update `backend/.env`:
   ```
   FFMPEG_PATH=C:\path\to\ffmpeg\bin\ffmpeg.exe
   ```

## After Installation

Once FFmpeg is installed:

1. **Close and reopen your terminal**
2. **Restart the backend server**:
   ```bash
   cd backend
   python main.py
   ```
3. **Try the extraction again** in the Chrome extension

## Quick Download Links

- **Official Site**: https://ffmpeg.org/download.html
- **Windows Builds**: https://www.gyan.dev/ffmpeg/builds/
- **Direct Download**: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

---

**Note**: After installing FFmpeg, you MUST open a new terminal window for the PATH changes to take effect!
