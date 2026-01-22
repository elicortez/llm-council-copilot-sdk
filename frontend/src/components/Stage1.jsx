import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage1.css';

export default function Stage1({ responses }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!responses || responses.length === 0) {
    return null;
  }

  // Separate successful and failed responses
  const failedResponses = responses.filter((r) => r.error);
  const successfulResponses = responses.filter((r) => !r.error && r.response);

  return (
    <div className="stage stage1">
      <h3 className="stage-title">Stage 1: Individual Responses</h3>

      {failedResponses.length > 0 && (
        <div className="stage-warnings">
          {failedResponses.map((resp, index) => (
            <div key={index} className="warning-banner">
              ⚠️ <strong>{resp.model}</strong> failed: {resp.error}
            </div>
          ))}
        </div>
      )}

      {successfulResponses.length === 0 ? (
        <div className="no-responses">All models failed to respond.</div>
      ) : (
        <>
          <div className="tabs">
            {successfulResponses.map((resp, index) => (
              <button
                key={index}
                className={`tab ${activeTab === index ? 'active' : ''}`}
                onClick={() => setActiveTab(index)}
              >
                {resp.model.split('/')[1] || resp.model}
              </button>
            ))}
          </div>

          <div className="tab-content">
            <div className="model-name">{successfulResponses[activeTab].model}</div>
            <div className="response-text markdown-content">
              <ReactMarkdown>{successfulResponses[activeTab].response}</ReactMarkdown>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
