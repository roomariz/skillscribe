import { type FormEvent, useEffect, useMemo, useState } from 'react';
import {
  type ReviewRule,
  type RuleReviewSummary,
  type StyleAnalysis,
  type StyleRule,
  completeRuleReview,
  getStyleAnalysis,
} from '../../api/client';

type RuleReviewPageProps = {
  profileId: string;
  analysisId: string;
};

type EditableRuleFields = Pick<ReviewRule, 'category' | 'title' | 'description' | 'examples'>;

const emptyDraft: EditableRuleFields = {
  category: 'tone',
  title: '',
  description: '',
  examples: { positive: '', negative: '' },
};

export function RuleReviewPage({ profileId, analysisId }: RuleReviewPageProps) {
  const [analysis, setAnalysis] = useState<StyleAnalysis | null>(null);
  const [approvedIds, setApprovedIds] = useState<string[]>([]);
  const [rejectedIds, setRejectedIds] = useState<string[]>([]);
  const [editedRules, setEditedRules] = useState<Record<string, StyleRule>>({});
  const [customRules, setCustomRules] = useState<ReviewRule[]>([]);
  const [editingRule, setEditingRule] = useState<StyleRule | null>(null);
  const [editDraft, setEditDraft] = useState<EditableRuleFields>(emptyDraft);
  const [customDraft, setCustomDraft] = useState<EditableRuleFields>(emptyDraft);
  const [customOpen, setCustomOpen] = useState(false);
  const [summary, setSummary] = useState<RuleReviewSummary | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    void loadAnalysis();
  }, [analysisId, profileId]);

  async function loadAnalysis() {
    try {
      const response = await getStyleAnalysis(profileId, analysisId);
      setAnalysis(response.data);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to load analysis');
    }
  }

  const rules = useMemo(() => analysis?.rules ?? [], [analysis]);
  const editedCount = Object.keys(editedRules).length;

  function toggleApproved(ruleId: string) {
    setApprovedIds((current) =>
      current.includes(ruleId) ? current.filter((id) => id !== ruleId) : [...current, ruleId],
    );
    setRejectedIds((current) => current.filter((id) => id !== ruleId));
  }

  function toggleRejected(ruleId: string) {
    setRejectedIds((current) =>
      current.includes(ruleId) ? current.filter((id) => id !== ruleId) : [...current, ruleId],
    );
    setApprovedIds((current) => current.filter((id) => id !== ruleId));
  }

  function openEdit(rule: StyleRule) {
    setEditingRule(rule);
    setEditDraft({
      category: rule.category,
      title: rule.title,
      description: rule.description,
      examples: rule.examples,
    });
  }

  function saveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingRule) {
      return;
    }
    setEditedRules((current) => ({
      ...current,
      [editingRule.rule_id]: {
        ...editingRule,
        title: editDraft.title,
        description: editDraft.description,
        examples: editDraft.examples,
      },
    }));
    setEditingRule(null);
  }

  function addCustomRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCustomRules((current) => [
      ...current,
      {
        rule_id: `custom-${current.length + 1}`,
        category: customDraft.category,
        title: customDraft.title,
        description: customDraft.description,
        examples: customDraft.examples,
        confidence: 1,
        source: 'user_authored',
        evidence: null,
        source_snippets: [],
      },
    ]);
    setCustomDraft(emptyDraft);
    setCustomOpen(false);
  }

  async function completeReview() {
    const byId = new Map(rules.map((rule) => [rule.rule_id, editedRules[rule.rule_id] ?? rule]));
    const response = await completeRuleReview(profileId, analysisId, {
      approved_rules: approvedIds.map((id) => byId.get(id)).filter(Boolean) as ReviewRule[],
      rejected_rules: rejectedIds.map((id) => byId.get(id)).filter(Boolean) as ReviewRule[],
      edited_rules: Object.values(editedRules),
      custom_rules: customRules,
    });
    setSummary(response.data);
  }

  return (
    <section className="rule-review-page" aria-labelledby="rule-review-title">
      <div className="settings-header">
        <div>
          <h2 id="rule-review-title">Rule Review</h2>
          <p>{analysis ? analysis.skill_name : 'Loading analysis'}</p>
        </div>
        <a href="/">Back</a>
      </div>

      <div className="review-layout">
        <div className="rule-card-list">
          {rules.map((rule) => {
            const displayed = editedRules[rule.rule_id] ?? rule;
            return (
              <article className="review-rule-card" key={rule.rule_id}>
                <div className="rule-card-header">
                  <span className="category-badge">{displayed.category}</span>
                  <strong>{Math.round(displayed.confidence * 100)}%</strong>
                </div>
                <h3>{displayed.title}</h3>
                <p>{displayed.description}</p>
                <dl>
                  <dt>Positive</dt>
                  <dd>{displayed.examples.positive}</dd>
                  <dt>Negative</dt>
                  <dd>{displayed.examples.negative}</dd>
                  <dt>Evidence</dt>
                  <dd>{displayed.evidence.join(', ')}</dd>
                </dl>
                <div className="rule-decision-row">
                  <label>
                    <input
                      checked={approvedIds.includes(rule.rule_id)}
                      onChange={() => toggleApproved(rule.rule_id)}
                      type="checkbox"
                    />
                    <span>Approve</span>
                  </label>
                  <label>
                    <input
                      checked={rejectedIds.includes(rule.rule_id)}
                      onChange={() => toggleRejected(rule.rule_id)}
                      type="checkbox"
                    />
                    <span>Reject</span>
                  </label>
                  <button onClick={() => openEdit(displayed)} type="button">
                    Edit
                  </button>
                </div>
              </article>
            );
          })}
          {customRules.map((rule) => (
            <article className="review-rule-card" key={rule.rule_id}>
              <div className="rule-card-header">
                <span className="category-badge">{rule.category}</span>
                <strong>User authored</strong>
              </div>
              <h3>{rule.title}</h3>
              <p>{rule.description}</p>
            </article>
          ))}
        </div>

        <aside className="review-summary-panel">
          <h3>Review Summary</h3>
          <dl>
            <dt>Approved</dt>
            <dd>{approvedIds.length}</dd>
            <dt>Rejected</dt>
            <dd>{rejectedIds.length}</dd>
            <dt>Edited</dt>
            <dd>{editedCount}</dd>
            <dt>Custom</dt>
            <dd>{customRules.length}</dd>
          </dl>
          <button onClick={() => setCustomOpen(true)} type="button">
            Add Custom Rule
          </button>
          <button onClick={() => void completeReview()} type="button">
            Complete Review
          </button>
          {summary ? <p>Review complete: {summary.approved_count} approved</p> : null}
          {message ? <p>{message}</p> : null}
        </aside>
      </div>

      {editingRule ? (
        <RuleFormModal
          draft={editDraft}
          onChange={setEditDraft}
          onClose={() => setEditingRule(null)}
          onSubmit={saveEdit}
          title="Edit Rule"
        />
      ) : null}

      {customOpen ? (
        <RuleFormModal
          draft={customDraft}
          onChange={setCustomDraft}
          onClose={() => setCustomOpen(false)}
          onSubmit={addCustomRule}
          title="Custom Rule"
        />
      ) : null}
    </section>
  );
}

