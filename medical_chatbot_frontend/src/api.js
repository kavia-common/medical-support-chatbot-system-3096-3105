 /**
  * PUBLIC_INTERFACE
  * api.js
  * A simple wrapper to construct API URLs and expose environment-driven configuration.
  * Provides a sensible default in local development if REACT_APP_API_BASE_URL is not set.
  */

const RAW_ENV_BASE = (process.env.REACT_APP_API_BASE_URL || '').trim();
const STRIPPED_ENV_BASE = RAW_ENV_BASE.replace(/\/+$/, '');

// Default FastAPI dev server URL
const DEFAULT_DEV_API = 'http://localhost:8000';

function inferDefaultBase() {
  try {
    const loc = typeof window !== 'undefined' ? window.location : null;
    // If running on CRA dev server and no env var set, default to FastAPI default port.
    if (!STRIPPED_ENV_BASE && loc && (loc.port === '3000' || loc.hostname === 'localhost')) {
      // eslint-disable-next-line no-console
      console.warn(
        '[api] REACT_APP_API_BASE_URL is not set. Defaulting to',
        DEFAULT_DEV_API,
        'Create medical_chatbot_frontend/.env and set REACT_APP_API_BASE_URL to your backend URL.'
      );
      return DEFAULT_DEV_API;
    }
  } catch {
    // ignore SSR or unavailable window
  }
  return STRIPPED_ENV_BASE;
}

// PUBLIC_INTERFACE
export const API_BASE_URL = inferDefaultBase();

// PUBLIC_INTERFACE
export function apiUrl(path) {
  const base = (API_BASE_URL || '').replace(/\/+$/, '');
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

// PUBLIC_INTERFACe
export function isApiConfigured() {
  return Boolean(API_BASE_URL);
}
