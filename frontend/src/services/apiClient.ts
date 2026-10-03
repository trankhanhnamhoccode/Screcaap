import { apiConfig } from '../api/config';

export type ApiFailureKind = 'network' | 'timeout' | 'backend' | 'invalid-response';

export class ApiError extends Error {
  constructor(readonly kind: ApiFailureKind, message: string, readonly status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

// Services must supply a decoder based on a finalized contract, rather than
// casting arbitrary response JSON to an invented DTO. No automatic retries.
export async function requestJson<T>(
  path: string,
  decode: (value: unknown) => T,
  signal?: AbortSignal,
): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const cancel = () => controller.abort();
  signal?.addEventListener('abort', cancel, { once: true });
  if (signal?.aborted) cancel();
  const timer = window.setTimeout(() => { timedOut = true; controller.abort(); }, apiConfig.timeoutMs);
  try {
    if (!apiConfig.baseUrl || !path.startsWith('/') || path.startsWith('//') || /[?#]/.test(apiConfig.baseUrl)) {
      throw new ApiError('invalid-response', 'Check the API base URL and request path.');
    }
    const response = await fetch(`${apiConfig.baseUrl}${path}`, {
      method: 'GET',
      signal: controller.signal,
      headers: { Accept: 'application/json' },
      credentials: 'omit', // Authentication is Needs confirmation.
    });
    if (!response.ok) throw new ApiError('backend', `API request failed (${response.status}).`, response.status);
    try {
      return decode(await response.json());
    } catch (error) {
      if (controller.signal.aborted) throw error;
      throw new ApiError('invalid-response', 'The API returned an invalid or unexpected response.');
    }
  } catch (error) {
    if (signal?.aborted) throw error;
    if (error instanceof ApiError) throw error;
    if (timedOut) throw new ApiError('timeout', 'The API request timed out.');
    throw new ApiError('network', 'Cannot reach the backend. Check that the API is running.');
  } finally {
    window.clearTimeout(timer);
    signal?.removeEventListener('abort', cancel);
  }
}
