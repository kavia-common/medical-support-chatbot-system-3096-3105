 /**
  * PUBLIC_INTERFACE
  * api.js
  * A simple wrapper to construct API URLs and expose environment-driven configuration.
  * Provides a sensible default in local/preview development if REACT_APP_API_BASE_URL is not set.
  *
  * Behavior:
  * - If REACT_APP_API_BASE_URL is set, it is used (trailing slashes removed).
  * - Otherwise, try to infer the proxy base in this environment or default to http://localhost:8000.
  */

const RAW_ENV_BASE = (process.env.REACT_APP_API_BASE_URL || '').trim();
const STRIPPED_ENV_BASE = RAW_ENV_BASE.replace(/\/*$/, '');

// Default FastAPI dev server URL
const DEFAULT_DEV_API = 'http://localhost:8000';

function inferDefaultBase() {
  // Prefer explicit env value
  if (STRIPPED_ENV_BASE) return STRIPPED_ENV_BASE;

  // Attempt to infer proxy base URL in VSCode-internal environment
  try {
    const loc = typeof window !== 'undefined' ? window.location : null;
    if (loc) {
      const host = loc.hostname || '';
      // If hosted on vscode-internal/cloud.kavia.ai, infer the known proxy path if no env provided
      if (host.includes('vscode-internal') || host.includes('beta01.cloud.kavia.ai')) {
        const inferred = 'https://vscode-internal-30348-beta.beta01.cloud.kavia.ai/proxy/8001';
        // eslint-disable-next-line no-console
        console.warn('[api] REACT_APP_API_BASE_URL not set. Inferring proxy base URL:', inferred);
        return inferred.replace(/\/*$/, '');
      }

      const isDevPort = loc.port === '3000';
      const isLocalhost = host === 'localhost' || host === '127.0.0.1';
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
        host,
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

// PUBLIC_INTERFACE
export async function apiHealthCheck() {
  const url = apiUrl('/');
  try {
    const res = await fetch(url, { method: 'GET' });
    if (!res.ok) {
      return { ok: false, status: res.status, url, message: `Health check failed (${res.status})` };
    }
    return { ok: true, status: res.status, url };
  } catch (e) {
    return { ok: false, status: 0, url, message: e?.message || 'Network error during health check' };
  }
}

// Helpful diagnostic log once at module load (non-fatal)
try {
  // eslint-disable-next-line no-console
  console.info('[api] Using API base URL:', API_BASE_URL);
} catch {
  // ignore
}
