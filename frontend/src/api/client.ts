export type ApiEnvelope<T> = {
  success: true;
  data: T;
  timestamp: string;
};

export type ApiErrorEnvelope = {
  success: false;
  error_code: string;
  message: string;
  timestamp: string;
  details?: Record<string, unknown>;
  recovery_hint?: string;
};

export type Profile = {
  profile_id: string;
  display_name: string;
  description: string;
  created_at: string;
  updated_at: string;
  default_skill: string | null;
  document_count: number;
  skill_count: number;
};

export type SkillLifecycleStatus = 'PENDING' | 'APPROVED' | 'ACTIVE';

export type SkillMetadata = {
  skill_id: string;
  profile_id: string;
  name: string;
  lifecycle_status: SkillLifecycleStatus;
  current_version: number;
  default: boolean;
  created_at: string;
  updated_at: string;
  versions: Array<{
    version: number;
    status: SkillLifecycleStatus;
    created_at: string;
    approved_at: string | null;
    activated_at: string | null;
    change_summary: string;
    path: string;
  }>;
};

export type Skill = {
  skill_id: string;
  profile_id: string;
  name: string;
  lifecycle_status: SkillLifecycleStatus;
  version: number;
  rules: Array<{
    rule_id: string;
    category: string;
    title: string;
    description: string;
    examples: {
      positive: string;
      negative: string;
    };
    confidence: number;
    source: 'document_derived' | 'user_authored';
    evidence: string[] | null;
  }>;
  created_at: string;
  updated_at: string;
};

export type SkillDetail = {
  metadata: SkillMetadata;
  skill: Skill;
};

export type DocumentMetadata = {
  doc_id: string;
  profile_id: string;
  original_filename: string;
  file_type: 'pdf' | 'docx' | 'txt';
  file_size_bytes: number;
  uploaded_at: string;
  extraction_method: string;
  word_count: number;
  character_count: number;
  status: string;
  extracted_text?: string;
};

export type ExtractedTextPreview = {
  doc_id: string;
  filename: string;
  preview: string;
  character_count: number;
  truncated: boolean;
};

export type UploadProgress = {
  stage: 'Uploading' | 'Extracting text' | 'Saving metadata' | 'Complete';
  percentage: number;
};

export type PrivacyMode = 'local_only' | 'hybrid' | 'cloud_allowed';

export type ProviderStatus = {
  name: string;
  available: boolean;
  configured: boolean;
  model?: string | null;
};

export type AppConfig = {
  providers: ProviderStatus[];
  privacy_mode: PrivacyMode;
  max_upload_size_mb: number;
  storage_path: string;
};

export type ProviderTestResult = {
  provider: string;
  connected: boolean;
  model?: string | null;
};

export type StyleRule = {
  rule_id: string;
  category: string;
  title: string;
  description: string;
  examples: {
    positive: string;
    negative: string;
  };
  source: 'document_derived';
  evidence: string[];
  source_snippets: string[];
  confidence: number;
};

export type ReviewRule = StyleRule | {
  rule_id: string;
  category: string;
  title: string;
  description: string;
  examples: {
    positive: string;
    negative: string;
  };
  source: 'user_authored';
  evidence: null;
  source_snippets: string[];
  confidence: number;
};

export type StyleAnalysis = {
  analysis_id: string;
  status: string;
  progress: number;
  skill_name: string;
  provider: string;
  privacy_mode: PrivacyMode;
  document_ids: string[];
  rules: StyleRule[];
};

