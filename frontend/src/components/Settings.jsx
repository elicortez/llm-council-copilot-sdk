import { useState, useEffect } from 'react';
import { api } from '../api';
import './Settings.css';

export default function Settings({ isOpen, onClose, onSave }) {
  const [models, setModels] = useState([]);
  const [councilModels, setCouncilModels] = useState([]);
  const [chairmanModel, setChairmanModel] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [modelsResponse, settingsResponse] = await Promise.all([
        api.fetchModels(),
        api.getSettings(),
      ]);
      setModels(modelsResponse.models || []);
      setCouncilModels(settingsResponse.council_models || []);
      setChairmanModel(settingsResponse.chairman_model || '');
    } catch (err) {
      setError('Failed to load settings: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCouncilModelToggle = (modelId) => {
    setCouncilModels((prev) => {
      if (prev.includes(modelId)) {
        return prev.filter((id) => id !== modelId);
      } else {
        return [...prev, modelId];
      }
    });
  };

  const handleSave = async () => {
    if (councilModels.length === 0) {
      setError('Please select at least one council model');
      return;
    }
    if (!chairmanModel) {
      setError('Please select a chairman model');
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await api.saveSettings({
        council_models: councilModels,
        chairman_model: chairmanModel,
      });
      onSave && onSave({ council_models: councilModels, chairman_model: chairmanModel });
      onClose();
    } catch (err) {
      setError('Failed to save settings: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Council Settings</h2>
          <button className="settings-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="settings-content">
          {isLoading ? (
            <div className="settings-loading">Loading models...</div>
          ) : error ? (
            <div className="settings-error">{error}</div>
          ) : (
            <>
              <div className="settings-section">
                <h3>Council Members</h3>
                <p className="settings-description">
                  Select the models that will participate in Stage 1 (answering) and Stage 2 (peer review).
                </p>
                <div className="model-list">
                  {models.length === 0 ? (
                    <div className="no-models">No models available. Is the Copilot CLI authenticated?</div>
                  ) : (
                    models.map((model) => (
                      <label key={model.id} className="model-item">
                        <input
                          type="checkbox"
                          checked={councilModels.includes(model.id)}
                          onChange={() => handleCouncilModelToggle(model.id)}
                        />
                        <span className="model-name">{model.name || model.id}</span>
                        <span className="model-id">{model.id}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div className="settings-section">
                <h3>Chairman</h3>
                <p className="settings-description">
                  Select the model that will synthesize the final response in Stage 3.
                </p>
                <select
                  className="chairman-select"
                  value={chairmanModel}
                  onChange={(e) => setChairmanModel(e.target.value)}
                >
                  <option value="">Select a chairman...</option>
                  {models.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name || model.id}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}
        </div>

        <div className="settings-footer">
          <button className="settings-btn cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            className="settings-btn save"
            onClick={handleSave}
            disabled={isLoading || isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
