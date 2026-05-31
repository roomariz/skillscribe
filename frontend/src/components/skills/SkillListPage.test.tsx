import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SkillListPage } from './SkillListPage';

describe('SkillListPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders skills with lifecycle status', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          success: true,
          data: [
            {
              skill_id: 'legal-drafting',
              profile_id: 'muhammad',
              name: 'Legal Drafting',
              lifecycle_status: 'PENDING',
              current_version: 1,
              default: false,
              created_at: '2026-05-30T00:00:00Z',
              updated_at: '2026-05-30T00:00:00Z',
              versions: [],
            },
          ],
          timestamp: '2026-05-30T00:00:00Z',
        }),
      ),
    );

    render(<SkillListPage profileId="muhammad" />);

    expect(await screen.findByText('Legal Drafting')).toBeInTheDocument();
    expect(screen.getByText('PENDING')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open Skill' })).toHaveAttribute(
      'href',
      '/profiles/muhammad/skills/legal-drafting/approval',
    );
  });
});
