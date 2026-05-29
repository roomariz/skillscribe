import { afterEach, describe, expect, it, vi } from 'vitest';
import { getStatus } from './client';

describe('getStatus', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads the API status envelope', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: { database_type: 'file-based', privacy_mode: 'local_only' },
          timestamp: '2026-05-30T00:00:00Z',
        }),
      ),
    );

    await expect(getStatus()).resolves.toMatchObject({
      success: true,
      data: { database_type: 'file-based', privacy_mode: 'local_only' },
    });
  });

  it('throws when status cannot be loaded', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 500 }));

    await expect(getStatus()).rejects.toThrow('Unable to load API status');
  });
});