type RuleFormModalProps = {
  draft: EditableRuleFields;
  onChange: (draft: EditableRuleFields) => void;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  title: string;
};

function RuleFormModal({ draft, onChange, onClose, onSubmit, title }: RuleFormModalProps) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={title}>
      <form className="rule-modal" onSubmit={onSubmit}>
        <h3>{title}</h3>
        <label>
          Category
          <input
            onChange={(event) => onChange({ ...draft, category: event.target.value })}
            required
            value={draft.category}
          />
        </label>
        <label>
          Title
          <input
            onChange={(event) => onChange({ ...draft, title: event.target.value })}
            required
            value={draft.title}
          />
        </label>
        <label>
          Description
          <textarea
            onChange={(event) => onChange({ ...draft, description: event.target.value })}
            required
            value={draft.description}
          />
        </label>
        <label>
          Positive
          <input
            onChange={(event) =>
              onChange({ ...draft, examples: { ...draft.examples, positive: event.target.value } })
            }
            required
            value={draft.examples.positive}
          />
        </label>
        <label>
          Negative
          <input
            onChange={(event) =>
              onChange({ ...draft, examples: { ...draft.examples, negative: event.target.value } })
            }
            required
            value={draft.examples.negative}
          />
        </label>
        <div className="rule-decision-row">
          <button type="submit">Save</button>
          <button onClick={onClose} type="button">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
