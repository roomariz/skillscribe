import { useEffect, useState } from 'react';
import {
  type SkillDetail,
  activateSkill,
  approveSkill,
  getSkill,
  setDefaultSkill,
} from '../../api/client';

type SkillApprovalPageProps = {
  profileId: string;
  skillId: string;
};

export function SkillApprovalPage({ profileId, skillId }: SkillApprovalPageProps) {
  const [detail, setDetail] = useState<SkillDetail | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    void loadSkill();
  }, [profileId, skillId]);

  async function loadSkill() {
    try {
      const response = await getSkill(profileId, skillId);
      setDetail(response.data);
      setMessage('');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to load skill');
    }
  }

  async function approve() {
    const response = await approveSkill(profileId, skillId);
    setDetail(response.data);
    setMessage('Skill approved.');
  }

  async function activate() {
    const response = await activateSkill(profileId, skillId);
    setDetail(response.data);
    setMessage('Skill activated.');
  }

  async function setDefault() {
    const response = await setDefaultSkill(profileId, skillId);
    setDetail(response.data);
    setMessage('Default skill updated.');
  }

  const status = detail?.metadata.lifecycle_status;

  return (
    <section className="skills-page" aria-labelledby="skill-approval-title">
      <div className="settings-header">
        <div>
          <h2 id="skill-approval-title">{detail ? detail.skill.name : 'Skill'}</h2>
          <p>{detail ? `v${detail.metadata.current_version} | ${detail.metadata.lifecycle_status}` : 'Loading'}</p>
        </div>
        <a href={`/profiles/${profileId}/skills`}>Back</a>
      </div>

      {detail ? (
        <>
          <div className="skill-action-bar">
            <button disabled={status !== 'PENDING'} onClick={() => void approve()} type="button">
              Approve
            </button>
            <button disabled={status !== 'APPROVED'} onClick={() => void activate()} type="button">
              Activate
            </button>
            <button disabled={status !== 'ACTIVE'} onClick={() => void setDefault()} type="button">
              Set Default
            </button>
          </div>

          <div className="skill-json-preview">
            <h3>skill.json</h3>
            <pre>{JSON.stringify(detail.skill, null, 2)}</pre>
          </div>

          <div className="rule-card-list">
            {detail.skill.rules.map((rule) => (
              <article className="review-rule-card" key={rule.rule_id}>
                <div className="rule-card-header">
                  <span className="category-badge">{rule.category}</span>
                  <strong>{rule.source === 'user_authored' ? 'User' : 'Evidence'}</strong>
                </div>
                <h3>{rule.title}</h3>
                <p>{rule.description}</p>
              </article>
            ))}
          </div>
        </>
      ) : null}
      {message ? <p className="analysis-message">{message}</p> : null}
    </section>
  );
}
