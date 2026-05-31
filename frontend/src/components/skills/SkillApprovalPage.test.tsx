import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SkillApprovalPage } from './SkillApprovalPage';

const detail = (status: 'PENDING' | 'APPROVED' | 'ACTIVE') => ({
  success: true,
  data: {
    metadata: {
      skill_id: 'legal-drafting',
      profile_id: 'muhammad',
      name: 'Legal Drafting',
      lifecycle_status: status,
      current_version: 1,
      default: status === 'ACTIVE',
      created_at: '2026-05-30T00:00:00Z',
      updated_at: '2026-05-30T00:00:00Z',
      versions: [],
    },
    skill: {
      skill_id: 'legal-drafting',
      profile_id: 'muhammad',
      name: 'Legal Drafting',
      lifecycle_status: status,
      version: 1,
      rules: [
        {
          rule_id: 'rule-001',
          category: 'tone',
          title: 'Precise cadence',
          description: 'Use concise sentences.',
          examples: { positive: 'Proceed today.', negative: 'Maybe later perhaps.' },
          confidence: 0.82,
          source: 'document_derived',
          evidence: ['doc-001#s001'],
        },
      ],
      created_at: '2026-05-30T00:00:00Z',
      updated_at: '2026-05-30T00:00:00Z',
    },
  },
  timestamp: '2026-05-30T00:00:00Z',
});

describe('SkillApprovalPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('approves a pending skill', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(JSON.stringify(detail('PENDING'))))
      .mockResolvedValueOnce(new Response(JSON.stringify(detail('APPROVED'))));

    render(<SkillApprovalPage profileId="muhammad" skillId="legal-drafting" />);

    expect(await screen.findByText('Precise cadence')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Approve' }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/profiles/muhammad/skills/legal-drafting/approve'),
        expect.objectContaining({ method: 'POST' }),
      ),
    );
    expect(await screen.findByText('Skill approved.')).toBeInTheDocument();
  });
});
