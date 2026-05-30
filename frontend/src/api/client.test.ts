import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  createProfile,
  getConfig,
  getStatus,
  listProfiles,
  previewDocument,
  testProvider,
  updateExtractedText,
  updatePrivacyMode,
  uploadDocument,
} from './client';

describe('getStatus', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
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

  it('loads profiles', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: [{ profile_id: 'muhammad', display_name: 'Muhammad' }],
          timestamp: '2026-05-30T00:00:00Z',
        }),
      ),
    );

    await expect(listProfiles()).resolves.toMatchObject({
      data: [{ profile_id: 'muhammad' }],
    });
  });

  it('loads and updates config', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              providers: [{ name: 'ollama', available: true, configured: true }],
              privacy_mode: 'local_only',
              max_upload_size_mb: 50,
              storage_path: './data',
            },
            timestamp: '2026-05-30T00:00:00Z',
          }),
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              providers: [{ name: 'ollama', available: true, configured: true }],
              privacy_mode: 'hybrid',
              max_upload_size_mb: 50,
              storage_path: './data',
            },
            timestamp: '2026-05-30T00:00:00Z',
          }),
        ),
      );

    await expect(getConfig()).resolves.toMatchObject({
      data: { privacy_mode: 'local_only' },
    });
    await updatePrivacyMode('hybrid');

    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/config/update-privacy-mode'),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('tests provider connections', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: { provider: 'ollama', connected: true, model: 'ollama/mistral' },
          timestamp: '2026-05-30T00:00:00Z',
        }),
      ),
    );

    await expect(testProvider('ollama')).resolves.toMatchObject({
      data: { connected: true },
    });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/config/test-provider'),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('creates profiles with JSON payloads', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: { profile_id: 'muhammad', display_name: 'Muhammad' },
          timestamp: '2026-05-30T00:00:00Z',
        }),
      ),
    );

    await createProfile({ display_name: 'Muhammad' });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/profiles'),
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('loads previews and updates extracted text', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: { doc_id: 'doc-001', preview: 'text' },
            timestamp: '2026-05-30T00:00:00Z',
          }),
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: { doc_id: 'doc-001', extraction_method: 'manual' },
            timestamp: '2026-05-30T00:00:00Z',
          }),
        ),
      );

    await expect(previewDocument('muhammad', 'doc-001')).resolves.toMatchObject({
      data: { preview: 'text' },
    });
    await updateExtractedText('muhammad', 'doc-001', 'new text');

    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/profiles/muhammad/documents/doc-001/extracted-text'),
      expect.objectContaining({ method: 'PUT' }),
    );
  });

  it('uploads documents with actual XMLHttpRequest progress', async () => {
    const progress = vi.fn();
    class MockXMLHttpRequest {
      status = 201;
      responseText = JSON.stringify({
        success: true,
        data: {
          doc_id: 'doc-001',
          profile_id: 'muhammad',
          original_filename: 'sample.txt',
          file_type: 'txt',
          file_size_bytes: 4,
          uploaded_at: '2026-05-30T00:00:00Z',
          extraction_method: 'plain-text',
          word_count: 1,
          character_count: 4,
          status: 'extracted',
        },
        timestamp: '2026-05-30T00:00:00Z',
      });
      upload = { onprogress: (_event: ProgressEvent) => undefined };
      onload = () => undefined;
      onerror = () => undefined;
      open = vi.fn();
      send = vi.fn(() => {
        this.upload.onprogress({ lengthComputable: true, loaded: 2, total: 4 } as ProgressEvent);
        this.onload();
      });
    }
    vi.stubGlobal('XMLHttpRequest', MockXMLHttpRequest);

    await expect(uploadDocument('muhammad', new File(['text'], 'sample.txt'), progress)).resolves.toMatchObject({
      data: { doc_id: 'doc-001' },
    });

    expect(progress).toHaveBeenCalledWith({ stage: 'Uploading', percentage: 23 });
    expect(progress).toHaveBeenCalledWith({ stage: 'Complete', percentage: 100 });
  });
});
