import { AppShell } from '../components/layout/AppShell';
import { RuleReviewPage } from '../components/analysis/RuleReviewPage';
import { ProfileSelector } from '../components/profiles/ProfileSelector';
import { SettingsPage } from '../components/settings/SettingsPage';
import { SkillApprovalPage } from '../components/skills/SkillApprovalPage';
import { SkillListPage } from '../components/skills/SkillListPage';

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

  const skillApprovalMatch = window.location.pathname.match(
    /^\/profiles\/([^/]+)\/skills\/([^/]+)\/approval$/,
  );
  if (skillApprovalMatch) {
    return (
      <AppShell>
        <SkillApprovalPage profileId={skillApprovalMatch[1]} skillId={skillApprovalMatch[2]} />
      </AppShell>
    );
  }

  const skillsMatch = window.location.pathname.match(/^\/profiles\/([^/]+)\/skills$/);
  if (skillsMatch) {
    return (
      <AppShell>
        <SkillListPage profileId={skillsMatch[1]} />
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
