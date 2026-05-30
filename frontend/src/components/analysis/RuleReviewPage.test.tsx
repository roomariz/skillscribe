import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RuleReviewPage } from './RuleReviewPage';

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

const reviewPayload = {
  success: true,
  data: {
    analysis_id: 'analysis-001',
    approved_count: 1,
    rejected_count: 0,
    edited_count: 0,
    custom_count: 0,
    ready_for_skill_creation: true,
  },
  timestamp: '2026-05-30T00:00:00Z',
};

function mockAnalysisFetch() {
  return vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(new Response(JSON.stringify(analysisPayload)));
}

describe('RuleReviewPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('rule cards render', async () => {
    mockAnalysisFetch();

    render(<RuleReviewPage analysisId="analysis-001" profileId="muhammad" />);

    expect(await screen.findByText('Precise cadence')).toBeInTheDocument();
    expect(screen.getByText('tone')).toBeInTheDocument();
    expect(screen.getByText('doc-001#s001')).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
  });

  it('approve toggle works', async () => {
    mockAnalysisFetch();
    render(<RuleReviewPage analysisId="analysis-001" profileId="muhammad" />);

    fireEvent.click(await screen.findByRole('checkbox', { name: 'Approve' }));

    const summary = screen.getByRole('complementary');
    expect(within(summary).getByText('Approved')).toBeInTheDocument();
    expect(within(summary).getByText('1')).toBeInTheDocument();
  });

  it('reject toggle works', async () => {
    mockAnalysisFetch();
    render(<RuleReviewPage analysisId="analysis-001" profileId="muhammad" />);

    fireEvent.click(await screen.findByRole('checkbox', { name: 'Reject' }));

    const summary = screen.getByRole('complementary');
    expect(within(summary).getByText('Rejected')).toBeInTheDocument();
    expect(within(summary).getByText('1')).toBeInTheDocument();
  });

  it('edit modal updates rule', async () => {
    mockAnalysisFetch();
    render(<RuleReviewPage analysisId="analysis-001" profileId="muhammad" />);

    fireEvent.click(await screen.findByRole('button', { name: 'Edit' }));
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Edited cadence' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    expect(screen.getByText('Edited cadence')).toBeInTheDocument();
    const summary = screen.getByRole('complementary');
    expect(within(summary).getByText('Edited')).toBeInTheDocument();
    expect(within(summary).getByText('1')).toBeInTheDocument();
  });

  it('custom rule modal adds rule', async () => {
    mockAnalysisFetch();
    render(<RuleReviewPage analysisId="analysis-001" profileId="muhammad" />);

    fireEvent.click(await screen.findByRole('button', { name: 'Add Custom Rule' }));
    fireEvent.change(screen.getByLabelText('Category'), { target: { value: 'structure' } });
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Use headings' } });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Add a heading before sections.' },
    });
    fireEvent.change(screen.getByLabelText('Positive'), { target: { value: 'Summary' } });
    fireEvent.change(screen.getByLabelText('Negative'), { target: { value: 'No heading' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    expect(screen.getByText('Use headings')).toBeInTheDocument();
    expect(screen.getByText('User authored')).toBeInTheDocument();
  });

  it('review summary updates', async () => {
    mockAnalysisFetch();
    render(<RuleReviewPage analysisId="analysis-001" profileId="muhammad" />);

    fireEvent.click(await screen.findByRole('checkbox', { name: 'Approve' }));
    fireEvent.click(screen.getByRole('button', { name: 'Add Custom Rule' }));
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Use headings' } });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Add a heading before sections.' },
    });
    fireEvent.change(screen.getByLabelText('Positive'), { target: { value: 'Summary' } });
    fireEvent.change(screen.getByLabelText('Negative'), { target: { value: 'No heading' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    const summary = screen.getByRole('complementary');
    expect(within(summary).getByText('Approved')).toBeInTheDocument();
    expect(within(summary).getByText('Custom')).toBeInTheDocument();
  });

  it('complete review calls API', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify(analysisPayload)))
      .mockResolvedValueOnce(new Response(JSON.stringify(reviewPayload)));
    render(<RuleReviewPage analysisId="analysis-001" profileId="muhammad" />);

    fireEvent.click(await screen.findByRole('checkbox', { name: 'Approve' }));
    fireEvent.click(screen.getByRole('button', { name: 'Complete Review' }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/profiles/muhammad/analyses/analysis-001/review'),
        expect.objectContaining({ method: 'POST' }),
      ),
    );
    expect(await screen.findByText('Review complete: 1 approved')).toBeInTheDocument();
  });
});
