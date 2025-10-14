/**
 * Authentication Service
 * Handles Microsoft 365 authentication, token management, and user session
 */

import { PublicClientApplication } from '@azure/msal-browser';

class AuthService {
  constructor() {
    this.storageKeys = {
      TOKEN: 'sgd_access_token',
      REFRESH_TOKEN: 'sgd_refresh_token',
      USER: 'sgd_user',
      PREFERENCES: 'sgd_user_preferences',
      SESSION: 'sgd_session',
    };

    // Microsoft Graph scopes
    this.scopes = [
      'User.Read',
      'User.ReadBasic.All',
      'Files.ReadWrite',
      'Sites.ReadWrite.All',
    ];

    // MSAL configuration
    this.msalConfig = {
      auth: {
        clientId: process.env.REACT_APP_MICROSOFT_CLIENT_ID,
        authority: `https://login.microsoftonline.com/${process.env.REACT_APP_MICROSOFT_TENANT_ID}`,
        redirectUri: process.env.REACT_APP_MICROSOFT_REDIRECT_URI || window.location.origin,
        postLogoutRedirectUri: window.location.origin,
        navigateToLoginRequestUrl: false,
      },
      cache: {
        cacheLocation: 'localStorage',
        storeAuthStateInCookie: false,
      },
      system: {
        loggerOptions: {
          loggerCallback: (level, message, containsPii) => {
            if (process.env.NODE_ENV === 'development' && !containsPii) {
              console.log(`[MSAL] ${level}: ${message}`);
            }
          },
          piiLoggingEnabled: false,
          logLevel: process.env.NODE_ENV === 'development' ? 'Info' : 'Error',
        },
      },
    };

    // Initialize MSAL instance
    this.msalInstance = new PublicClientApplication(this.msalConfig);
    
    // Initialize
    this.initialize();
  }

