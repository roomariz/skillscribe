import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SettingsPage } from './SettingsPage';

const configPayload = {
  success: true,
  data: {
    privacy_mode: 'local_only',
    max_upload_size_mb: 50,
    storage_path: './data',
    providers: [
      { name: 'ollama', available: true, configured: true, model: 'ollama' },
      { name: 'groq', available: false, configured: false, model: null },
    ],
  },
  timestamp: '2026-05-30T00:00:00Z',
};

describe('SettingsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('privacy_selector_renders', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(configPayload)));

    render(<SettingsPage />);

    expect(await screen.findByRole('radio', { name: 'Local Only' })).toBeChecked();
    expect(screen.getByRole('radio', { name: 'Hybrid' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Cloud Allowed' })).toBeInTheDocument();
  });

  it('privacy_selector_updates_mode', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify(configPayload)))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            ...configPayload,
            data: { ...configPayload.data, privacy_mode: 'hybrid' },
          }),
        ),
      );

    render(<SettingsPage />);

    fireEvent.click(await screen.findByRole('radio', { name: 'Hybrid' }));

    await waitFor(() => expect(screen.getByRole('radio', { name: 'Hybrid' })).toBeChecked());
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/config/update-privacy-mode'),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('provider_status_list_renders', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(configPayload)));

    render(<SettingsPage />);

    expect(await screen.findByText('ollama')).toBeInTheDocument();
    expect(screen.getByText('configured | available')).toBeInTheDocument();
    expect(screen.getByText('groq')).toBeInTheDocument();
    expect(screen.getByText('not configured | unavailable')).toBeInTheDocument();
  });

  it('provider_test_button_calls_api', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify(configPayload)))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: { provider: 'ollama', connected: true, model: 'ollama/mistral' },
            timestamp: '2026-05-30T00:00:00Z',
          }),
        ),
      );

    render(<SettingsPage />);

    fireEvent.click(await screen.findAllByRole('button', { name: 'Test Connection' }).then((buttons) => buttons[0]));

    await screen.findByText('ollama/mistral');
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/config/test-provider'),
      expect.objectContaining({ method: 'POST' }),
    );
  });
});
