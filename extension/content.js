// Content script that runs on YouTube pages
// Can interact with the YouTube page DOM if needed

console.log('YouTube Notes Extractor content script loaded');

// Listen for messages from popup or background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getVideoInfo') {
        // Extract video information from the page
        const videoInfo = {
            title: document.title.replace(' - YouTube', ''),
            url: window.location.href,
            videoId: new URLSearchParams(window.location.search).get('v')
        };

        sendResponse(videoInfo);
    }
});

// Optional: Add visual indicator when extraction is in progress
function showExtractionIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'notes-extractor-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
    `;

    indicator.innerHTML = `
        <div style="width: 16px; height: 16px; border: 2px solid white; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        Extracting notes...
    `;

    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(indicator);
}

function hideExtractionIndicator() {
    const indicator = document.getElementById('notes-extractor-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// Export functions for use by other scripts
window.notesExtractor = {
    showIndicator: showExtractionIndicator,
    hideIndicator: hideExtractionIndicator
};
