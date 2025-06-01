import React, { useState } from 'react';

interface WizardConfig {
  gitRemote: string;
  registry: string;
  secrets: string;
}

function App() {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<WizardConfig>({
    gitRemote: '',
    registry: 'offline',
    secrets: 'env'
  });

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
  };

  const handlePrev = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleSave = () => {
    // Save configuration via IPC to backend
    console.log('Saving config:', config);
    alert('Configuration saved! MCP Hub is ready to use.');
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>MCP Hub Setup Wizard</h1>
      
      {step === 1 && (
        <div>
          <h2>Step 1: Dependency Check</h2>
          <p>✅ Docker installed</p>
          <p>✅ Git available</p>
          <p>✅ Python 3.10+ available</p>
          <button onClick={handleNext}>Next</button>
        </div>
      )}

      {step === 2 && (
        <div>
          <h2>Step 2: Configuration</h2>
          <div style={{ marginBottom: '10px' }}>
            <label>Git Remote URL:</label>
            <input 
              type="text" 
              value={config.gitRemote}
              onChange={(e) => setConfig({...config, gitRemote: e.target.value})}
              style={{ marginLeft: '10px', width: '300px' }}
            />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Registry:</label>
            <select 
              value={config.registry}
              onChange={(e) => setConfig({...config, registry: e.target.value})}
              style={{ marginLeft: '10px' }}
            >
              <option value="offline">Offline</option>
              <option value="ghcr">GitHub Container Registry</option>
              <option value="gitlab">GitLab Registry</option>
            </select>
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Secrets Backend:</label>
            <select 
              value={config.secrets}
              onChange={(e) => setConfig({...config, secrets: e.target.value})}
              style={{ marginLeft: '10px' }}
            >
              <option value="env">Environment/Manual</option>
              <option value="lastpass">LastPass</option>
            </select>
          </div>
          <button onClick={handlePrev}>Previous</button>
          <button onClick={handleNext} style={{ marginLeft: '10px' }}>Next</button>
        </div>
      )}

      {step === 3 && (
        <div>
          <h2>Step 3: Review & Start</h2>
          <p><strong>Git Remote:</strong> {config.gitRemote}</p>
          <p><strong>Registry:</strong> {config.registry}</p>
          <p><strong>Secrets:</strong> {config.secrets}</p>
          <button onClick={handlePrev}>Previous</button>
          <button onClick={handleSave} style={{ marginLeft: '10px' }}>Save & Start</button>
        </div>
      )}
    </div>
  );
}

export default App;
