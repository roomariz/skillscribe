import { useEffect, useState } from 'react';
import { type SkillMetadata, listSkills } from '../../api/client';

type SkillListPageProps = {
  profileId: string;
};

export function SkillListPage({ profileId }: SkillListPageProps) {
  const [skills, setSkills] = useState<SkillMetadata[]>([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    void loadSkills();
  }, [profileId]);

  async function loadSkills() {
    try {
      const response = await listSkills(profileId);
      setSkills(response.data);
      setMessage('');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to load skills');
    }
  }

  return (
    <section className="skills-page" aria-labelledby="skills-title">
      <div className="settings-header">
        <div>
          <h2 id="skills-title">Skills</h2>
          <p>{profileId}</p>
        </div>
        <a href="/">Back</a>
      </div>

      <div className="skill-list">
        {skills.length === 0 ? (
          <p>No skills created yet.</p>
        ) : (
          skills.map((skill) => (
            <article className="skill-card" key={skill.skill_id}>
              <div className="rule-card-header">
                <span className={`lifecycle-badge lifecycle-${skill.lifecycle_status.toLowerCase()}`}>
                  {skill.lifecycle_status}
                </span>
                {skill.default ? <strong>Default</strong> : null}
              </div>
              <h3>{skill.name}</h3>
              <p>Version v{skill.current_version}</p>
              <a href={`/profiles/${profileId}/skills/${skill.skill_id}/approval`}>
                Open Skill
              </a>
            </article>
          ))
        )}
      </div>
      {message ? <p className="analysis-message">{message}</p> : null}
    </section>
  );
}
