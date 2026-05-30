import { type ChangeEvent, type FormEvent, useEffect, useMemo, useState } from 'react';
import {
  type DocumentMetadata,
  type ExtractedTextPreview,
  type Profile,
  type UploadProgress,
  createProfile,
  getProfile,
  listProfiles,
  previewDocument,
  updateExtractedText,
  uploadDocument,
} from '../../api/client';
import { AnalysisPanel } from '../analysis/AnalysisPanel';

export function ProfileSelector() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<(Profile & { documents: DocumentMetadata[] }) | null>(
    null,
  );
  const [displayName, setDisplayName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedDocument, setSelectedDocument] = useState<DocumentMetadata | null>(null);
  const [preview, setPreview] = useState<ExtractedTextPreview | null>(null);
  const [draftText, setDraftText] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);

  useEffect(() => {
    void refreshProfiles();
  }, []);

  const createdLabel = useMemo(() => {
    if (!selectedProfile) {
      return '';
    }
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(selectedProfile.created_at));
  }, [selectedProfile]);

  async function refreshProfiles() {
    try {
      const response = await listProfiles();
      setProfiles(response.data);
      setMessage('');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to load profiles');
    }
  }

  async function selectProfile(profileId: string) {
    try {
      const response = await getProfile(profileId);
      setSelectedProfile(response.data);
      setSelectedDocument(null);
      setPreview(null);
      setDraftText('');
      setMessage('');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to load profile');
    }
  }

  async function handleCreateProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsBusy(true);
    try {
      const response = await createProfile({ display_name: displayName, description });
      setDisplayName('');
      setDescription('');
      await refreshProfiles();
      await selectProfile(response.data.profile_id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to create profile');
    } finally {
      setIsBusy(false);
    }
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !selectedProfile) {
      return;
    }
    setIsBusy(true);
    setUploadProgress({ stage: 'Uploading', percentage: 5 });
    const stagedProgress: UploadProgress[] = [
      { stage: 'Uploading', percentage: 25 },
      { stage: 'Extracting text', percentage: 55 },
      { stage: 'Saving metadata', percentage: 82 },
    ];
    let stagedIndex = 0;
    const progressTimer = window.setInterval(() => {
      const next = stagedProgress[Math.min(stagedIndex, stagedProgress.length - 1)];
      setUploadProgress((current) => {
        if (!current || current.percentage < next.percentage) {
          return next;
        }
        return current;
      });
      stagedIndex += 1;
    }, 350);
    try {
      const response = await uploadDocument(selectedProfile.profile_id, file, (progress) => {
        setUploadProgress((current) => {
          if (!current || progress.percentage >= current.percentage) {
            return progress;
          }
          return current;
        });
      });
      setUploadProgress({ stage: 'Complete', percentage: 100 });
      await selectProfile(selectedProfile.profile_id);
      await openPreview(response.data);
      setMessage('Document uploaded and extracted.');
    } catch (error) {
      setUploadProgress(null);
      setMessage(error instanceof Error ? error.message : 'Unable to upload document');
    } finally {
      window.clearInterval(progressTimer);
      event.target.value = '';
      setIsBusy(false);
    }
  }

  async function openPreview(document: DocumentMetadata) {
    if (!selectedProfile) {
      return;
    }
    const response = await previewDocument(selectedProfile.profile_id, document.doc_id);
    setSelectedDocument(document);
    setPreview(response.data);
    setDraftText(response.data.preview);
  }

  async function handleSaveText() {
    if (!selectedProfile || !selectedDocument) {
      return;
    }
    setIsBusy(true);
    try {
      const response = await updateExtractedText(
        selectedProfile.profile_id,
        selectedDocument.doc_id,
        draftText,
      );
      await selectProfile(selectedProfile.profile_id);
      await openPreview(response.data);
      setMessage('Extracted text updated.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to update extracted text');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="profile-workspace" aria-labelledby="profile-selector-title">
      <div className="profile-sidebar">
        <div className="section-heading">
          <h2 id="profile-selector-title">Profiles</h2>
          <span>{profiles.length}</span>
        </div>

        <div className="profile-list" aria-label="Profiles">
          {profiles.length === 0 ? (
            <p>No profiles yet.</p>
          ) : (
            profiles.map((profile) => (
              <button
                className="profile-row"
                key={profile.profile_id}
                onClick={() => void selectProfile(profile.profile_id)}
                type="button"
              >
                <strong>{profile.display_name}</strong>
                <span>
                  {profile.document_count} documents | {profile.skill_count} skills
                </span>
              </button>
            ))
          )}
        </div>

        <form className="profile-form" onSubmit={(event) => void handleCreateProfile(event)}>
          <label htmlFor="display-name">Name</label>
          <input
            id="display-name"
            onChange={(event) => setDisplayName(event.target.value)}
            required
            value={displayName}
          />
          <label htmlFor="profile-description">Description</label>
          <textarea
            id="profile-description"
            onChange={(event) => setDescription(event.target.value)}
            rows={3}
            value={description}
          />
          <button disabled={isBusy} type="submit">
            Create Profile
          </button>
        </form>
      </div>

      <div className="profile-dashboard">
        {selectedProfile ? (
          <>
            <div className="dashboard-header">
              <div>
                <h2>{selectedProfile.display_name}</h2>
                <p>Created {createdLabel}</p>
              </div>
              <label className="upload-control">
                <span>{isBusy ? 'Working...' : 'Upload Document'}</span>
                <input
                  accept=".pdf,.docx,.txt"
                  disabled={isBusy}
                  onChange={(event) => void handleUpload(event)}
                  type="file"
                />
              </label>
            </div>
            {uploadProgress ? (
              <div className="upload-progress" aria-label="Upload progress">
                <div className="progress-copy">
                  <strong>{uploadProgress.stage}</strong>
                  <span>{uploadProgress.percentage}%</span>
                </div>
                <div
                  aria-valuemax={100}
                  aria-valuemin={0}
                  aria-valuenow={uploadProgress.percentage}
                  className="progress-track"
                  role="progressbar"
                >
                  <span style={{ width: `${uploadProgress.percentage}%` }} />
                </div>
              </div>
            ) : null}
            <AnalysisPanel
              documents={selectedProfile.documents}
              profileId={selectedProfile.profile_id}
            />

            <div className="document-grid">
              <div className="document-list">
                <div className="section-heading">
                  <h3>Documents</h3>
                  <span>{selectedProfile.documents.length}</span>
                </div>
                {selectedProfile.documents.length === 0 ? (
                  <p>No documents uploaded.</p>
                ) : (
                  selectedProfile.documents.map((document) => (
                    <button
                      className="document-row"
                      key={document.doc_id}
                      onClick={() => void openPreview(document)}
                      type="button"
                    >
                      <strong>{document.original_filename}</strong>
                      <span>
                        {document.status} | {document.word_count} words
                      </span>
                    </button>
                  ))
                )}
              </div>

              <div className="preview-panel">
                <div className="section-heading">
                  <h3>Preview</h3>
                  {preview ? <span>{preview.character_count} chars</span> : null}
                </div>
                {preview ? (
                  <>
                    <p>{preview.filename}</p>
                    <textarea
                      aria-label="Extracted text"
                      onChange={(event) => setDraftText(event.target.value)}
                      rows={14}
                      value={draftText}
                    />
                    <button disabled={isBusy} onClick={() => void handleSaveText()} type="button">
                      Save Extracted Text
                    </button>
                  </>
                ) : (
                  <p>Select a document to preview extracted text.</p>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="empty-dashboard">
            <h2>Profile Dashboard</h2>
            <p>Select or create a profile to manage local documents.</p>
          </div>
        )}
      </div>

      {message ? <p className="status-message">{message}</p> : null}
    </section>
  );
}
