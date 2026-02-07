// Configuration
const API_BASE_URL = 'http://localhost:8000';
const POLL_INTERVAL = 2000; // Poll every 2 seconds

// State
let currentJobId = null;
let pollInterval = null;
let currentMode = 'currentTab'; // 'currentTab' or 'manualUrl'

// DOM Elements
const startBtn = document.getElementById('startBtn');
const downloadBtn = document.getElementById('downloadBtn');
const videoInfo = document.getElementById('videoInfo');
const videoTitle = document.getElementById('videoTitle');
const statusContainer = document.getElementById('statusContainer');
const statusText = document.getElementById('statusText');
const progressPercent = document.getElementById('progressPercent');
const progressFill = document.getElementById('progressFill');
const statusMessage = document.getElementById('statusMessage');
const errorContainer = document.getElementById('errorContainer');
const errorMessage = document.getElementById('errorMessage');
const qualitySelect = document.getElementById('quality');

// Tab switching elements
const currentTabModeBtn = document.getElementById('currentTabMode');
const manualUrlModeBtn = document.getElementById('manualUrlMode');
const currentTabSection = document.getElementById('currentTabSection');
const manualUrlSection = document.getElementById('manualUrlSection');
const urlInput = document.getElementById('urlInput');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Get current tab info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (tab.url && tab.url.includes('youtube.com/watch')) {
        videoTitle.textContent = tab.title.replace(' - YouTube', '');
        startBtn.disabled = false;
    } else {
        videoTitle.textContent = 'Not on YouTube';
        startBtn.disabled = false; // Enable button for manual URL mode
    }

    // Load saved settings
    const settings = await chrome.storage.local.get(['quality']);
    if (settings.quality) {
        qualitySelect.value = settings.quality;
    }

    // Check for ongoing job
    const { jobId } = await chrome.storage.local.get(['jobId']);
    if (jobId) {
        currentJobId = jobId;
        statusContainer.classList.remove('hidden');
        startBtn.disabled = true;
        updateStatus('processing', 0, 'Resuming extraction...');
        startPolling();
    }
});

// Event Listeners
startBtn.addEventListener('click', handleStartExtraction);
downloadBtn.addEventListener('click', handleDownload);
qualitySelect.addEventListener('change', async (e) => {
    await chrome.storage.local.set({ quality: e.target.value });
});

// Tab switching
currentTabModeBtn.addEventListener('click', () => {
    currentMode = 'currentTab';
    currentTabModeBtn.classList.add('active');
    manualUrlModeBtn.classList.remove('active');
    currentTabSection.classList.remove('hidden');
    manualUrlSection.classList.add('hidden');
    hideError();
});

manualUrlModeBtn.addEventListener('click', () => {
    currentMode = 'manualUrl';
    manualUrlModeBtn.classList.add('active');
    currentTabModeBtn.classList.remove('active');
    manualUrlSection.classList.remove('hidden');
    currentTabSection.classList.add('hidden');
    hideError();
});

// URL input validation
urlInput.addEventListener('input', (e) => {
    const url = e.target.value.trim();
    if (url && isValidYouTubeUrl(url)) {
        urlInput.style.borderColor = '#4CAF50';
    } else if (url) {
        urlInput.style.borderColor = '#ff6b6b';
    } else {
        urlInput.style.borderColor = '#e9ecef';
    }
});

function isValidYouTubeUrl(url) {
    try {
        const urlObj = new URL(url);
        return (urlObj.hostname === 'www.youtube.com' || urlObj.hostname === 'youtube.com' || urlObj.hostname === 'youtu.be') &&
            (urlObj.pathname.includes('/watch') || urlObj.hostname === 'youtu.be');
    } catch {
        return false;
    }
}

// Main Functions
async function handleStartExtraction() {
    try {
        let videoUrl;

        // Get URL based on current mode
        if (currentMode === 'manualUrl') {
            videoUrl = urlInput.value.trim();

            if (!videoUrl) {
                showError('Please enter a YouTube video URL');
                return;
            }

            if (!isValidYouTubeUrl(videoUrl)) {
                showError('Please enter a valid YouTube URL');
                return;
            }
        } else {
            // Get current tab
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

            if (!tab.url || !tab.url.includes('youtube.com/watch')) {
                showError('Please navigate to a YouTube video page or use Manual URL mode');
                return;
            }

            videoUrl = tab.url;
        }

        // Disable start button
        startBtn.disabled = true;
        hideError();

        // Show status
        statusContainer.classList.remove('hidden');
        updateStatus('queued', 0, 'Starting extraction...');

        // Send request to API
        const response = await fetch(`${API_BASE_URL}/api/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: videoUrl,
                quality: qualitySelect.value
            })
        });

        if (!response.ok) {
            throw new Error('Failed to start extraction');
        }

        const data = await response.json();
        currentJobId = data.job_id;

        // Save job ID
        await chrome.storage.local.set({ jobId: currentJobId });

        // Start polling for status
        startPolling();

    } catch (error) {
        console.error('Error starting extraction:', error);
        showError('Failed to start extraction. Make sure the backend server is running.');
        startBtn.disabled = false;
        statusContainer.classList.add('hidden');
    }
}

async function handleDownload() {
    if (!currentJobId) return;

    try {
        // Open download URL in new tab
        const downloadUrl = `${API_BASE_URL}/api/download/${currentJobId}`;
        chrome.tabs.create({ url: downloadUrl });

    } catch (error) {
        console.error('Error downloading PDF:', error);
        showError('Failed to download PDF');
    }
}

function startPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    pollInterval = setInterval(checkJobStatus, POLL_INTERVAL);
    checkJobStatus(); // Check immediately
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

async function checkJobStatus() {
    if (!currentJobId) {
        stopPolling();
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/status/${currentJobId}`);

        if (!response.ok) {
            throw new Error('Failed to get job status');
        }

        const data = await response.json();

        updateStatus(data.status, data.progress, data.message);

        // Handle completion
        if (data.status === 'completed') {
            stopPolling();
            startBtn.disabled = false;
            downloadBtn.classList.remove('hidden');
            await chrome.storage.local.remove(['jobId']);
        }

        // Handle failure
        if (data.status === 'failed') {
            stopPolling();
            showError(data.error || 'Extraction failed');
            startBtn.disabled = false;
            statusContainer.classList.add('hidden');
            await chrome.storage.local.remove(['jobId']);
        }

    } catch (error) {
        console.error('Error checking job status:', error);
        // Don't show error immediately, might be temporary network issue
    }
}

function updateStatus(status, progress, message) {
    // Update status text
    const statusLabels = {
        'queued': 'Queued',
        'downloading': 'Downloading Video',
        'extracting': 'Extracting Frames',
        'detecting': 'Detecting Pages',
        'cleaning': 'Cleaning Frames',
        'ocr': 'Extracting Text',
        'generating': 'Generating PDF',
        'completed': 'Completed'
    };

    statusText.textContent = statusLabels[status] || status;

    // Update progress
    progressPercent.textContent = `${progress}%`;
    progressFill.style.width = `${progress}%`;

    // Update message
    statusMessage.textContent = message;

    // Add pulse animation during processing
    if (status !== 'completed' && status !== 'failed') {
        progressFill.classList.add('pulse');
    } else {
        progressFill.classList.remove('pulse');
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorContainer.classList.remove('hidden');
}

function hideError() {
    errorContainer.classList.add('hidden');
}

// Cleanup on popup close
window.addEventListener('unload', () => {
    stopPolling();
});
