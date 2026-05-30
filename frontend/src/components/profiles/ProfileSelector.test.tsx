import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ProfileSelector } from './ProfileSelector';

const envelope = (data: unknown) =>
  new Response(JSON.stringify({ success: true, data, timestamp: '2026-05-30T00:00:00Z' }));

const profile = {
  profile_id: 'muhammad',
  display_name: 'Muhammad',
  description: 'Legal drafting',
  created_at: '2026-05-30T00:00:00Z',
  updated_at: '2026-05-30T00:00:00Z',
  default_skill: null,
  document_count: 1,
  skill_count: 0,
};

const documentMetadata = {
  doc_id: 'doc-001',
  profile_id: 'muhammad',
  original_filename: 'sample.txt',
  file_type: 'txt',
  file_size_bytes: 12,
  uploaded_at: '2026-05-30T00:00:00Z',
  extraction_method: 'plain-text',
  word_count: 2,
  character_count: 12,
  status: 'extracted',
};

describe('ProfileSelector', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it('renders profile list and opens the dashboard', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(envelope([profile]))
      .mockResolvedValueOnce(envelope({ ...profile, documents: [documentMetadata] }))
      .mockResolvedValueOnce(
        envelope({
          doc_id: 'doc-001',
          filename: 'sample.txt',
          preview: 'Extracted text',
          character_count: 14,
          truncated: false,
        }),
      );

    render(<ProfileSelector />);

    expect(await screen.findByRole('button', { name: /Muhammad/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Muhammad/ }));

    expect(await screen.findByRole('heading', { name: 'Documents' })).toBeInTheDocument();
    fireEvent.click(await screen.findByRole('button', { name: /sample.txt/ }));

    expect(await screen.findByLabelText('Extracted text')).toHaveValue('Extracted text');
  });

  it('creates a profile from the form', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(envelope([]))
      .mockResolvedValueOnce(envelope(profile))
      .mockResolvedValueOnce(envelope([profile]))
      .mockResolvedValueOnce(envelope({ ...profile, documents: [] }));

    render(<ProfileSelector />);

    fireEvent.change(await screen.findByLabelText('Name'), { target: { value: 'Muhammad' } });
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'Legal drafting' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create Profile' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    expect(await screen.findByText(/Select a document to preview/)).toBeInTheDocument();
  });

  it('shows staged upload and extraction progress while a document is processing', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(envelope([profile]))
      .mockResolvedValueOnce(envelope({ ...profile, documents: [] }))
      .mockResolvedValueOnce(envelope({ ...profile, documents: [documentMetadata] }))
      .mockResolvedValueOnce(
        envelope({
          doc_id: 'doc-001',
          filename: 'sample.txt',
          preview: 'Extracted text',
          character_count: 14,
          truncated: false,
        }),
      );

    let xhr: { onload: () => void } | null = null;
    class MockXMLHttpRequest {
      status = 201;
      responseText = JSON.stringify({
        success: true,
        data: documentMetadata,
        timestamp: '2026-05-30T00:00:00Z',
      });
      upload = { onprogress: (_event: ProgressEvent) => undefined };
      onload = () => undefined;
      onerror = () => undefined;
      open = vi.fn();
      send = vi.fn(() => {
        xhr = this;
      });
    }
    vi.stubGlobal('XMLHttpRequest', MockXMLHttpRequest);

    render(<ProfileSelector />);
    fireEvent.click(await screen.findByRole('button', { name: /Muhammad/ }));

    const input = await screen.findByLabelText('Upload Document');
    fireEvent.change(input, {
      target: { files: [new File(['Extracted text'], 'sample.txt', { type: 'text/plain' })] },
    });

    expect(await screen.findByRole('progressbar')).toHaveAttribute('aria-valuenow', '5');
    expect(screen.getByText('Uploading')).toBeInTheDocument();

    expect(await screen.findByText('Extracting text', undefined, { timeout: 1200 })).toBeInTheDocument();

    await act(async () => {
      xhr?.onload();
      await Promise.resolve();
      await Promise.resolve();
    });

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
    expect(await screen.findByLabelText('Extracted text')).toHaveValue('Extracted text');
  });
});
