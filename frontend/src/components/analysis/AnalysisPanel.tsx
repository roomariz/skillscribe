import { type FormEvent, useState } from 'react';
import {
  type DocumentMetadata,
  type StyleAnalysis,
  startStyleAnalysis,
} from '../../api/client';

type AnalysisPanelProps = {
  profileId: string;
  documents: DocumentMetadata[];
};

export function AnalysisPanel({ profileId, documents }: AnalysisPanelProps) {
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [skillName, setSkillName] = useState('');
  const [analysis, setAnalysis] = useState<StyleAnalysis | null>(null);
  const [message, setMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  function toggleDocument(docId: string) {
    setSelectedDocumentIds((current) =>
      current.includes(docId) ? current.filter((id) => id !== docId) : [...current, docId],
    );
  }

  async function handleStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsBusy(true);
    try {
      const response = await startStyleAnalysis(profileId, {
        document_ids: selectedDocumentIds,
        skill_name: skillName,
      });
      setAnalysis(response.data);
      setMessage('');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to start style analysis');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="analysis-panel" aria-labelledby="analysis-title">
      <div className="section-heading">
        <h3 id="analysis-title">Style Analysis</h3>
        {analysis ? <span>{Math.round(analysis.progress * 100)}%</span> : null}
      </div>

      <form className="analysis-form" onSubmit={(event) => void handleStart(event)}>
        <label htmlFor="skill-name">Skill name</label>
        <input
          id="skill-name"
          onChange={(event) => setSkillName(event.target.value)}
          required
          value={skillName}
        />

        <fieldset>
          <legend>Documents</legend>
          {documents.length === 0 ? (
            <p>No documents available.</p>
          ) : (
            documents.map((document) => (
              <label key={document.doc_id}>
                <input
                  checked={selectedDocumentIds.includes(document.doc_id)}
                  onChange={() => toggleDocument(document.doc_id)}
                  type="checkbox"
                />
                <span>{document.original_filename}</span>
              </label>
            ))
          )}
        </fieldset>

        <button disabled={isBusy || selectedDocumentIds.length === 0} type="submit">
          {isBusy ? 'Analyzing...' : 'Start Analysis'}
        </button>
      </form>

      {analysis ? (
        <div className="analysis-results" aria-label="Analysis results">
          <p>
            {analysis.status} via {analysis.provider}
          </p>
          {analysis.rules.map((rule) => (
            <article className="rule-preview" key={rule.rule_id}>
              <div className="section-heading">
                <h4>{rule.title}</h4>
                <span>{Math.round(rule.confidence * 100)}%</span>
              </div>
              <p>{rule.description}</p>
              <dl>
                <dt>Positive</dt>
                <dd>{rule.examples.positive}</dd>
                <dt>Negative</dt>
                <dd>{rule.examples.negative}</dd>
                <dt>Evidence</dt>
                <dd>{rule.evidence.join(', ')}</dd>
              </dl>
            </article>
          ))}
        </div>
      ) : null}

      {message ? <p className="analysis-message">{message}</p> : null}
    </section>
  );
}
