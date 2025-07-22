document.addEventListener('DOMContentLoaded', async () => {
  const loginSection = document.getElementById('login-section');
  const dashboardSection = document.getElementById('dashboard-section');
  const loginBtn = document.getElementById('login-btn');
  const registerBtn = document.getElementById('register-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const errorDiv = document.getElementById('error-message');

  // Check auth status
  const authStatus = await chrome.runtime.sendMessage({ action: 'get_auth_status' });
  
  if (authStatus.isAuthenticated) {
    showDashboard();
  } else {
    showLogin();
  }

  function showLogin() {
    loginSection.style.display = 'block';
    dashboardSection.style.display = 'none';
  }

  function showDashboard() {
    loginSection.style.display = 'none';
    dashboardSection.style.display = 'block';
  }

  function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    setTimeout(() => {
      errorDiv.style.display = 'none';
    }, 5000);
  }

  loginBtn.addEventListener('click', async () => {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!email || !password) {
      showError('Please fill in all fields');
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = 'Signing in...';

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'login',
        credentials: { email, password }
      });

      if (response.success) {
        showDashboard();
      } else {
        showError(response.error || 'Login failed');
      }
    } catch (error) {
      showError('Network error. Please try again.');
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = 'Sign In';
    }
  });

  registerBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:8000/docs' });
  });

  logoutBtn.addEventListener('click', async () => {
    await chrome.storage.local.clear();
    showLogin();
  });
});