# Extension Icons

The extension requires three icon sizes:
- 16x16 pixels (toolbar)
- 48x48 pixels (extension management)
- 128x128 pixels (Chrome Web Store)

## Creating Icons

### Option 1: Use an Online Icon Generator
1. Visit [favicon.io](https://favicon.io/favicon-generator/)
2. Use these settings:
   - Text: "YN" (YouTube Notes)
   - Background: Gradient from #667eea to #764ba2
   - Font: Bold, modern sans-serif
   - Shape: Rounded square

### Option 2: Use Design Software
Create icons with these specifications:
- **Design**: Play button + document/notepad
- **Colors**: Purple gradient (#667eea to #764ba2)
- **Style**: Modern, flat, minimalist
- **Format**: PNG with transparency

### Option 3: Use Placeholder Icons
For testing, you can use simple colored squares:

1. Create a 128x128 purple square
2. Resize to 48x48 and 16x16
3. Save as PNG files

## File Locations
Place the icons in the `extension/icons/` directory:
```
extension/icons/
├── icon16.png
├── icon48.png
└── icon128.png
```

## Temporary Workaround
Until you create proper icons, the extension will work without them (Chrome will show a default icon).

## Design Guidelines
- Keep it simple and recognizable
- Ensure good contrast for visibility
- Test at all sizes (16px should still be clear)
- Use consistent branding colors
- Avoid text at small sizes (16px, 48px)
