import React, { useState } from 'react';

interface WizardProps {
  onComplete: (config: WizardConfig) => void;
}

export interface WizardConfig {
  gitRemote: string; registry: string; secrets: string;
  llmBackend: 'claude' | 'openai' | 'custom';
  customLLMUrl?: string; customLLMToken?: string;
  dependencies: { docker: boolean; git: boolean; python: boolean; };
  expeditedSetup?: boolean;
}

const Wizard: React.FC<WizardProps> = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<WizardConfig>({
    gitRemote: '', registry: 'offline', secrets: 'env', llmBackend: 'claude',
    expeditedSetup: false, dependencies: { docker: false, git: false, python: false }
  });
  const [testResults, setTestResults] = useState<{[key: string]: boolean}>({});
  const [testing, setTesting] = useState(false);
  const [errors, setErrors] = useState<{[key: string]: string}>({});

  const isValidUrl = (url: string): boolean => {
    try { new URL(url); return true; } catch { return false; }
  };

  const validateStep = (stepNumber: number): boolean => {
    const newErrors: {[key: string]: string} = {};
    if (stepNumber === 1) {
      if (!config.dependencies.docker) newErrors.docker = '🐳 Docker required';
      if (!config.dependencies.git) newErrors.git = '📂 Git required';
    } else if (stepNumber === 2 && config.llmBackend === 'custom') {
      if (!config.customLLMUrl?.trim()) newErrors.customUrl = '🔗 URL required';
      else if (!isValidUrl(config.customLLMUrl)) newErrors.customUrl = '❌ Invalid URL';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const handleNext = () => { if (validateStep(step) && step < 5) setStep(step + 1); };
  const handlePrev = () => { if (step > 1) { setErrors({}); setStep(step - 1); } };
  const handleComplete = () => { if (validateStep(4)) onComplete(config); };
  const handleQuickStart = () => {
    setConfig({...config, expeditedSetup: true, 
      gitRemote: 'https://github.com/modelcontextprotocol/mcp-hub-registry',
      registry: 'ghcr', secrets: 'env'});
    setErrors({});
  };

  const testLLMConnection = async () => {
    setTesting(true);
    setErrors({});
    try {
      const result = await window.electronAPI?.testLLM(config);
      setTestResults({ ...testResults, llm: result.success });
      if (!result.success) {
        setErrors({ llm: `❌ ${result.message || 'Connection test failed'}` });
      }
    } catch (error) {
      setTestResults({ ...testResults, llm: false });
      setErrors({ llm: '❌ Failed to test connection. Please check your settings.' });
    }
    setTesting(false);
  };

  const checkDependencies = async () => {
    try {
      const deps = await window.electronAPI?.checkDependencies();
      setConfig({
        ...config,
        dependencies: deps || { docker: false, git: false, python: false }
      });
    } catch (error) {
      console.error('Failed to check dependencies:', error);
    }
  };

  React.useEffect(() => {
    if (step === 1) {
      checkDependencies();
    }
  }, [step]);

  const stepTitles = [
    '🔧 System Check',
    '🤖 AI Assistant', 
    '📚 Repository Setup',
    '📋 Review & Test',
    '🎉 All Done!'
  ];

  return (
    <div style={{ 
      padding: '40px', fontFamily: 'system-ui', maxWidth: '700px', 
      margin: '0 auto', backgroundColor: '#f8fafc', minHeight: '100vh'
    }}>
      <div style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 style={{ 
          color: '#1a365d', marginBottom: '10px', fontSize: '28px', fontWeight: 'bold'
        }}>
          Welcome to MCP Hub! 👋
        </h1>
        <p style={{ 
          color: '#4a5568', fontSize: '16px', marginBottom: '30px'
        }}>
          Let's set up your AI-powered tools in just a few easy steps
        </p>

        <div style={{ 
          display: 'flex', justifyContent: 'center', gap: '15px', 
          marginBottom: '30px', fontSize: '12px'
        }}>
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} style={{ 
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              opacity: i === step ? 1 : i < step ? 0.8 : 0.4
            }}>
              <div style={{
                width: '50px', height: '50px', borderRadius: '50%',
                backgroundColor: i === step ? '#3182ce' : i < step ? '#38a169' : '#e2e8f0',
                color: i === step || i < step ? 'white' : '#a0aec0',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 'bold', fontSize: '18px', marginBottom: '8px'
              }}>
                {i < step ? '✓' : i}
              </div>
              <span style={{ 
                fontSize: '11px', color: i === step ? '#3182ce' : '#718096',
                fontWeight: i === step ? 'bold' : 'normal', textAlign: 'center',
                maxWidth: '70px', lineHeight: '1.2'
              }}>
                {stepTitles[i - 1]}
              </span>
            </div>
          ))}
        </div>
      </div>

      {step === 1 && (
        <div style={{ 
          backgroundColor: 'white', padding: '30px', borderRadius: '12px', 
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)', marginBottom: '30px'
        }}>
          <h2 style={{ 
            color: '#2d3748', marginBottom: '15px', fontSize: '22px',
            display: 'flex', alignItems: 'center', gap: '10px'
          }}>
            🔧 System Requirements Check
          </h2>
          <p style={{ color: '#4a5568', marginBottom: '25px', fontSize: '14px' }}>
            We're checking if you have the necessary tools installed. Don't worry - we can help you install anything that's missing!
          </p>

          <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
            <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '20px' }}>
                {config.dependencies.docker ? '✅' : '❌'}
              </span>
              <div>
                <strong>Docker:</strong> {config.dependencies.docker ? 'Installed ✨' : 'Not found'}
                <div style={{ fontSize: '12px', color: '#718096' }}>
                  Runs your MCP servers in secure containers
                </div>
              </div>
            </div>
            <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '20px' }}>
                {config.dependencies.git ? '✅' : '❌'}
              </span>
              <div>
                <strong>Git:</strong> {config.dependencies.git ? 'Installed ✨' : 'Not found'}
                <div style={{ fontSize: '12px', color: '#718096' }}>
                  Downloads MCP servers from repositories
                </div>
              </div>
            </div>
            <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '20px' }}>
                {config.dependencies.python ? '✅' : '⚠️'}
              </span>
              <div>
                <strong>Python 3.10+:</strong> {config.dependencies.python ? 'Installed ✨' : 'Not found'}
                <div style={{ fontSize: '12px', color: '#718096' }}>
                  Optional: Needed for some advanced features
                </div>
              </div>
            </div>
          </div>

          {Object.keys(errors).length > 0 && (
            <div style={{ 
              background: '#fed7d7', border: '1px solid #feb2b2', 
              padding: '15px', borderRadius: '8px', marginBottom: '20px'
            }}>
              <h4 style={{ color: '#e53e3e', marginBottom: '10px', fontSize: '14px' }}>
                ⚠️ Required Items Missing:
              </h4>
              {Object.entries(errors).map(([key, message]) => (
                <div key={key} style={{ color: '#c53030', fontSize: '13px', marginBottom: '5px' }}>
                  • {message}
                </div>
              ))}
              <p style={{ color: '#c53030', fontSize: '12px', marginTop: '10px' }}>
                💡 Tip: Click "Install Missing Tools" to automatically install them for you!
              </p>
            </div>
          )}

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {(!config.dependencies.docker || !config.dependencies.git) && (
              <button 
                style={{
                  padding: '12px 20px', backgroundColor: '#3182ce', color: 'white',
                  border: 'none', borderRadius: '6px', cursor: 'pointer',
                  fontSize: '14px', fontWeight: 'bold',
                  display: 'flex', alignItems: 'center', gap: '8px'
                }}
                onClick={() => {
                  // This would trigger dependency installation
                  alert('Feature coming soon! Please install Docker and Git manually for now.');
                }}
              >
                🛠️ Install Missing Tools
              </button>
            )}
            
            <button 
              onClick={checkDependencies}
              style={{
                padding: '12px 20px', backgroundColor: '#38a169', color: 'white',
                border: 'none', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px', fontWeight: 'bold'
              }}
            >
              🔄 Re-check
            </button>
            
            <button 
              onClick={handleNext}
              disabled={!config.dependencies.docker || !config.dependencies.git}
              style={{
                padding: '12px 24px', 
                backgroundColor: (!config.dependencies.docker || !config.dependencies.git) ? '#e2e8f0' : '#3182ce',
                color: (!config.dependencies.docker || !config.dependencies.git) ? '#a0aec0' : 'white',
                border: 'none', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px', fontWeight: 'bold',
                opacity: (!config.dependencies.docker || !config.dependencies.git) ? 0.6 : 1
              }}
            >
              Next: Choose AI Assistant →
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div style={{ 
          backgroundColor: 'white', padding: '30px', borderRadius: '12px', 
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)', marginBottom: '30px'
        }}>
          <h2 style={{ 
            color: '#2d3748', marginBottom: '15px', fontSize: '22px',
            display: 'flex', alignItems: 'center', gap: '10px'
          }}>
            🤖 Choose Your AI Assistant
          </h2>
          <p style={{ color: '#4a5568', marginBottom: '25px', fontSize: '14px' }}>
            Select which AI service you'd like to use. This will power all the intelligent features in MCP Hub.
          </p>
          
          <div style={{ marginBottom: '25px' }}>
            <label style={{ 
              display: 'flex', alignItems: 'center', marginBottom: '15px', 
              cursor: 'pointer', padding: '15px', border: '2px solid ' + 
              (config.llmBackend === 'claude' ? '#3182ce' : '#e2e8f0'),
              borderRadius: '8px', backgroundColor: config.llmBackend === 'claude' ? '#ebf8ff' : 'transparent'
            }}>
              <input
                type="radio"
                name="llmBackend"
                value="claude"
                checked={config.llmBackend === 'claude'}
                onChange={(e) => setConfig({ ...config, llmBackend: e.target.value as any })}
                style={{ marginRight: '15px', transform: 'scale(1.2)' }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                  <span style={{ fontSize: '20px' }}>🔵</span>
                  <strong style={{ fontSize: '16px' }}>Claude Desktop (Recommended)</strong>
                  <span style={{ 
                    background: '#38a169', color: 'white', padding: '2px 8px', 
                    borderRadius: '12px', fontSize: '11px', fontWeight: 'bold'
                  }}>
                    FREE
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: '#718096', marginLeft: '28px' }}>
                  Use the Claude app running on your computer. Fast, private, and works offline.
                </div>
              </div>
            </label>

            <label style={{ 
              display: 'flex', alignItems: 'center', marginBottom: '15px', 
              cursor: 'pointer', padding: '15px', border: '2px solid ' + 
              (config.llmBackend === 'openai' ? '#3182ce' : '#e2e8f0'),
              borderRadius: '8px', backgroundColor: config.llmBackend === 'openai' ? '#ebf8ff' : 'transparent'
            }}>
              <input
                type="radio"
                name="llmBackend"
                value="openai"
                checked={config.llmBackend === 'openai'}
                onChange={(e) => setConfig({ ...config, llmBackend: e.target.value as any })}
                style={{ marginRight: '15px', transform: 'scale(1.2)' }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                  <span style={{ fontSize: '20px' }}>🟢</span>
                  <strong style={{ fontSize: '16px' }}>OpenAI ChatGPT</strong>
                  <span style={{ 
                    background: '#f56565', color: 'white', padding: '2px 8px', 
                    borderRadius: '12px', fontSize: '11px', fontWeight: 'bold'
                  }}>
                    PAID
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: '#718096', marginLeft: '28px' }}>
                  Use OpenAI's cloud service. Requires an API key and credits.
                </div>
              </div>
            </label>

            <label style={{ 
              display: 'flex', alignItems: 'center', marginBottom: '15px', 
              cursor: 'pointer', padding: '15px', border: '2px solid ' + 
              (config.llmBackend === 'custom' ? '#3182ce' : '#e2e8f0'),
              borderRadius: '8px', backgroundColor: config.llmBackend === 'custom' ? '#ebf8ff' : 'transparent'
            }}>
              <input
                type="radio"
                name="llmBackend"
                value="custom"
                checked={config.llmBackend === 'custom'}
                onChange={(e) => setConfig({ ...config, llmBackend: e.target.value as any })}
                style={{ marginRight: '15px', transform: 'scale(1.2)' }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                  <span style={{ fontSize: '20px' }}>⚙️</span>
                  <strong style={{ fontSize: '16px' }}>Custom AI Service</strong>
                  <span style={{ 
                    background: '#805ad5', color: 'white', padding: '2px 8px', 
                    borderRadius: '12px', fontSize: '11px', fontWeight: 'bold'
                  }}>
                    ADVANCED
                  </span>
                </div>
                <div style={{ fontSize: '13px', color: '#718096', marginLeft: '28px' }}>
                  Connect to your own AI service or alternative provider.
                </div>
              </div>
            </label>
          </div>

          {config.llmBackend === 'custom' && (
            <div style={{ 
              background: '#f7fafc', padding: '20px', borderRadius: '8px', 
              marginBottom: '20px', border: '1px solid #e2e8f0'
            }}>
              <h4 style={{ marginBottom: '15px', color: '#2d3748', fontSize: '14px' }}>
                🔧 Custom AI Service Configuration
              </h4>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', fontSize: '13px' }}>
                  🔗 Service URL:
                </label>
                <input
                  type="text"
                  placeholder="https://api.your-ai-service.com/v1"
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
                  type="password"
                  placeholder="sk-your-api-key-here"
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

          <div style={{ marginBottom: '20px' }}>
            <button
              onClick={testLLMConnection}
              disabled={testing}
              style={{
                padding: '12px 20px', backgroundColor: '#38a169', color: 'white',
                border: 'none', borderRadius: '6px', cursor: 'pointer',
                marginRight: '15px', fontSize: '14px', fontWeight: 'bold',
                opacity: testing ? 0.7 : 1,
                display: 'flex', alignItems: 'center', gap: '8px'
              }}
            >
              {testing ? '🔄 Testing...' : '🧪 Test Connection'}
            </button>
            
            {testResults.llm !== undefined && (
              <div style={{ 
                marginTop: '15px', padding: '12px', borderRadius: '6px',
                backgroundColor: testResults.llm ? '#f0fff4' : '#fed7d7',
                border: `1px solid ${testResults.llm ? '#9ae6b4' : '#feb2b2'}`
              }}>
                <div style={{ 
                  color: testResults.llm ? '#38a169' : '#e53e3e',
                  fontWeight: 'bold', fontSize: '14px', marginBottom: '5px'
                }}>
                  {testResults.llm ? '✅ Connection Successful!' : '❌ Connection Failed'}
                </div>
                {testResults.llm && (
                  <div style={{ fontSize: '13px', color: '#38a169' }}>
                    Your AI assistant is ready to help! 🎉
                  </div>
                )}
              </div>
            )}

            {errors.llm && (
              <div style={{ 
                marginTop: '15px', padding: '12px', borderRadius: '6px',
                backgroundColor: '#fed7d7', border: '1px solid #feb2b2'
              }}>
                <div style={{ color: '#e53e3e', fontSize: '13px' }}>
                  {errors.llm}
                </div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              onClick={handlePrev}
              style={{ 
                padding: '12px 20px', border: '1px solid #e2e8f0', 
                backgroundColor: 'white', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              ← Previous
            </button>
            <button 
              onClick={handleNext}
              style={{ 
                padding: '12px 24px', backgroundColor: '#3182ce', color: 'white', 
                border: 'none', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px', fontWeight: 'bold'
              }}
            >
              Next: Repository Setup →
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div style={{ 
          backgroundColor: 'white', padding: '30px', borderRadius: '12px', 
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)', marginBottom: '30px'
        }}>
          <h2 style={{ 
            color: '#2d3748', marginBottom: '15px', fontSize: '22px',
            display: 'flex', alignItems: 'center', gap: '10px'
          }}>
            📚 MCP Server Repository
          </h2>
          <p style={{ color: '#4a5568', marginBottom: '25px', fontSize: '14px' }}>
            Choose where to get your MCP servers from. We recommend our curated collection for beginners.
          </p>

          <div style={{ marginBottom: '30px' }}>
            <div style={{ 
              background: '#ebf8ff', border: '2px solid #3182ce', 
              padding: '20px', borderRadius: '12px', marginBottom: '20px'
            }}>
              <h3 style={{ 
                color: '#2b6cb0', marginBottom: '10px', fontSize: '16px',
                display: 'flex', alignItems: 'center', gap: '8px'
              }}>
                🚀 Quick Start (Recommended)
              </h3>
              <p style={{ color: '#2b6cb0', fontSize: '13px', marginBottom: '15px' }}>
                Use our official collection of tested MCP servers. Perfect for getting started quickly!
              </p>
              <button
                onClick={handleQuickStart}
                style={{
                  padding: '12px 20px', backgroundColor: '#3182ce', color: 'white',
                  border: 'none', borderRadius: '6px', cursor: 'pointer',
                  fontSize: '14px', fontWeight: 'bold',
                  display: 'flex', alignItems: 'center', gap: '8px'
                }}
              >
                ✨ Use Quick Start
              </button>
              {config.expeditedSetup && (
                <div style={{ 
                  marginTop: '10px', padding: '10px', backgroundColor: '#c6f6d5',
                  borderRadius: '6px', color: '#22543d', fontSize: '12px'
                }}>
                  ✅ Quick Start enabled! Using official MCP Hub registry.
                </div>
              )}
            </div>

            {!config.expeditedSetup && (
              <div>
                <h3 style={{ marginBottom: '15px', color: '#2d3748', fontSize: '16px' }}>
                  🔧 Custom Repository (Advanced)
                </h3>
                <div style={{ marginBottom: '15px' }}>
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
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              onClick={handlePrev}
              style={{ 
                padding: '12px 20px', border: '1px solid #e2e8f0', 
                backgroundColor: 'white', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              ← Previous
            </button>
            <button 
              onClick={handleNext}
              style={{ 
                padding: '12px 24px', backgroundColor: '#3182ce', color: 'white', 
                border: 'none', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px', fontWeight: 'bold'
              }}
            >
              Next: Review Setup →
            </button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div style={{ 
          backgroundColor: 'white', padding: '30px', borderRadius: '12px', 
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)', marginBottom: '30px'
        }}>
          <h2 style={{ 
            color: '#2d3748', marginBottom: '15px', fontSize: '22px',
            display: 'flex', alignItems: 'center', gap: '10px'
          }}>
            📋 Review Your Setup
          </h2>
          <p style={{ color: '#4a5568', marginBottom: '25px', fontSize: '14px' }}>
            Everything looks good! Here's a summary of your configuration:
          </p>

          <div style={{ background: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '25px' }}>
            <h3 style={{ marginBottom: '15px', color: '#2d3748', fontSize: '16px' }}>
              🎯 Configuration Summary
            </h3>
            
            <div style={{ marginBottom: '15px', paddingBottom: '15px', borderBottom: '1px solid #e2e8f0' }}>
              <strong style={{ color: '#4a5568' }}>🤖 AI Assistant:</strong>
              <div style={{ marginTop: '5px', fontSize: '14px' }}>
                {config.llmBackend === 'claude' && '🔵 Claude Desktop (Free & Private)'}
                {config.llmBackend === 'openai' && '🟢 OpenAI ChatGPT (Cloud-based)'}
                {config.llmBackend === 'custom' && `⚙️ Custom Service: ${config.customLLMUrl}`}
              </div>
            </div>

            <div style={{ marginBottom: '15px', paddingBottom: '15px', borderBottom: '1px solid #e2e8f0' }}>
              <strong style={{ color: '#4a5568' }}>📚 MCP Repository:</strong>
              <div style={{ marginTop: '5px', fontSize: '14px' }}>
                {config.expeditedSetup 
                  ? '🚀 Quick Start (Official MCP Hub Registry)' 
                  : `📂 Custom: ${config.gitRemote || 'Not specified'}`}
              </div>
            </div>

            <div>
              <strong style={{ color: '#4a5568' }}>🔧 System Status:</strong>
              <div style={{ marginTop: '8px', display: 'flex', gap: '15px', fontSize: '13px' }}>
                <span style={{ color: config.dependencies.docker ? '#38a169' : '#e53e3e' }}>
                  {config.dependencies.docker ? '✅' : '❌'} Docker
                </span>
                <span style={{ color: config.dependencies.git ? '#38a169' : '#e53e3e' }}>
                  {config.dependencies.git ? '✅' : '❌'} Git  
                </span>
                <span style={{ color: config.dependencies.python ? '#38a169' : '#f6ad55' }}>
                  {config.dependencies.python ? '✅' : '⚠️'} Python (Optional)
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              onClick={handlePrev}
              style={{ 
                padding: '12px 20px', border: '1px solid #e2e8f0', 
                backgroundColor: 'white', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              ← Previous
            </button>
            <button 
              onClick={handleNext}
              style={{ 
                padding: '15px 30px', backgroundColor: '#38a169', color: 'white', 
                border: 'none', borderRadius: '8px', cursor: 'pointer',
                fontSize: '16px', fontWeight: 'bold',
                display: 'flex', alignItems: 'center', gap: '8px'
              }}
            >
              🚀 Complete Setup
            </button>
          </div>
        </div>
      )}

      {step === 5 && (
        <div style={{ 
          backgroundColor: 'white', padding: '40px', borderRadius: '12px', 
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)', textAlign: 'center'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '20px' }}>🎉</div>
          <h2 style={{ color: '#38a169', marginBottom: '15px', fontSize: '24px' }}>
            Welcome to MCP Hub!
          </h2>
          <p style={{ color: '#4a5568', marginBottom: '30px', fontSize: '16px', lineHeight: '1.5' }}>
            Your setup is complete! You're now ready to discover, install, and manage AI-powered tools 
            that will supercharge your productivity.
          </p>
          
          <div style={{ 
            background: '#f0fff4', padding: '20px', borderRadius: '8px', 
            marginBottom: '30px', textAlign: 'left'
          }}>
            <h3 style={{ color: '#38a169', marginBottom: '10px', fontSize: '16px' }}>
              🌟 What's Next?
            </h3>
            <ul style={{ color: '#22543d', fontSize: '14px', lineHeight: '1.6', margin: 0, paddingLeft: '20px' }}>
              <li>Browse available MCP servers in the main app</li>
              <li>Install tools for web scraping, file management, and more</li>
              <li>Connect them to your AI assistant for powerful workflows</li>
              <li>Enjoy your enhanced AI capabilities! ✨</li>
            </ul>
          </div>

          <button 
            onClick={handleComplete}
            style={{
              padding: '15px 30px', backgroundColor: '#38a169', color: 'white',
              border: 'none', borderRadius: '8px', fontSize: '16px', cursor: 'pointer',
              fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px',
              margin: '0 auto'
            }}
          >
            🎯 Launch MCP Hub
          </button>
        </div>
      )}
    </div>
  );
};

export default Wizard;