  /**
   * Initialize authentication service
   */
  async initialize() {
    try {
      await this.msalInstance.initialize();
      
      // Handle redirect response
      const response = await this.msalInstance.handleRedirectPromise();
      if (response) {
        await this.handleAuthResponse(response);
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    const token = this.getToken();
    if (!token) return false;

    try {
      const payload = this.parseJwtPayload(token);
      const now = Date.now() / 1000;
      return payload.exp > now;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get current user
   */
  getCurrentUser() {
    const userStr = localStorage.getItem(this.storageKeys.USER);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch (error) {
      return null;
    }
  }

  /**
   * Get access token
   */
  getToken() {
    return localStorage.getItem(this.storageKeys.TOKEN);
  }

  /**
   * Get refresh token
   */
  getRefreshToken() {
    return localStorage.getItem(this.storageKeys.REFRESH_TOKEN);
  }

  /**
   * Login with Microsoft 365
   */
  async loginWithMicrosoft() {
    try {
      const loginRequest = {
        scopes: this.scopes,
        prompt: 'select_account',
      };

      // Try silent login first
      const accounts = this.msalInstance.getAllAccounts();
      if (accounts.length > 0) {
        const silentRequest = {
          ...loginRequest,
          account: accounts[0],
        };

        try {
          const response = await this.msalInstance.acquireTokenSilent(silentRequest);
          return await this.handleAuthResponse(response);
        } catch (silentError) {
          console.log('Silent login failed, falling back to interactive');
        }
      }

      // Interactive login
      const response = await this.msalInstance.acquireTokenPopup(loginRequest);
      return await this.handleAuthResponse(response);
    } catch (error) {
      console.error('Microsoft login error:', error);
      throw new Error('Microsoft authentication failed');
    }
  }

  /**
   * Login with local credentials (for demo/development mode)
   */
  async loginWithLocal(email, password) {
    try {
      const { apiService } = await import('./api');

      const response = await apiService.post('/auth/local/login', {
        email,
        password,
      });

      // Store authentication data
      this.storeAuthData(response);

      return response.user;
    } catch (error) {
      console.error('Local login error:', error);
      throw error;
    }
  }

  /**
   * Handle authentication response
   */
  async handleAuthResponse(response) {
    try {
      if (!response.accessToken) {
        throw new Error('No access token received');
      }

      // Exchange Microsoft token for backend token
      const backendResponse = await this.exchangeTokenWithBackend(response);
      
      // Store tokens and user data
      this.storeAuthData(backendResponse);
      
      return backendResponse.user;
    } catch (error) {
      console.error('Auth response handling error:', error);
      throw error;
    }
  }

  /**
   * Exchange Microsoft token with backend
   */
  async exchangeTokenWithBackend(msalResponse) {
    const { apiService } = await import('./api');
    
    try {
      const response = await apiService.post('/auth/microsoft', {
        access_token: msalResponse.accessToken,
        id_token: msalResponse.idToken,
        account: msalResponse.account,
      });

      return response.data;
    } catch (error) {
      throw new Error('Backend token exchange failed');
    }
  }

  /**
   * Store authentication data
   */
  storeAuthData(authData) {
    localStorage.setItem(this.storageKeys.TOKEN, authData.access_token);
    if (authData.refresh_token) {
      localStorage.setItem(this.storageKeys.REFRESH_TOKEN, authData.refresh_token);
    }
    localStorage.setItem(this.storageKeys.USER, JSON.stringify(authData.user));

    // Store session info
    const session = {
      loginTime: Date.now(),
      expiresAt: Date.now() + (authData.expires_in * 1000),
    };
    localStorage.setItem(this.storageKeys.SESSION, JSON.stringify(session));
  }

  /**
   * Refresh access token
   */
  async refreshToken() {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const { apiService } = await import('./api');
      const response = await apiService.post('/auth/refresh', {
        refresh_token: refreshToken,
      });

      const { access_token, expires_in } = response.data;
      
      // Update stored token
      localStorage.setItem(this.storageKeys.TOKEN, access_token);
      
      // Update session expiry
      const session = this.getSession();
      if (session) {
        session.expiresAt = Date.now() + (expires_in * 1000);
        localStorage.setItem(this.storageKeys.SESSION, JSON.stringify(session));
      }

      return access_token;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.logout();
      throw error;
    }
  }

  /**
   * Logout user
   */
  async logout() {
    try {
      // Call backend logout
      const token = this.getToken();
      if (token) {
        const { apiService } = await import('./api');
        try {
          await apiService.post('/auth/logout');
        } catch (error) {
          console.warn('Backend logout failed:', error);
        }
      }

      // Clear local storage
      this.clearAuthData();

      // Logout from Microsoft
      const accounts = this.msalInstance.getAllAccounts();
      if (accounts.length > 0) {
        await this.msalInstance.logoutPopup({
          account: accounts[0],
          postLogoutRedirectUri: window.location.origin,
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Force clear even if logout fails
      this.clearAuthData();
    }
  }

  /**
   * Clear authentication data
   */
  clearAuthData() {
    Object.values(this.storageKeys).forEach(key => {
      localStorage.removeItem(key);
    });
  }

  /**
   * Get session information
   */
  getSession() {
    const sessionStr = localStorage.getItem(this.storageKeys.SESSION);
    if (!sessionStr) return null;

    try {
      return JSON.parse(sessionStr);
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if session is expired
   */
  isSessionExpired() {
    const session = this.getSession();
    if (!session) return true;

    return Date.now() >= session.expiresAt;
  }

  /**
   * Get user preferences
   */
  getUserPreferences() {
    const prefsStr = localStorage.getItem(this.storageKeys.PREFERENCES);
    if (!prefsStr) return null;

    try {
      return JSON.parse(prefsStr);
    } catch (error) {
      return null;
    }
  }

  /**
   * Update user preferences
   */
  async updateUserPreferences(preferences) {
    try {
      const { apiService } = await import('./api');
      const response = await apiService.put('/users/preferences', preferences);
      
      // Update local storage
      localStorage.setItem(this.storageKeys.PREFERENCES, JSON.stringify(response.data));
      
      return response.data;
    } catch (error) {
      console.error('Preferences update error:', error);
      throw error;
    }
  }

  /**
   * Parse JWT payload
   */
  parseJwtPayload(token) {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      throw new Error('Invalid token format');
    }
  }

  /**
   * Get Microsoft Graph token
   */
  async getMicrosoftGraphToken() {
    try {
      const accounts = this.msalInstance.getAllAccounts();
      if (accounts.length === 0) {
        throw new Error('No Microsoft account found');
      }

      const silentRequest = {
        scopes: this.scopes,
        account: accounts[0],
      };

      const response = await this.msalInstance.acquireTokenSilent(silentRequest);
      return response.accessToken;
    } catch (error) {
      console.error('Microsoft Graph token error:', error);
      throw error;
    }
  }

  /**
   * Get user's Microsoft profile
   */
  async getMicrosoftProfile() {
    try {
      const token = await this.getMicrosoftGraphToken();
      
      const response = await fetch('https://graph.microsoft.com/v1.0/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch Microsoft profile');
      }

      return await response.json();
    } catch (error) {
      console.error('Microsoft profile error:', error);
      throw error;
    }
  }

  /**
   * Setup automatic token refresh
   */
  setupTokenRefresh() {
    const checkInterval = 5 * 60 * 1000; // 5 minutes
    
    setInterval(async () => {
      if (this.isAuthenticated()) {
        const token = this.getToken();
        const payload = this.parseJwtPayload(token);
        const now = Date.now() / 1000;
        const timeUntilExpiry = payload.exp - now;
        
        // Refresh if token expires in less than 10 minutes
        if (timeUntilExpiry < 600) {
          try {
            await this.refreshToken();
          } catch (error) {
            console.error('Automatic token refresh failed:', error);
          }
        }
      }
    }, checkInterval);
  }

  /**
   * Add authentication event listeners
   */
  addEventListeners() {
    // Handle storage changes (for multi-tab support)
    window.addEventListener('storage', (event) => {
      if (Object.values(this.storageKeys).includes(event.key)) {
        // Trigger auth state change event
        window.dispatchEvent(new CustomEvent('authStateChange', {
          detail: { 
            isAuthenticated: this.isAuthenticated(),
            user: this.getCurrentUser(),
          }
        }));
      }
    });

    // Handle page visibility change
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.isAuthenticated()) {
        // Check token validity when page becomes visible
        if (this.isSessionExpired()) {
          this.logout();
        }
      }
    });
  }
}

// Create singleton instance
const authServiceInstance = new AuthService();

// Export singleton instance
export { authServiceInstance as AuthService };
export default authServiceInstance;