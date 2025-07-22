class LeetCodeDetector {
  constructor() {
    this.currentProblem = null;
    this.hintWidget = null;
    this.isInitialized = false;
    this.API_BASE = 'http://localhost:8000/api';
    this.startTime = Date.now();
  }

  async init() {
    if (this.isInitialized) return;
    
    console.log('CodeMentor: Initializing LeetCode detector...');
    console.log('CodeMentor: Current URL:', window.location.href);
    
    // Check if we're actually on a LeetCode problem page
    if (!this.isLeetCodeProblemPage()) {
      console.log('CodeMentor: Not a LeetCode problem page');
      return;
    }
    
    // Try multiple selectors for the problem title
    await this.waitForProblemElements();
    await this.detectProblem();
    
    if (this.currentProblem) {
      this.createHintWidget();
    }
    
    this.setupNavigationListener();
    this.isInitialized = true;
    console.log('CodeMentor: Initialization complete');
  }

  isLeetCodeProblemPage() {
    const url = window.location.href;
    return url.includes('leetcode.com/problems/') && !url.includes('/submissions/');
  }

  async waitForProblemElements() {
    console.log('CodeMentor: Waiting for problem elements...');
    
    // Try multiple selectors that LeetCode might use
    const possibleSelectors = [
      '[data-cy="question-title"]',
      'h1[data-cy="question-title"]',
      '.css-v3d350',  // Common LeetCode title class
      'h1',           // Fallback to any h1
      '[class*="title"]',
      '.question-title',
      'div[data-track-load="question_title"]'
    ];

    for (const selector of possibleSelectors) {
      try {
        console.log(`CodeMentor: Trying selector: ${selector}`);
        const element = await this.waitForElement(selector, 2000);
        if (element && element.textContent.trim()) {
          console.log(`CodeMentor: Found title element with selector: ${selector}`);
          console.log(`CodeMentor: Title text: "${element.textContent.trim()}"`);
          return element;
        }
      } catch (error) {
        console.log(`CodeMentor: Selector ${selector} not found`);
      }
    }
    
    throw new Error('Could not find problem title with any selector');
  }

  parseProblemFromDOM() {
    console.log('CodeMentor: Parsing problem from DOM...');
    
    // Try multiple ways to get the title
    let title = null;
    const titleSelectors = [
      '[data-cy="question-title"]',
      'h1[data-cy="question-title"]', 
      '.css-v3d350',
      'h1',
      '[class*="title"]'
    ];

    for (const selector of titleSelectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        title = element.textContent.trim();
        console.log(`CodeMentor: Found title "${title}" with selector: ${selector}`);
        break;
      }
    }

    if (!title) {
      console.error('CodeMentor: Could not find problem title');
      return null;
    }

    // Try to get difficulty
    let difficulty = 'Unknown';
    const difficultySelectors = [
      '[diff]',
      '[class*="difficulty"]',
      '.text-difficulty-easy',
      '.text-difficulty-medium', 
      '.text-difficulty-hard',
      '[data-degree]'
    ];

    for (const selector of difficultySelectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        difficulty = element.textContent.trim();
        console.log(`CodeMentor: Found difficulty "${difficulty}" with selector: ${selector}`);
        break;
      }
    }

    // Try to get description
    let description = '';
    const descriptionSelectors = [
      '[data-track-load="description_content"]',
      '.question-content',
      '[class*="content"]',
      '.elfjS'  // Another common LeetCode class
    ];

    for (const selector of descriptionSelectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent.trim()) {
        description = element.textContent.trim();
        console.log(`CodeMentor: Found description with selector: ${selector}`);
        break;
      }
    }

    // Extract problem ID from URL
    const url = window.location.href;
    const problemId = this.extractProblemId(url);

    const problemData = {
      id: problemId,
      title: title,
      difficulty: difficulty,
      description: description.substring(0, 1000), // Limit description length
      examples: [],
      constraints: [],
      url: url,
      platform: 'leetcode'
    };

    console.log('CodeMentor: Parsed problem data:', problemData);
    return problemData;
  }

  extractProblemId(url) {
    const match = url.match(/\/problems\/([^\/\?]+)/);
    return match ? match[1] : null;
  }

  async detectProblem() {
    try {
      const problemData = this.parseProblemFromDOM();
      
      if (!problemData) {
        console.log('CodeMentor: No problem data could be parsed');
        return;
      }

      console.log('CodeMentor: Problem detected:', problemData.title);
      
      // For now, let's store the problem locally and skip the API call
      // This will help us test if the detection is working
      this.currentProblem = {
        ...problemData,
        id: Date.now() // temporary ID
      };
      
      console.log('CodeMentor: Problem stored locally (skipping API for now)');
      
      // Uncomment this when you want to test API calls:
      /*
      const response = await this.sendToBackend('/problems/detect', {
        method: 'POST',
        body: JSON.stringify(problemData)
      });

      if (response.ok) {
        this.currentProblem = await response.json();
        console.log('CodeMentor: Problem registered with backend');
      } else {
        console.error('CodeMentor: API error:', response.status);
      }
      */
      
    } catch (error) {
      console.error('CodeMentor: Error detecting problem:', error);
    }
  }

  createHintWidget() {
    if (this.hintWidget) {
      this.hintWidget.remove();
    }

    this.hintWidget = document.createElement('div');
    this.hintWidget.id = 'codementor-widget';
    this.hintWidget.innerHTML = this.getWidgetHTML();

    this.hintWidget.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      width: 350px;
      max-height: 500px;
      background: #ffffff;
      border: 2px solid #ff6b6b;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      z-index: 10000;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      overflow: hidden;
    `;

    document.body.appendChild(this.hintWidget);
    this.setupWidgetEvents();
    console.log('CodeMentor: Widget created and displayed');
  }

  getWidgetHTML() {
    return `
      <div style="padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-weight: bold;">🎯 CodeMentor Assistant</div>
          <button id="cm-minimize" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">−</button>
        </div>
      </div>
      
      <div id="cm-content" style="padding: 15px;">
        <div style="margin-bottom: 15px;">
          <h3 style="margin: 0; font-size: 16px; color: #333;">${this.currentProblem?.title || 'Problem Detected!'}</h3>
          <span style="background: #f0f0f0; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-top: 5px; display: inline-block; color: #666;">
            ${this.currentProblem?.difficulty || 'Unknown'}
          </span>
        </div>

        <div style="margin-bottom: 15px;">
          <div style="margin-bottom: 10px;">
            <button id="cm-hint-1" data-level="1" style="width: 100%; padding: 10px; background: #ff6b6b; color: white; border: none; border-radius: 6px; cursor: pointer; margin-bottom: 5px;">
              Get Hint Level 1 (Problem Type)
            </button>
          </div>

          <div style="margin-bottom: 10px;">
            <button id="cm-hint-2" data-level="2" disabled style="width: 100%; padding: 10px; background: #ccc; color: white; border: none; border-radius: 6px; cursor: not-allowed; margin-bottom: 5px;">
              Get Hint Level 2 (Approach)
            </button>
          </div>

          <div style="margin-bottom: 10px;">
            <button id="cm-hint-3" data-level="3" disabled style="width: 100%; padding: 10px; background: #ccc; color: white; border: none; border-radius: 6px; cursor: not-allowed;">
              Get Hint Level 3 (Implementation)
            </button>
          </div>
        </div>

        <div id="cm-hints-display" style="max-height: 200px; overflow-y: auto;">
          <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 14px; color: #666;">
            Widget loaded successfully! Click buttons above to get hints.
          </div>
        </div>
      </div>
    `;
  }

  setupWidgetEvents() {
    const minimizeBtn = this.hintWidget.querySelector('#cm-minimize');
    const content = this.hintWidget.querySelector('#cm-content');
    
    minimizeBtn.addEventListener('click', () => {
      const isMinimized = content.style.display === 'none';
      content.style.display = isMinimized ? 'block' : 'none';
      minimizeBtn.textContent = isMinimized ? '−' : '+';
    });

    const hintButtons = this.hintWidget.querySelectorAll('[data-level]');
    hintButtons.forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const level = parseInt(e.target.dataset.level);
        await this.requestHint(level);
      });
    });
  }

  async requestHint(level) {
    console.log(`CodeMentor: Requesting hint level ${level}`);
    
    const button = this.hintWidget.querySelector(`#cm-hint-${level}`);
    const originalText = button.textContent;
    button.textContent = 'Loading...';
    button.disabled = true;

    try {
      // For now, provide static hints to test the UI
      const staticHints = {
        1: "This appears to be an algorithm problem. Look at the input/output pattern to identify the problem type (array, string, tree, graph, etc.)",
        2: "Consider the time complexity requirements. Can you solve this with a brute force approach first, then optimize?",
        3: "Think about the data structures you need. Often problems require HashMaps, Arrays, or Two Pointers technique."
      };

      const hint = staticHints[level] || "Keep working on it! You're making progress.";
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      this.displayHint(level, hint);
      this.enableNextLevel(level + 1);
      
    } catch (error) {
      console.error('CodeMentor: Error requesting hint:', error);
      this.showError('Failed to get hint. Please try again.');
      
      button.textContent = originalText;
      button.disabled = false;
    }
  }

  displayHint(level, hintText) {
    const hintsDisplay = this.hintWidget.querySelector('#cm-hints-display');
    
    // Clear the initial message if it's the first hint
    if (level === 1) {
      hintsDisplay.innerHTML = '';
    }
    
    const hintElement = document.createElement('div');
    hintElement.style.cssText = `
      background: #f8f9fa;
      padding: 10px;
      border-radius: 6px;
      margin-bottom: 10px;
      border-left: 4px solid #ff6b6b;
    `;
    hintElement.innerHTML = `
      <div style="font-weight: bold; color: #ff6b6b; font-size: 12px; margin-bottom: 5px;">
        HINT LEVEL ${level}
      </div>
      <div style="font-size: 14px; line-height: 1.4; color: #333;">${hintText}</div>
    `;

    hintsDisplay.appendChild(hintElement);
    hintElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    const button = this.hintWidget.querySelector(`#cm-hint-${level}`);
    button.textContent = `Hint ${level} Received ✓`;
    button.style.background = '#28a745';
  }

  enableNextLevel(level) {
    if (level <= 3) {
      const nextButton = this.hintWidget.querySelector(`#cm-hint-${level}`);
      if (nextButton) {
        nextButton.disabled = false;
        nextButton.style.background = '#ff6b6b';
        nextButton.style.cursor = 'pointer';
      }
    }
  }

  showError(message) {
    const hintsDisplay = this.hintWidget.querySelector('#cm-hints-display');
    const errorElement = document.createElement('div');
    errorElement.style.cssText = `
      background: #f8d7da;
      color: #721c24;
      padding: 10px;
      border-radius: 6px;
      margin-bottom: 10px;
    `;
    errorElement.textContent = message;
    hintsDisplay.appendChild(errorElement);
  }

  setupNavigationListener() {
    let currentUrl = location.href;
    const observer = new MutationObserver(() => {
      if (location.href !== currentUrl) {
        currentUrl = location.href;
        console.log('CodeMentor: URL changed to:', currentUrl);
        setTimeout(() => {
          this.isInitialized = false;
          this.init();
        }, 1000);
      }
    });

    observer.observe(document, { subtree: true, childList: true });
  }

  waitForElement(selector, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);
      if (element) {
        resolve(element);
        return;
      }

      const observer = new MutationObserver((mutations, obs) => {
        const element = document.querySelector(selector);
        if (element) {
          obs.disconnect();
          resolve(element);
        }
      });

      observer.observe(document, {
        childList: true,
        subtree: true
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`Element ${selector} not found within ${timeout}ms`));
      }, timeout);
    });
  }
}

// Initialize when page loads
console.log('CodeMentor: Script loaded');

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new LeetCodeDetector().init();
  });
} else {
  new LeetCodeDetector().init();
}