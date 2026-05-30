import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from './App';

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the application shell', () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ success: true, data: [], timestamp: '2026-05-30T00:00:00Z' })),
    );

    render(<App />);

    expect(screen.getByRole('heading', { name: 'Hermes Writer' })).toBeInTheDocument();
    expect(screen.getByText('Local Only')).toBeInTheDocument();
  });
});
