 /**
  * PUBLIC_INTERFACE
  * api.js
  * A simple wrapper to construct API URLs and expose environment-driven configuration.
  */

export const API_BASE_URL = (process.env.REACT_APP_API_BASE_URL || '').replace(/\/+$/, '');

// PUBLIC_INTERFACE
export function apiUrl(path) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}