export type RuleReviewSummary = {
  analysis_id: string;
  approved_count: number;
  rejected_count: number;
  edited_count: number;
  custom_count: number;
  ready_for_skill_creation: boolean;
  skill_id?: string;
  lifecycle_status?: SkillLifecycleStatus;
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function parseEnvelope<T>(response: Response, fallbackMessage: string): Promise<ApiEnvelope<T>> {
  if (!response.ok) {
    let message = fallbackMessage;
    try {
      const error = (await response.json()) as ApiErrorEnvelope;
      message = error.message || fallbackMessage;
    } catch {
      // Keep the caller-facing fallback for non-JSON failures.
    }
    throw new Error(message);
  }
  return (await response.json()) as ApiEnvelope<T>;
}

export async function getStatus() {
  const response = await fetch(`${API_BASE_URL}/api/status`);
  return parseEnvelope<{
    database_type: 'file-based';
    privacy_mode: 'local_only' | 'hybrid' | 'cloud_allowed';
  }>(response, 'Unable to load API status');
}

export async function getConfig() {
  const response = await fetch(`${API_BASE_URL}/api/config`);
  return parseEnvelope<AppConfig>(response, 'Unable to load settings');
}

export async function updatePrivacyMode(privacyMode: PrivacyMode) {
  const response = await fetch(`${API_BASE_URL}/api/config/update-privacy-mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ privacy_mode: privacyMode }),
  });
  return parseEnvelope<AppConfig>(response, 'Unable to update privacy mode');
}

export async function testProvider(provider: string) {
  const response = await fetch(`${API_BASE_URL}/api/config/test-provider`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  });
  return parseEnvelope<ProviderTestResult>(response, 'Unable to test provider');
}

export async function startStyleAnalysis(profileId: string, payload: {
  document_ids: string[];
  skill_name: string;
  provider?: string;
}) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/analyze-style`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseEnvelope<StyleAnalysis>(response, 'Unable to start style analysis');
}

export async function getStyleAnalysis(profileId: string, analysisId: string) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/analyze-style/${analysisId}`);
  return parseEnvelope<StyleAnalysis>(response, 'Unable to load style analysis');
}

export async function completeRuleReview(profileId: string, analysisId: string, payload: {
  approved_rules: ReviewRule[];
  rejected_rules: ReviewRule[];
  edited_rules: ReviewRule[];
  custom_rules: ReviewRule[];
}) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/analyses/${analysisId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseEnvelope<RuleReviewSummary>(response, 'Unable to complete rule review');
}

export async function listSkills(profileId: string) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/skills`);
  return parseEnvelope<SkillMetadata[]>(response, 'Unable to load skills');
}

export async function getSkill(profileId: string, skillId: string) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/skills/${skillId}`);
  return parseEnvelope<SkillDetail>(response, 'Unable to load skill');
}

export async function approveSkill(profileId: string, skillId: string) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/skills/${skillId}/approve`, {
    method: 'POST',
  });
  return parseEnvelope<SkillDetail>(response, 'Unable to approve skill');
}

export async function activateSkill(profileId: string, skillId: string) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/skills/${skillId}/activate`, {
    method: 'POST',
  });
  return parseEnvelope<SkillDetail>(response, 'Unable to activate skill');
}

export async function setDefaultSkill(profileId: string, skillId: string) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/skills/${skillId}/set-default`, {
    method: 'POST',
  });
  return parseEnvelope<SkillDetail>(response, 'Unable to set default skill');
}

export async function listProfiles() {
  const response = await fetch(`${API_BASE_URL}/api/profiles`);
  return parseEnvelope<Profile[]>(response, 'Unable to load profiles');
}

export async function createProfile(payload: {
  profile_id?: string;
  display_name: string;
  description?: string;
}) {
  const response = await fetch(`${API_BASE_URL}/api/profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseEnvelope<Profile>(response, 'Unable to create profile');
}

export async function getProfile(profileId: string) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}`);
  return parseEnvelope<Profile & { documents: DocumentMetadata[] }>(
    response,
    'Unable to load profile',
  );
}

export async function uploadDocument(
  profileId: string,
  file: File,
  onProgress?: (progress: UploadProgress) => void,
) {
  const body = new FormData();
  body.append('file', file);

  return new Promise<ApiEnvelope<DocumentMetadata>>((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open('POST', `${API_BASE_URL}/api/profiles/${profileId}/documents/upload`);

    request.upload.onprogress = (event) => {
      if (!event.lengthComputable) {
        return;
      }
      const uploadPercent = Math.min(45, Math.round((event.loaded / event.total) * 45));
      onProgress?.({ stage: 'Uploading', percentage: uploadPercent });
    };

    request.onload = () => {
      try {
        const bodyText = request.responseText || '{}';
        const parsed = JSON.parse(bodyText) as ApiEnvelope<DocumentMetadata> | ApiErrorEnvelope;
        if (request.status < 200 || request.status >= 300 || parsed.success === false) {
          reject(new Error((parsed as ApiErrorEnvelope).message || 'Unable to upload document'));
          return;
        }
        onProgress?.({ stage: 'Complete', percentage: 100 });
        resolve(parsed as ApiEnvelope<DocumentMetadata>);
      } catch {
        reject(new Error('Unable to upload document'));
      }
    };

    request.onerror = () => reject(new Error('Unable to upload document'));
    request.send(body);
  });
}

export async function previewDocument(profileId: string, docId: string) {
  const response = await fetch(`${API_BASE_URL}/api/profiles/${profileId}/documents/${docId}/preview`);
  return parseEnvelope<ExtractedTextPreview>(response, 'Unable to preview document');
}

export async function updateExtractedText(profileId: string, docId: string, extractedText: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/profiles/${profileId}/documents/${docId}/extracted-text`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ extracted_text: extractedText }),
    },
  );
  return parseEnvelope<DocumentMetadata>(response, 'Unable to update extracted text');
}
