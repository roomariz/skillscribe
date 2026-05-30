import { AppShell } from '../components/layout/AppShell';
import { ProfileSelector } from '../components/profiles/ProfileSelector';
import { SettingsPage } from '../components/settings/SettingsPage';

export function App() {
  return (
    <AppShell>
      <SettingsPage />
      <ProfileSelector />
    </AppShell>
  );
}
