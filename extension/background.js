

console.log('CodeMentor: Service worker starting...');

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('CodeMentor: Extension installed/updated', details);
  
  // Set default settings
  chrome.storage.local.set({
    settings: {
      hintsEnabled: true,
      maxHintsPerDay: 10,
      difficultyCap: 'Hard'
    }
  }).then(() => {
    console.log('CodeMentor: Default settings saved');
  }).catch(error => {
    console.error('CodeMentor: Error saving settings:', error);
  });
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('CodeMentor: Message received:', request);

  // Handle async operations properly
  if (request.action === 'get_auth_status') {
    handleGetAuthStatus()
      .then(result => {
        sendResponse(result);
      })
      .catch(error => {
        console.error('CodeMentor: Error getting auth status:', error);
        sendResponse({
          isAuthenticated: false,
          user: null,
          error: error.message
        });
      });
    return true; // Keep message channel open for async response
  }
  
  if (request.action === 'login') {
    handleLogin(request.credentials)
      .then(result => {
        sendResponse(result);
      })
      .catch(error => {
        console.error('CodeMentor: Login error:', error);
        sendResponse({
          success: false,
          error: 'Login failed: ' + error.message
        });
      });
    return true; // Keep message channel open for async response
  }

  if (request.action === 'logout') {
    handleLogout()
      .then(result => {
        sendResponse(result);
      })
      .catch(error => {
        console.error('CodeMentor: Logout error:', error);
        sendResponse({
          success: false,
          error: error.message
        });
      });
    return true;
  }

  if (request.action === 'track_event') {
    handleTrackEvent(request.eventData)
      .then(result => {
        sendResponse(result);
      })
      .catch(error => {
        console.error('CodeMentor: Event tracking error:', error);
        sendResponse({
          success: false,
          error: error.message
        });
      });
    return true;
  }

  // Handle unknown actions
  console.warn('CodeMentor: Unknown action:', request.action);
  sendResponse({
    success: false,
    error: 'Unknown action: ' + request.action
  });
});

// Handle tab updates to detect LeetCode pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only act when page is completely loaded
  if (changeInfo.status === 'complete' && tab.url) {
    // Check if it's a LeetCode problem page
    if (tab.url.includes('leetcode.com/problems/')) {
      console.log('CodeMentor: LeetCode problem page detected:', tab.url);
      
      // Inject content script if needed (fallback)
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        function: injectDetector
      }).catch(error => {
        // Ignore injection errors (script might already be injected via manifest)
        console.log('CodeMentor: Script injection skipped (likely already injected)');
      });
    }
  }
});

// Function to inject into page context
function injectDetector() {
  if (!window.codeMentorInjected) {
    window.codeMentorInjected = true;
    console.log('CodeMentor: Detector injected via background script');
  }
}

// Get authentication status
async function handleGetAuthStatus() {
  try {
    const result = await chrome.storage.local.get(['auth_token', 'user_data']);
    
    return {
      isAuthenticated: !!result.auth_token,
      user: result.user_data || null
    };
  } catch (error) {
    console.error('CodeMentor: Error getting auth status:', error);
    throw new Error('Failed to get authentication status');
  }
}

// Handle user login
async function handleLogin(credentials) {
  try {
    console.log('CodeMentor: Attempting login for:', credentials.email);
    
    // Validate input
    if (!credentials.email || !credentials.password) {
      throw new Error('Email and password are required');
    }

    const response = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password
      })
    });

    if (!response.ok) {
      // Try to get error details from response
      let errorMessage = 'Login failed';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch (e) {
        // If we can't parse the error response, use status text
        errorMessage = response.statusText || errorMessage;
      }
      
      throw new Error(errorMessage);
    }

    const data = await response.json();
    
    // Validate response data
    if (!data.access_token || !data.user) {
      throw new Error('Invalid response from server');
    }

    // Store authentication data
    await chrome.storage.local.set({
      auth_token: data.access_token,
      user_data: data.user,
      login_timestamp: Date.now()
    });
    
    console.log('CodeMentor: Login successful for user:', data.user.email);
    
    return {
      success: true,
      user: data.user,
      message: 'Login successful'
    };

  } catch (error) {
    console.error('CodeMentor: Login error:', error);
    
    // Return user-friendly error messages
    let userMessage = error.message;
    if (error.message.includes('fetch')) {
      userMessage = 'Unable to connect to server. Please check if the backend is running.';
    } else if (error.message.includes('NetworkError')) {
      userMessage = 'Network error. Please check your internet connection.';
    }
    
    return {
      success: false,
      error: userMessage
    };
  }
}

// Handle user logout
async function handleLogout() {
  try {
    // Clear all stored authentication data
    await chrome.storage.local.remove(['auth_token', 'user_data', 'login_timestamp']);
    
    console.log('CodeMentor: User logged out successfully');
    
    return {
      success: true,
      message: 'Logged out successfully'
    };
  } catch (error) {
    console.error('CodeMentor: Logout error:', error);
    throw new Error('Failed to logout');
  }
}

// Handle event tracking
async function handleTrackEvent(eventData) {
  try {
    // Get auth token
    const authStatus = await handleGetAuthStatus();
    
    if (!authStatus.isAuthenticated) {
      console.log('CodeMentor: Skipping event tracking - user not authenticated');
      return { success: true, message: 'Event tracking skipped - not authenticated' };
    }

    const response = await fetch('http://localhost:8000/api/analytics/track', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStatus.auth_token}`
      },
      body: JSON.stringify({
        ...eventData,
        timestamp: Date.now(),
        extension_version: chrome.runtime.getManifest().version
      })
    });

    if (response.ok) {
      console.log('CodeMentor: Event tracked successfully');
      return { success: true };
    } else {
      console.warn('CodeMentor: Event tracking failed:', response.status);
      return { success: false, error: 'Server error' };
    }

  } catch (error) {
    console.error('CodeMentor: Event tracking error:', error);
    // Don't throw error for analytics - just log it
    return { success: false, error: error.message };
  }
}

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
  console.log('CodeMentor: Extension startup');
});

// Handle service worker suspension
self.addEventListener('beforeunload', () => {
  console.log('CodeMentor: Service worker suspending');
});

// Keep service worker alive with periodic heartbeat
const keepAlive = () => {
  setInterval(() => {
    chrome.runtime.getPlatformInfo(() => {
      // This API call keeps the service worker alive
    });
  }, 20000); // Every 20 seconds
};

// Start keepalive
keepAlive();

console.log('CodeMentor: Service worker setup complete');