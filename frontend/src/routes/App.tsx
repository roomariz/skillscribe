import { AppShell } from '../components/layout/AppShell';
import { RuleReviewPage } from '../components/analysis/RuleReviewPage';
import { ProfileSelector } from '../components/profiles/ProfileSelector';
import { SettingsPage } from '../components/settings/SettingsPage';

export function App() {
  const reviewMatch = window.location.pathname.match(
    /^\/profiles\/([^/]+)\/analyses\/([^/]+)\/review$/,
  );
  if (reviewMatch) {
    return (
      <AppShell>
        <RuleReviewPage analysisId={reviewMatch[2]} profileId={reviewMatch[1]} />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <SettingsPage />
      <ProfileSelector />
    </AppShell>
  );
}
