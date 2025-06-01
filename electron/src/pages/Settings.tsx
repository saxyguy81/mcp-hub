import React, { useState, useEffect } from 'react';
import { WizardConfig } from './Wizard';

interface SettingsProps {
  onClose: () => void;
}

const Settings: React.FC<SettingsProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('llm');
  const [config, setConfig] = useState<WizardConfig>({
    gitRemote: '', registry: 'offline', secrets: 'env', llmBackend: 'claude',
    dependencies: { docker: true, git: true, python: true }, expeditedSetup: false
  });
  const [testResults, setTestResults] = useState<{[key: string]: any}>({});
  const [testing, setTesting] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<{[key: string]: string}>({});

  useEffect(() => { loadCurrentConfig(); }, []);

  const loadCurrentConfig = async () => {
    try {
      const currentConfig = await window.electronAPI?.getCurrentConfig();
      if (currentConfig) setConfig(currentConfig);
    } catch (error) { console.error('Failed to load config:', error); }
  };

  const validateConfig = (): boolean => {
    const newErrors: {[key: string]: string} = {};
    if (config.llmBackend === 'custom') {
      if (!config.customLLMUrl?.trim()) newErrors.customUrl = '🔗 URL required';
      else if (!isValidUrl(config.customLLMUrl)) newErrors.customUrl = '❌ Invalid URL';
    }
    if (!config.expeditedSetup && !config.gitRemote?.trim()) newErrors.gitRemote = '📚 Repository URL required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidUrl = (url: string): boolean => { try { new URL(url); return true; } catch { return false; } };

  const saveConfig = async () => {
    if (!validateConfig()) return;
    setSaving(true);
    try {
      await window.electronAPI?.saveConfig(config);
      alert('✅ Configuration saved!');
    } catch (error) { alert('❌ Failed to save configuration'); }
    setSaving(false);
  };

  const testLLMConnection = async () => {
    setTesting(true);
    setErrors({});
    try {
      const result = await window.electronAPI?.testLLM(config);
      setTestResults({ ...testResults, llm: { 
        success: result.success, duration: result.duration, status: result.status 
      }});
      if (!result.success) {
        setErrors({ llm: `❌ ${result.message || 'Connection test failed'}` });
      }
    } catch (error) {
      setTestResults({ ...testResults, llm: { success: false, error: error.message }});
      setErrors({ llm: '❌ Failed to test connection. Please check your settings.' });
    }
    setTesting(false);
  };

  const regenerateBridge = async () => {
    setRegenerating(true);
    try {
      await window.electronAPI?.regenerateBridge();
      alert('✅ OpenAPI bridge regenerated successfully!');
    } catch (error) {
      console.error('Failed to regenerate bridge:', error);
      alert('❌ Failed to regenerate bridge schema');
    }
    setRegenerating(false);
  };

  const tabStyle = (isActive: boolean) => ({
    padding: '12px 24px', border: 'none',
    backgroundColor: isActive ? '#3182ce' : '#e2e8f0',
    color: isActive ? 'white' : '#4a5568',
    cursor: 'pointer', borderRadius: '6px 6px 0 0',
    fontWeight: isActive ? 'bold' : 'normal',
    fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px'
  });

  return (
    <div style={{ 
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', 
      alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div style={{ 
        backgroundColor: 'white', borderRadius: '12px', width: '85%', 
        maxWidth: '900px', height: '85%', display: 'flex', flexDirection: 'column'
      }}>
        <div style={{ 
          padding: '25px', borderBottom: '1px solid #e2e8f0', 
          display: 'flex', justifyContent: 'space-between', alignItems: 'center' 
        }}>
          <h2 style={{ color: '#1a365d', margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
            ⚙️ MCP Hub Settings
          </h2>
          <button 
            onClick={onClose}
            style={{ 
              background: 'none', border: 'none', fontSize: '28px', 
              cursor: 'pointer', color: '#a0aec0', padding: '5px'
            }}
          >
            ×
          </button>
        </div>

        <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', padding: '0 25px' }}>
          <button 
            style={tabStyle(activeTab === 'llm')}
            onClick={() => setActiveTab('llm')}
          >
            🤖 AI Assistant
          </button>
          <button 
            style={tabStyle(activeTab === 'general')}
            onClick={() => setActiveTab('general')}
          >
            📚 Repository
          </button>
          <button 
            style={tabStyle(activeTab === 'advanced')}
            onClick={() => setActiveTab('advanced')}
          >
            🛠️ Advanced
          </button>
        </div>

        <div style={{ flex: 1, padding: '25px', overflow: 'auto' }}>
          {activeTab === 'llm' && (
            <div>
              <h3 style={{ color: '#2d3748', marginBottom: '20px', fontSize: '20px' }}>
                🤖 AI Assistant Configuration
              </h3>
              <p style={{ color: '#4a5568', marginBottom: '25px', fontSize: '14px' }}>
                Manage your AI service connection and test its functionality.
              </p>
              
              <div style={{ marginBottom: '30px' }}>
                <h4 style={{ marginBottom: '15px', fontSize: '16px', color: '#2d3748' }}>
                  🔌 Language Model Backend
                </h4>
                
                <label style={{ 
                  display: 'flex', alignItems: 'center', marginBottom: '15px', cursor: 'pointer',
                  padding: '15px', border: '2px solid ' + (config.llmBackend === 'claude' ? '#3182ce' : '#e2e8f0'),
                  borderRadius: '8px', backgroundColor: config.llmBackend === 'claude' ? '#ebf8ff' : 'transparent'
                }}>
                  <input
                    type="radio" name="llmBackend" value="claude"
                    checked={config.llmBackend === 'claude'}
                    onChange={(e) => setConfig({ ...config, llmBackend: e.target.value as any })}
                    style={{ marginRight: '15px', transform: 'scale(1.2)' }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                      <span style={{ fontSize: '18px' }}>🔵</span>
                      <strong>Claude Desktop</strong>
                      <span style={{ 
                        background: '#38a169', color: 'white', padding: '2px 6px', 
                        borderRadius: '10px', fontSize: '10px', fontWeight: 'bold'
                      }}>FREE</span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#718096', marginLeft: '26px' }}>
                      Fast, private, works offline. Uses Claude app on your computer.
                    </div>
                  </div>
                </label>

                <label style={{ 
                  display: 'flex', alignItems: 'center', marginBottom: '15px', cursor: 'pointer',
                  padding: '15px', border: '2px solid ' + (config.llmBackend === 'openai' ? '#3182ce' : '#e2e8f0'),
                  borderRadius: '8px', backgroundColor: config.llmBackend === 'openai' ? '#ebf8ff' : 'transparent'
                }}>
                  <input
                    type="radio" name="llmBackend" value="openai"
                    checked={config.llmBackend === 'openai'}
                    onChange={(e) => setConfig({ ...config, llmBackend: e.target.value as any })}
                    style={{ marginRight: '15px', transform: 'scale(1.2)' }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                      <span style={{ fontSize: '18px' }}>🟢</span>
                      <strong>OpenAI ChatGPT</strong>
                      <span style={{ 
                        background: '#f56565', color: 'white', padding: '2px 6px', 
                        borderRadius: '10px', fontSize: '10px', fontWeight: 'bold'
                      }}>PAID</span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#718096', marginLeft: '26px' }}>
                      Cloud-based AI service. Requires API key and usage credits.
                    </div>
                  </div>
                </label>

                <label style={{ 
                  display: 'flex', alignItems: 'center', marginBottom: '15px', cursor: 'pointer',
                  padding: '15px', border: '2px solid ' + (config.llmBackend === 'custom' ? '#3182ce' : '#e2e8f0'),
                  borderRadius: '8px', backgroundColor: config.llmBackend === 'custom' ? '#ebf8ff' : 'transparent'
                }}>
                  <input
                    type="radio" name="llmBackend" value="custom"
                    checked={config.llmBackend === 'custom'}
                    onChange={(e) => setConfig({ ...config, llmBackend: e.target.value as any })}
                    style={{ marginRight: '15px', transform: 'scale(1.2)' }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                      <span style={{ fontSize: '18px' }}>⚙️</span>
                      <strong>Custom AI Service</strong>
                      <span style={{ 
                        background: '#805ad5', color: 'white', padding: '2px 6px', 
                        borderRadius: '10px', fontSize: '10px', fontWeight: 'bold'
                      }}>ADVANCED</span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#718096', marginLeft: '26px' }}>
                      Connect to your own AI service or alternative provider.
                    </div>
                  </div>
                </label>

                {config.llmBackend === 'custom' && (
                  <div style={{ 
                    background: '#f7fafc', padding: '20px', borderRadius: '8px', 
                    marginTop: '15px', border: '1px solid #e2e8f0'
                  }}>
                    <h5 style={{ color: '#2d3748', marginBottom: '15px', fontSize: '14px' }}>
                      🔧 Custom Service Configuration
                    </h5>
                    <div style={{ marginBottom: '15px' }}>
                      <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', fontSize: '13px' }}>
                        🔗 Service URL:
                      </label>
                      <input
                        type="text" placeholder="https://api.your-service.com/v1"
                        value={config.customLLMUrl || ''}
                        onChange={(e) => setConfig({ ...config, customLLMUrl: e.target.value })}
                        style={{
                          width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0',
                          borderRadius: '6px', fontSize: '14px'
                        }}
                      />
                      {errors.customUrl && (
                        <div style={{ color: '#e53e3e', fontSize: '12px', marginTop: '5px' }}>
                          {errors.customUrl}
                        </div>
                      )}
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', fontSize: '13px' }}>
                        🔑 API Key (Optional):
                      </label>
                      <input
                        type="password" placeholder="sk-your-api-key-here"
                        value={config.customLLMToken || ''}
                        onChange={(e) => setConfig({ ...config, customLLMToken: e.target.value })}
                        style={{
                          width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0',
                          borderRadius: '6px', fontSize: '14px'
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div style={{ marginBottom: '30px' }}>
                <h4 style={{ marginBottom: '15px', fontSize: '16px', color: '#2d3748' }}>
                  🧪 Connection Testing
                </h4>
                <p style={{ fontSize: '13px', color: '#4a5568', marginBottom: '15px' }}>
                  Test your AI assistant connection to make sure everything is working properly.
                </p>
                <button
                  onClick={testLLMConnection} disabled={testing}
                  style={{
                    padding: '12px 20px', backgroundColor: '#38a169', color: 'white',
                    border: 'none', borderRadius: '6px', cursor: 'pointer',
                    marginRight: '15px', fontSize: '14px', fontWeight: 'bold',
                    opacity: testing ? 0.7 : 1, display: 'flex', alignItems: 'center', gap: '8px'
                  }}
                >
                  {testing ? '🔄 Testing...' : '🔗 Test Connection'}
                </button>
                
                {testResults.llm && (
                  <div style={{ 
                    marginTop: '15px', padding: '15px', borderRadius: '8px',
                    backgroundColor: testResults.llm.success ? '#f0fff4' : '#fed7d7',
                    border: `1px solid ${testResults.llm.success ? '#9ae6b4' : '#feb2b2'}`
                  }}>
                    <div style={{ 
                      color: testResults.llm.success ? '#38a169' : '#e53e3e',
                      fontWeight: 'bold', fontSize: '14px', marginBottom: '5px'
                    }}>
                      {testResults.llm.success ? '✅ Connection Successful!' : '❌ Connection Failed'}
                    </div>
                    {testResults.llm.duration && (
                      <div style={{ fontSize: '13px', color: '#4a5568' }}>
                        ⚡ Response time: {testResults.llm.duration}ms
                      </div>
                    )}
                    {testResults.llm.error && (
                      <div style={{ fontSize: '13px', color: '#e53e3e' }}>
                        🔍 Error: {testResults.llm.error}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div>
                <h4 style={{ marginBottom: '15px', fontSize: '16px', color: '#2d3748' }}>
                  🔄 OpenAPI Bridge Management
                </h4>
                <p style={{ fontSize: '13px', color: '#4a5568', marginBottom: '15px' }}>
                  Regenerate the connection bridge when you change AI providers or need to refresh the configuration.
                </p>
                <button
                  onClick={regenerateBridge} disabled={regenerating}
                  style={{
                    padding: '12px 20px', backgroundColor: '#3182ce', color: 'white',
                    border: 'none', borderRadius: '6px', cursor: 'pointer',
                    opacity: regenerating ? 0.7 : 1, fontSize: '14px', fontWeight: 'bold',
                    display: 'flex', alignItems: 'center', gap: '8px'
                  }}
                >
                  {regenerating ? '🔄 Regenerating...' : '🔧 Regenerate Bridge'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'general' && (
            <div>
              <h3 style={{ color: '#2d3748', marginBottom: '20px', fontSize: '20px' }}>
                📚 MCP Server Repository
              </h3>
              <p style={{ color: '#4a5568', marginBottom: '25px', fontSize: '14px' }}>
                Configure where MCP Hub downloads AI tools and servers from.
              </p>

              <div style={{ marginBottom: '25px' }}>
                <div style={{ 
                  background: '#ebf8ff', border: '2px solid #3182ce', 
                  padding: '20px', borderRadius: '12px', marginBottom: '20px'
                }}>
                  <h4 style={{ 
                    color: '#2b6cb0', marginBottom: '10px', fontSize: '16px',
                    display: 'flex', alignItems: 'center', gap: '8px'
                  }}>
                    🚀 Quick Start Mode
                  </h4>
                  <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '10px' }}>
                    <input
                      type="checkbox"
                      checked={config.expeditedSetup || false}
                      onChange={(e) => setConfig({ ...config, expeditedSetup: e.target.checked })}
                      style={{ marginRight: '10px', transform: 'scale(1.2)' }}
                    />
                    <span style={{ color: '#2b6cb0', fontSize: '14px', fontWeight: 'bold' }}>
                      Use official MCP Hub registry (Recommended)
                    </span>
                  </label>
                  <p style={{ color: '#2b6cb0', fontSize: '12px', marginLeft: '28px' }}>
                    ✨ Automatically uses our curated collection of tested MCP servers. Perfect for beginners!
                  </p>
                </div>

                {!config.expeditedSetup && (
                  <div>
                    <h4 style={{ marginBottom: '15px', color: '#2d3748', fontSize: '16px' }}>
                      🔧 Custom Repository (Advanced Users)
                    </h4>
                    <div style={{ marginBottom: '20px' }}>
                      <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', fontSize: '13px' }}>
                        📂 Git Repository URL:
                      </label>
                      <input 
                        type="text" 
                        value={config.gitRemote}
                        placeholder="https://github.com/your-username/mcp-servers"
                        onChange={(e) => setConfig({...config, gitRemote: e.target.value})}
                        style={{ 
                          width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0', 
                          borderRadius: '6px', fontSize: '14px'
                        }}
                      />
                      {errors.gitRemote && (
                        <div style={{ color: '#e53e3e', fontSize: '12px', marginTop: '5px' }}>
                          {errors.gitRemote}
                        </div>
                      )}
                      <div style={{ fontSize: '12px', color: '#718096', marginTop: '5px' }}>
                        💡 This should be a GitHub repository containing MCP server definitions
                      </div>
                    </div>

                    <div style={{ marginBottom: '20px' }}>
                      <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', fontSize: '13px' }}>
                        🏪 Registry Type:
                      </label>
                      <select 
                        value={config.registry}
                        onChange={(e) => setConfig({...config, registry: e.target.value})}
                        style={{ 
                          width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0', 
                          borderRadius: '6px', fontSize: '14px'
                        }}
                      >
                        <option value="offline">📦 Offline (Local containers only)</option>
                        <option value="ghcr">🐙 GitHub Container Registry</option>
                        <option value="gitlab">🦊 GitLab Container Registry</option>
                      </select>
                    </div>

                    <div style={{ marginBottom: '20px' }}>
                      <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', fontSize: '13px' }}>
                        🔐 Secrets Management:
                      </label>
                      <select 
                        value={config.secrets}
                        onChange={(e) => setConfig({...config, secrets: e.target.value})}
                        style={{ 
                          width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0', 
                          borderRadius: '6px', fontSize: '14px'
                        }}
                      >
                        <option value="env">🌍 Environment Variables (Simple)</option>
                        <option value="lastpass">🔒 LastPass (Team Sharing)</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'advanced' && (
            <div>
              <h3 style={{ color: '#2d3748', marginBottom: '20px', fontSize: '20px' }}>
                🛠️ Advanced Settings
              </h3>
              <p style={{ color: '#4a5568', marginBottom: '25px', fontSize: '14px' }}>
                Advanced configuration options for power users and debugging.
              </p>
              
              <div style={{ marginBottom: '25px' }}>
                <h4 style={{ marginBottom: '15px', fontSize: '16px', color: '#2d3748' }}>
                  🐳 Container Engine Status
                </h4>
                <div style={{ 
                  background: '#f7fafc', padding: '15px', borderRadius: '8px',
                  border: '1px solid #e2e8f0'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                    <span style={{ fontSize: '18px' }}>
                      {config.dependencies.docker ? '✅' : '❌'}
                    </span>
                    <div>
                      <strong>Docker Engine:</strong> {config.dependencies.docker ? 'Running ✨' : 'Not detected'}
                      <div style={{ fontSize: '12px', color: '#718096' }}>
                        Manages containerized MCP servers
                      </div>
                    </div>
                  </div>
                  <button
                    style={{
                      padding: '8px 16px', backgroundColor: '#e2e8f0', color: '#4a5568',
                      border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px'
                    }}
                    onClick={() => alert('🔄 Checking engine status...')}
                  >
                    🔍 Check Engine Status
                  </button>
                </div>
              </div>

              <div style={{ marginBottom: '25px' }}>
                <h4 style={{ marginBottom: '15px', fontSize: '16px', color: '#2d3748' }}>
                  🐛 Debug Options
                </h4>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '10px' }}>
                  <input
                    type="checkbox"
                    style={{ marginRight: '10px', transform: 'scale(1.2)' }}
                  />
                  <div>
                    <span style={{ fontSize: '14px', fontWeight: 'bold' }}>Enable debug logging</span>
                    <div style={{ fontSize: '12px', color: '#718096' }}>
                      Show detailed logs for troubleshooting issues
                    </div>
                  </div>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', marginBottom: '10px' }}>
                  <input
                    type="checkbox"
                    style={{ marginRight: '10px', transform: 'scale(1.2)' }}
                  />
                  <div>
                    <span style={{ fontSize: '14px', fontWeight: 'bold' }}>Auto-start with system</span>
                    <div style={{ fontSize: '12px', color: '#718096' }}>
                      Launch MCP Hub automatically when you start your computer
                    </div>
                  </div>
                </label>
              </div>
            </div>
          )}
        </div>

        <div style={{ 
          padding: '20px', borderTop: '1px solid #e2e8f0', 
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          backgroundColor: '#f7fafc'
        }}>
          <div style={{ fontSize: '13px', color: '#4a5568' }}>
            💡 Changes will take effect after saving and restarting MCP Hub
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              onClick={onClose}
              style={{ 
                padding: '10px 20px', border: '1px solid #e2e8f0', 
                backgroundColor: 'white', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Cancel
            </button>
            <button 
              onClick={saveConfig}
              disabled={saving}
              style={{ 
                padding: '10px 20px', backgroundColor: saving ? '#a0aec0' : '#3182ce', 
                color: 'white', border: 'none', borderRadius: '6px', 
                cursor: 'pointer', fontSize: '14px', fontWeight: 'bold',
                opacity: saving ? 0.7 : 1, display: 'flex', alignItems: 'center', gap: '8px'
              }}
            >
              {saving ? '💾 Saving...' : '💾 Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
