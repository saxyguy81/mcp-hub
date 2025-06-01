import React, { useState, useEffect } from 'react';
import ProxyManager from './pages/ProxyManager';
import Settings from './pages/Settings';

interface MCPService {
  name: string;
  status: 'running' | 'stopped' | 'error';
  url?: string;
  port?: number;
}

interface ProxyStatus {
  running: boolean;
  healthy: boolean;
  endpoint?: string;
}

function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'proxy' | 'settings'>('dashboard');
  const [services, setServices] = useState<MCPService[]>([]);
  const [proxyStatus, setProxyStatus] = useState<ProxyStatus>({ running: false, healthy: false });
  const [loading, setLoading] = useState(true);

  const checkServices = async () => {
    try {
      const result = await window.electronAPI?.executeCommand(['status']);
      if (result?.stdout) {
        // Parse mcpctl status output to get services
        // This is a simplified parser - you'd want more robust parsing
        const mockServices: MCPService[] = [
          { name: 'firecrawl', status: 'running', url: 'http://localhost:8081', port: 8081 },
          { name: 'web-search', status: 'running', url: 'http://localhost:8082', port: 8082 },
        ];
        setServices(mockServices);
      }
    } catch (error) {
      console.error('Failed to check services:', error);
    }
  };

  const checkProxyStatus = async () => {
    try {
      const response = await fetch('http://localhost:3000/health');
      if (response.ok) {
        setProxyStatus({ 
          running: true, 
          healthy: true, 
          endpoint: 'http://localhost:3000' 
        });
      } else {
        setProxyStatus({ running: false, healthy: false });
      }
    } catch (error) {
      setProxyStatus({ running: false, healthy: false });
    }
  };

  const startServices = async () => {
    try {
      setLoading(true);
      await window.electronAPI?.executeCommand(['start']);
      setTimeout(() => {
        checkServices();
        setLoading(false);
      }, 3000);
    } catch (error) {
      console.error('Failed to start services:', error);
      setLoading(false);
    }
  };

  const stopServices = async () => {
    try {
      setLoading(true);
      await window.electronAPI?.executeCommand(['stop']);
      setTimeout(() => {
        checkServices();
        checkProxyStatus();
        setLoading(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to stop services:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await checkServices();
      await checkProxyStatus();
      setLoading(false);
    };

    init();

    // Poll for status updates
    const interval = setInterval(() => {
      checkServices();
      checkProxyStatus();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  if (currentView === 'proxy') {
    return <ProxyManager onClose={() => setCurrentView('dashboard')} />;
  }

  if (currentView === 'settings') {
    return <Settings onClose={() => setCurrentView('dashboard')} />;
  }

  // Main Dashboard
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f7fafc', 
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' 
    }}>
      {/* Header */}
      <div style={{ 
        backgroundColor: 'white', 
        borderBottom: '1px solid #e2e8f0', 
        padding: '20px 30px' 
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ 
            margin: 0, 
            fontSize: '28px', 
            fontWeight: 'bold', 
            color: '#1a365d' 
          }}>
            🚀 MCP Hub
          </h1>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <button 
              onClick={() => setCurrentView('proxy')}
              style={{ 
                background: proxyStatus.running ? '#48bb78' : '#4299e1', 
                color: 'white', 
                border: 'none', 
                borderRadius: '8px', 
                padding: '10px 20px', 
                cursor: 'pointer',
                fontSize: '14px', 
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              🎯 Proxy Manager
              {proxyStatus.running && <span style={{ fontSize: '12px' }}>🟢</span>}
            </button>
            
            <button 
              onClick={() => setCurrentView('settings')}
              style={{ 
                background: '#805ad5', 
                color: 'white', 
                border: 'none', 
                borderRadius: '8px', 
                padding: '10px 20px', 
                cursor: 'pointer',
                fontSize: '14px', 
                fontWeight: 'bold'
              }}
            >
              ⚙️ Settings
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ padding: '30px' }}>
        {/* Connection Status Card */}
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '12px', 
          padding: '25px', 
          marginBottom: '25px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ margin: '0 0 20px 0', fontSize: '20px', color: '#2d3748' }}>
            🔗 Connection Status
          </h2>
          
          {proxyStatus.running ? (
            <div style={{ 
              backgroundColor: '#f0fff4', 
              border: '1px solid #9ae6b4', 
              borderRadius: '8px', 
              padding: '20px',
              marginBottom: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
                <span style={{ fontSize: '24px' }}>🟢</span>
                <div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#22543d' }}>
                    Single Endpoint Mode Active
                  </div>
                  <div style={{ fontSize: '14px', color: '#2f855a' }}>
                    All MCP servers accessible via single endpoint
                  </div>
                </div>
              </div>
              
              <div style={{ 
                backgroundColor: '#1a202c', 
                color: '#f7fafc', 
                padding: '12px', 
                borderRadius: '6px', 
                fontFamily: 'monospace',
                fontSize: '14px',
                marginBottom: '10px'
              }}>
                http://localhost:3000
              </div>
              
              <div style={{ fontSize: '14px', color: '#2f855a' }}>
                ✅ Configure your LLM client with this single endpoint instead of multiple URLs
              </div>
            </div>
          ) : (
            <div style={{ 
              backgroundColor: '#fffbeb', 
              border: '1px solid #f6e05e', 
              borderRadius: '8px', 
              padding: '20px',
              marginBottom: '20px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
                <span style={{ fontSize: '24px' }}>🟡</span>
                <div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#744210' }}>
                    Multi-Endpoint Mode
                  </div>
                  <div style={{ fontSize: '14px', color: '#9c4221' }}>
                    Each MCP server requires separate configuration
                  </div>
                </div>
              </div>
              
              <button 
                onClick={() => setCurrentView('proxy')}
                style={{ 
                  background: '#4299e1', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '6px', 
                  padding: '10px 20px', 
                  cursor: 'pointer',
                  fontSize: '14px', 
                  fontWeight: 'bold'
                }}
              >
                🎯 Enable Single Endpoint Mode
              </button>
            </div>
          )}
        </div>

        {/* Services Status */}
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '12px', 
          padding: '25px', 
          marginBottom: '25px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2 style={{ margin: 0, fontSize: '20px', color: '#2d3748' }}>
              🐳 MCP Services
            </h2>
            
            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                onClick={startServices}
                disabled={loading}
                style={{ 
                  background: loading ? '#a0aec0' : '#48bb78', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '6px', 
                  padding: '10px 20px', 
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '14px', 
                  fontWeight: 'bold'
                }}
              >
                {loading ? '⏳' : '🚀'} Start
              </button>
              
              <button 
                onClick={stopServices}
                disabled={loading}
                style={{ 
                  background: loading ? '#a0aec0' : '#f56565', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '6px', 
                  padding: '10px 20px', 
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '14px', 
                  fontWeight: 'bold'
                }}
              >
                {loading ? '⏳' : '🛑'} Stop
              </button>
            </div>
          </div>
          
          {services.length === 0 ? (
            <div style={{ 
              backgroundColor: '#f7fafc', 
              border: '1px solid #e2e8f0', 
              borderRadius: '8px', 
              padding: '20px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '10px' }}>📭</div>
              <div style={{ fontSize: '16px', color: '#4a5568', marginBottom: '10px' }}>
                No MCP services running
              </div>
              <div style={{ fontSize: '14px', color: '#718096' }}>
                Start services to see them here
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
              {services.map((service) => (
                <div 
                  key={service.name}
                  style={{ 
                    border: '1px solid #e2e8f0', 
                    borderRadius: '8px', 
                    padding: '16px',
                    backgroundColor: service.status === 'running' ? '#f0fff4' : 
                                   service.status === 'error' ? '#fed7d7' : '#f7fafc'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                      {service.name}
                    </div>
                    <span style={{ fontSize: '20px' }}>
                      {service.status === 'running' ? '🟢' : 
                       service.status === 'error' ? '🔴' : '🟡'}
                    </span>
                  </div>
                  
                  {service.url && (
                    <div style={{ fontSize: '12px', color: '#666', fontFamily: 'monospace' }}>
                      {service.url}
                    </div>
                  )}
                  
                  <div style={{ 
                    fontSize: '12px', 
                    color: service.status === 'running' ? '#2f855a' : 
                           service.status === 'error' ? '#e53e3e' : '#718096',
                    textTransform: 'capitalize',
                    marginTop: '5px'
                  }}>
                    {service.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '12px', 
          padding: '25px',
          border: '1px solid #e2e8f0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ margin: '0 0 20px 0', fontSize: '20px', color: '#2d3748' }}>
            ⚡ Quick Actions
          </h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <button 
              onClick={() => setCurrentView('proxy')}
              style={{ 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                color: 'white', 
                border: 'none', 
                borderRadius: '8px', 
                padding: '20px', 
                cursor: 'pointer',
                fontSize: '14px', 
                fontWeight: 'bold',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎯</div>
              <div style={{ fontSize: '16px', marginBottom: '4px' }}>Proxy Manager</div>
              <div style={{ fontSize: '12px', opacity: 0.9 }}>
                Manage single endpoint aggregation
              </div>
            </button>
            
            <button 
              onClick={() => window.electronAPI?.openUrl('http://localhost:3000/status')}
              style={{ 
                background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', 
                color: 'white', 
                border: 'none', 
                borderRadius: '8px', 
                padding: '20px', 
                cursor: 'pointer',
                fontSize: '14px', 
                fontWeight: 'bold',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>📊</div>
              <div style={{ fontSize: '16px', marginBottom: '4px' }}>View Status</div>
              <div style={{ fontSize: '12px', opacity: 0.9 }}>
                Open proxy status page
              </div>
            </button>
            
            <button 
              onClick={() => setCurrentView('settings')}
              style={{ 
                background: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', 
                color: 'white', 
                border: 'none', 
                borderRadius: '8px', 
                padding: '20px', 
                cursor: 'pointer',
                fontSize: '14px', 
                fontWeight: 'bold',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>⚙️</div>
              <div style={{ fontSize: '16px', marginBottom: '4px' }}>Settings</div>
              <div style={{ fontSize: '12px', opacity: 0.9 }}>
                Configure MCP Hub
              </div>
            </button>
            
            <button 
              onClick={() => window.electronAPI?.openUrl('https://github.com/saxyguy81/mcp-hub')}
              style={{ 
                background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', 
                color: '#2d3748', 
                border: 'none', 
                borderRadius: '8px', 
                padding: '20px', 
                cursor: 'pointer',
                fontSize: '14px', 
                fontWeight: 'bold',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>📚</div>
              <div style={{ fontSize: '16px', marginBottom: '4px' }}>Documentation</div>
              <div style={{ fontSize: '12px', opacity: 0.8 }}>
                View project documentation
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
