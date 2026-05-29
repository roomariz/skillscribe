import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { App } from './App';

describe('App', () => {
  it('renders the application shell', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Hermes Writer' })).toBeInTheDocument();
    expect(screen.getByText('Local Only')).toBeInTheDocument();
  });
});

