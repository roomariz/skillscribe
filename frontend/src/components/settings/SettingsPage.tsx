import { useEffect, useState } from 'react';
import {
  type AppConfig,
  type PrivacyMode,
  type ProviderTestResult,
  getConfig,
  testProvider,
  updatePrivacyMode,
} from '../../api/client';

const PRIVACY_OPTIONS: Array<{ value: PrivacyMode; label: string }> = [
  { value: 'local_only', label: 'Local Only' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'cloud_allowed', label: 'Cloud Allowed' },
];

export function SettingsPage() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [testResults, setTestResults] = useState<Record<string, ProviderTestResult>>({});
  const [busyProvider, setBusyProvider] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    void loadConfig();
  }, []);

  async function loadConfig() {
    try {
      const response = await getConfig();
      setConfig(response.data);
      setMessage('');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to load settings');
    }
  }

  async function handleModeChange(privacyMode: PrivacyMode) {
    try {
      const response = await updatePrivacyMode(privacyMode);
      setConfig(response.data);
      setMessage('Privacy mode updated.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to update privacy mode');
    }
  }

  async function handleProviderTest(provider: string) {
    setBusyProvider(provider);
    try {
      const response = await testProvider(provider);
      setTestResults((current) => ({ ...current, [provider]: response.data }));
      setMessage(`${provider} connection ${response.data.connected ? 'passed' : 'failed'}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to test provider');
    } finally {
      setBusyProvider(null);
    }
  }

  return (
    <section className="settings-page" aria-labelledby="settings-title">
      <div className="settings-header">
        <div>
          <h2 id="settings-title">Settings</h2>
          <p>Privacy routing and provider status</p>
        </div>
        {config ? <span>{config.storage_path}</span> : null}
      </div>

      <div className="settings-grid">
        <fieldset className="privacy-selector">
          <legend>Privacy Mode</legend>
          {PRIVACY_OPTIONS.map((option) => (
            <label key={option.value}>
              <input
                checked={config?.privacy_mode === option.value}
                disabled={!config}
                name="privacy-mode"
                onChange={() => void handleModeChange(option.value)}
                type="radio"
              />
              <span>{option.label}</span>
            </label>
          ))}
        </fieldset>

        <div className="provider-status-list">
          <div className="section-heading">
            <h3>Providers</h3>
            <span>{config?.providers.length ?? 0}</span>
          </div>
          {config?.providers.map((provider) => {
            const result = testResults[provider.name];
            return (
              <div className="provider-row" key={provider.name}>
                <div>
                  <strong>{provider.name}</strong>
                  <span>
                    {provider.configured ? 'configured' : 'not configured'} |{' '}
                    {provider.available ? 'available' : 'unavailable'}
                  </span>
                  {result ? (
                    <span>{result.connected ? result.model ?? 'connected' : 'connection failed'}</span>
                  ) : null}
                </div>
                <button
                  disabled={busyProvider === provider.name}
                  onClick={() => void handleProviderTest(provider.name)}
                  type="button"
                >
                  Test Connection
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {message ? <p className="settings-message">{message}</p> : null}
    </section>
  );
}
