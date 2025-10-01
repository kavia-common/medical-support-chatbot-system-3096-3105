 /**
  * PUBLIC_INTERFACE
  * api.js
  * A simple wrapper to construct API URLs and expose environment-driven configuration.
  * Provides a sensible default in local/preview development if REACT_APP_API_BASE_URL is not set.
  *
  * Behavior:
  * - If REACT_APP_API_BASE_URL is set, it is used (trailing slashes removed).
  * - Otherwise, default to http://localhost:8000 to reach the FastAPI dev server.
  *   This helps in preview environments where hostname/port may not be localhost:3000.
  */

const RAW_ENV_BASE = (process.env.REACT_APP_API_BASE_URL || '').trim();
const STRIPPED_ENV_BASE = RAW_ENV_BASE.replace(/\/*$/, '');

// Default FastAPI dev server URL
const DEFAULT_DEV_API = 'http://localhost:8000';

function inferDefaultBase() {
  // Prefer explicit env value
  if (STRIPPED_ENV_BASE) return STRIPPED_ENV_BASE;

  // Otherwise default to localhost:8000 for dev/preview usage
  try {
    const loc = typeof window !== 'undefined' ? window.location : null;
    if (loc) {
      const isDevPort = loc.port === '3000';
      const isLocalhost = loc.hostname === 'localhost' || loc.hostname === '127.0.0.1';
      if (isDevPort || isLocalhost) {
        // eslint-disable-next-line no-console
        console.warn(
          '[api] REACT_APP_API_BASE_URL is not set. Defaulting to',
          DEFAULT_DEV_API,
          'Create medical_chatbot_frontend/.env and set REACT_APP_API_BASE_URL to your backend URL if different.'
        );
        return DEFAULT_DEV_API;
      }
      // Preview or other host: still default to localhost:8000 to avoid empty base
      // eslint-disable-next-line no-console
      console.warn(
        '[api] REACT_APP_API_BASE_URL is not set on host',
        loc.hostname,
        'Defaulting to',
        DEFAULT_DEV_API
      );
      return DEFAULT_DEV_API;
    }
  } catch {
    // ignore SSR or unavailable window
  }

  // Fallback default
  return DEFAULT_DEV_API;
}

// PUBLIC_INTERFACE
export const API_BASE_URL = inferDefaultBase();

// PUBLIC_INTERFACE
export function apiUrl(path) {
  const base = (API_BASE_URL || '').replace(/\/*$/, '');
  const full = `${base}${path.startsWith('/') ? path : `/${path}`}`;
  return full;
}

// PUBLIC_INTERFACE
export function isApiConfigured() {
  return Boolean(API_BASE_URL);
}

// Helpful diagnostic log once at module load (non-fatal)
try {
  // eslint-disable-next-line no-console
  console.info('[api] Using API base URL:', API_BASE_URL);
} catch {
  // ignore
}
