// Background service worker for Chrome Extension
// Handles background tasks and message passing

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
    console.log('YouTube Notes Extractor installed');

    // Set default settings
    chrome.storage.local.set({
        quality: '720p',
        apiUrl: 'http://localhost:8000'
    });
});

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getVideoUrl') {
        // Get current tab URL
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                sendResponse({ url: tabs[0].url });
            }
        });
        return true; // Keep channel open for async response
    }

    if (request.action === 'notify') {
        // Show notification
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon128.png',
            title: request.title || 'YouTube Notes Extractor',
            message: request.message
        });
    }
});

// Handle notification clicks
chrome.notifications.onClicked.addListener((notificationId) => {
    // Open extension popup or relevant page
    chrome.action.openPopup();
});
