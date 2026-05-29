import type { ReactNode } from 'react';

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Hermes Writer</h1>
          <p>Local-first writing skill assistant</p>
        </div>
        <span className="status-pill">Local Only</span>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}

