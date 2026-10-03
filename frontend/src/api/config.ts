// VITE_* values are public. Never put credentials in this configuration.
export const apiConfig = {
  baseUrl: (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').trim().replace(/\/+$/, ''),
  timeoutMs: 10_000,
  useMocks: import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_API === 'true',
};
