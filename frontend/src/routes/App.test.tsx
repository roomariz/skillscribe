import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from './App';

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the application shell', () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith('/api/config')) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              success: true,
              data: {
                providers: [],
                privacy_mode: 'local_only',
                max_upload_size_mb: 50,
                storage_path: './data',
              },
              timestamp: '2026-05-30T00:00:00Z',
            }),
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ success: true, data: [], timestamp: '2026-05-30T00:00:00Z' })),
      );
    });

    render(<App />);

    expect(screen.getByRole('heading', { name: 'Hermes Writer' })).toBeInTheDocument();
    expect(screen.getAllByText('Local Only').length).toBeGreaterThan(0);
  });
});
