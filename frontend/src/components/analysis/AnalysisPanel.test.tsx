import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AnalysisPanel } from './AnalysisPanel';

const documents = [
  {
    doc_id: 'doc-001',
    profile_id: 'muhammad',
    original_filename: 'sample.txt',
    file_type: 'txt' as const,
    file_size_bytes: 25,
    uploaded_at: '2026-05-30T00:00:00Z',
    extraction_method: 'plain-text',
    word_count: 4,
    character_count: 25,
    status: 'extracted',
  },
];

const analysisPayload = {
  success: true,
  data: {
    analysis_id: 'analysis-001',
    status: 'completed',
    progress: 1,
    skill_name: 'Legal',
    provider: 'ollama',
    privacy_mode: 'local_only',
    document_ids: ['doc-001'],
    rules: [
      {
        rule_id: 'rule-001',
        category: 'tone',
        title: 'Precise cadence',
        description: 'Use concise sentences.',
        examples: { positive: 'Proceed today.', negative: 'Maybe later perhaps.' },
        source: 'document_derived',
        evidence: ['doc-001#s001'],
        source_snippets: ['Raw private sentence.'],
        confidence: 0.82,
      },
    ],
  },
  timestamp: '2026-05-30T00:00:00Z',
};

describe('AnalysisPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('analysis form renders', () => {
    render(<AnalysisPanel documents={documents} profileId="muhammad" />);

    expect(screen.getByRole('heading', { name: 'Style Analysis' })).toBeInTheDocument();
    expect(screen.getByLabelText('Skill name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start Analysis' })).toBeDisabled();
  });

  it('document selection works', () => {
    render(<AnalysisPanel documents={documents} profileId="muhammad" />);

    const checkbox = screen.getByRole('checkbox', { name: 'sample.txt' });
    fireEvent.click(checkbox);

    expect(checkbox).toBeChecked();
    expect(screen.getByRole('button', { name: 'Start Analysis' })).toBeEnabled();
  });

  it('start analysis calls API', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify(analysisPayload)));
    render(<AnalysisPanel documents={documents} profileId="muhammad" />);

    fireEvent.change(screen.getByLabelText('Skill name'), { target: { value: 'Legal' } });
    fireEvent.click(screen.getByRole('checkbox', { name: 'sample.txt' }));
    fireEvent.click(screen.getByRole('button', { name: 'Start Analysis' }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/api/profiles/muhammad/analyze-style'),
        expect.objectContaining({ method: 'POST' }),
      ),
    );
  });

  it('returned rules display read-only', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(analysisPayload)));
    render(<AnalysisPanel documents={documents} profileId="muhammad" />);

    fireEvent.change(screen.getByLabelText('Skill name'), { target: { value: 'Legal' } });
    fireEvent.click(screen.getByRole('checkbox', { name: 'sample.txt' }));
    fireEvent.click(screen.getByRole('button', { name: 'Start Analysis' }));

    expect(await screen.findByText('Precise cadence')).toBeInTheDocument();
    expect(screen.getByText('doc-001#s001')).toBeInTheDocument();
    expect(screen.queryByText('Approve')).not.toBeInTheDocument();
    expect(screen.queryByText('Reject')).not.toBeInTheDocument();
  });
});
