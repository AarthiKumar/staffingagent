export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
export const DEFAULT_AGENT_ID = 'staffing';

// Auth0 Configuration
export const AUTH0_DOMAIN = import.meta.env.VITE_AUTH0_DOMAIN || '';
export const AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID || '';
export const AUTH0_AUDIENCE = import.meta.env.VITE_AUTH0_AUDIENCE || 'https://api.staffingagent.com';
export const AUTH0_REDIRECT_URI = import.meta.env.VITE_AUTH0_REDIRECT_URI || `${window.location.origin}/callback`;
export const AUTH0_ENABLED = import.meta.env.VITE_AUTH0_ENABLED === 'true';
