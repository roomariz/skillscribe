export type ApiEnvelope<T> = {
  success: true;
  data: T;
  timestamp: string;
};

export type ApiErrorEnvelope = {
  success: false;
  error_code: string;
  message: string;
  timestamp: string;
  details?: Record<string, unknown>;
  recovery_hint?: string;
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function getStatus() {
  const response = await fetch(`${API_BASE_URL}/api/status`);
  if (!response.ok) {
    throw new Error('Unable to load API status');
  }
  return (await response.json()) as ApiEnvelope<{
    database_type: 'file-based';
    privacy_mode: 'local_only' | 'hybrid' | 'cloud_allowed';
  }>;
}

