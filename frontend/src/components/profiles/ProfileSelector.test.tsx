import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ProfileSelector } from './ProfileSelector';

describe('ProfileSelector', () => {
  it('renders the Sprint 1 placeholder', () => {
    render(<ProfileSelector />);

    expect(screen.getByRole('heading', { name: 'Profiles' })).toBeInTheDocument();
    expect(screen.getByText(/Profile creation starts in Sprint 2/)).toBeInTheDocument();
  });
});

