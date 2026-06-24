const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function apiUrl(path: string): string {
  const normalizedBase = API_URL.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}
