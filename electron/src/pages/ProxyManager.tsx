import React, { useState, useEffect } from 'react';

interface ProxyStatus {
  running: boolean;
  healthy: boolean;
  data?: {
    servers: number;
    healthy_servers: number;
    server_list: string[];
  };
}

interface BackendServer {
  name: string;
  url: string;
  healthy: boolean;
  last_check?: string;
  error_count: number;
  capabilities?: any;
}

interface ProxyManagerProps {
  onClose: () => void;
}

const ProxyManager: React.FC<ProxyManagerProps> = ({ onClose }) => {
  const [proxyStatus, setProxyStatus] = useState<ProxyStatus>({ running: false, healthy: false });
  const [servers, setServers] = useState<BackendServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [logs, setLogs] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'status' | 'servers' | 'logs'>('status');

  const checkProxyStatus = async () => {
    try {
      const response = await fetch('http://localhost:3000/health');
      if (response.ok) {
        const data = await response.json();
        setProxyStatus({ running: true, healthy: true, data });
      } else {
        setProxyStatus({ running: false, healthy: false });
      }
    } catch (error) {
      setProxyStatus({ running: false, healthy: false });
    }
  };

  const fetchServers = async () => {
    try {
      const response = await fetch('http://localhost:3000/servers');
      if (response.ok) {
        const data = await response.json();
        setServers(data.servers || []);
      }
    } catch (error) {
      console.error('Failed to fetch servers:', error);
    }
  };

  const fetchLogs = async () => {
    try {
      const result = await window.electronAPI?.executeCommand(['proxy', 'logs', '--lines', '100']);
      if (result?.stdout) {
        setLogs(result.stdout);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  };

  const startProxy = async () => {
    setStarting(true);
    try {
      const result = await window.electronAPI?.executeCommand(['proxy', 'start']);
      if (result?.success) {
        setTimeout(checkProxyStatus, 2000); // Wait a bit before checking status
      }
    } catch (error) {
      console.error('Failed to start proxy:', error);
    } finally {
      setStarting(false);
    }
  };

  const stopProxy = async () => {
    setStopping(true);
    try {
      await window.electronAPI?.executeCommand(['proxy', 'stop']);
      setTimeout(checkProxyStatus, 1000);
    } catch (error) {
      console.error('Failed to stop proxy:', error);
    } finally {
      setStopping(false);
    }
  };

  const restartProxy = async () => {
    setStopping(true);
    try {
      await stopProxy();
      setTimeout(startProxy, 2000);
    } catch (error) {
      console.error('Failed to restart proxy:', error);
    } finally {
      setStopping(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await checkProxyStatus();
      if (proxyStatus.running) {
        await fetchServers();
      }
      setLoading(false);
    };

    init();

    // Set up polling for status updates
    const interval = setInterval(() => {
      checkProxyStatus();
      if (proxyStatus.running) {
        fetchServers();
      }
      if (activeTab === 'logs') {
        fetchLogs();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [activeTab, proxyStatus.running]);

  const tabStyle = (isActive: boolean) => ({
    padding: '12px 24px',
    border: 'none',
    backgroundColor: isActive ? '#3182ce' : '#e2e8f0',
    color: isActive ? 'white' : '#4a5568',
    cursor: 'pointer',
    borderRadius: '6px 6px 0 0',
    fontWeight: isActive ? 'bold' : 'normal',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  });

  const getStatusIcon = () => {
    if (loading) return '⏳';
    if (proxyStatus.running && proxyStatus.healthy) return '🟢';
    if (proxyStatus.running && !proxyStatus.healthy) return '🟡';
    return '🔴';
  };

  const getStatusText = () => {
    if (loading) return 'Checking...';
    if (proxyStatus.running && proxyStatus.healthy) return 'Running & Healthy';
    if (proxyStatus.running && !proxyStatus.healthy) return 'Running but Unhealthy';
    return 'Not Running';
  };

  return (
    <div style={{ 
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', 
      alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div style={{ 
        backgroundColor: 'white', borderRadius: '12px', width: '90%', 
        maxWidth: '1000px', height: '85%', display: 'flex', flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{ 
          padding: '25px', borderBottom: '1px solid #e2e8f0', 
          display: 'flex', justifyContent: 'space-between', alignItems: 'center' 
        }}>
          <h2 style={{ color: '#1a365d', margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
            🎯 MCP Hub Proxy Manager
          </h2>
          <button 
            onClick={onClose}
            style={{ 
              background: '#f56565', color: 'white', border: 'none', 
              borderRadius: '6px', padding: '10px 20px', cursor: 'pointer',
              fontSize: '16px', fontWeight: 'bold'
            }}
          >
            ✕ Close
          </button>
        </div>

        {/* Status Overview */}
        <div style={{ padding: '20px', borderBottom: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '15px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '24px' }}>{getStatusIcon()}</span>
              <div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  {getStatusText()}
                </div>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  http://localhost:3000
                </div>
              </div>
            </div>

            {proxyStatus.data && (
              <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                  {proxyStatus.data.healthy_servers}/{proxyStatus.data.servers} Servers Healthy
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Backend Services
                </div>
              </div>
            )}
          </div>

          {/* Control Buttons */}
          <div style={{ display: 'flex', gap: '10px' }}>
            {!proxyStatus.running ? (
              <button 
                onClick={startProxy}
                disabled={starting}
                style={{ 
                  background: starting ? '#a0aec0' : '#48bb78', 
                  color: 'white', border: 'none', borderRadius: '6px', 
                  padding: '10px 20px', cursor: starting ? 'not-allowed' : 'pointer',
                  fontSize: '14px', fontWeight: 'bold'
                }}
              >
                {starting ? '⏳ Starting...' : '🚀 Start Proxy'}
              </button>
            ) : (
              <>
                <button 
                  onClick={stopProxy}
                  disabled={stopping}
                  style={{ 
                    background: stopping ? '#a0aec0' : '#f56565', 
                    color: 'white', border: 'none', borderRadius: '6px', 
                    padding: '10px 20px', cursor: stopping ? 'not-allowed' : 'pointer',
                    fontSize: '14px', fontWeight: 'bold'
                  }}
                >
                  {stopping ? '⏳ Stopping...' : '🛑 Stop'}
                </button>
                <button 
                  onClick={restartProxy}
                  disabled={stopping}
                  style={{ 
                    background: stopping ? '#a0aec0' : '#ed8936', 
                    color: 'white', border: 'none', borderRadius: '6px', 
                    padding: '10px 20px', cursor: stopping ? 'not-allowed' : 'pointer',
                    fontSize: '14px', fontWeight: 'bold'
                  }}
                >
                  🔄 Restart
                </button>
              </>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', padding: '0 20px', backgroundColor: '#f7fafc' }}>
          <button 
            style={tabStyle(activeTab === 'status')}
            onClick={() => setActiveTab('status')}
          >
            📊 Status
          </button>
          <button 
            style={tabStyle(activeTab === 'servers')}
            onClick={() => setActiveTab('servers')}
          >
            🔗 Servers ({servers.length})
          </button>
          <button 
            style={tabStyle(activeTab === 'logs')}
            onClick={() => setActiveTab('logs')}
          >
            📜 Logs
          </button>
        </div>

        {/* Tab Content */}
        <div style={{ flex: 1, padding: '20px', overflow: 'auto' }}>
          {activeTab === 'status' && (
            <div>
              <h3 style={{ marginTop: 0, color: '#2d3748' }}>📊 Proxy Status</h3>
              
              {proxyStatus.running ? (
                <div>
                  <div style={{ 
                    backgroundColor: '#f0fff4', 
                    border: '1px solid #9ae6b4', 
                    borderRadius: '8px', 
                    padding: '16px', 
                    marginBottom: '20px' 
                  }}>
                    <h4 style={{ margin: '0 0 10px 0', color: '#22543d' }}>
                      ✅ Single Endpoint Mode Active
                    </h4>
                    <p style={{ margin: 0, color: '#2f855a' }}>
                      Your LLM client can connect to <strong>http://localhost:3000</strong> for access to all MCP servers.
                    </p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                    <div style={{ 
                      backgroundColor: '#ebf8ff', 
                      border: '1px solid #90cdf4', 
                      borderRadius: '8px', 
                      padding: '16px', 
                      textAlign: 'center' 
                    }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2c5282' }}>
                        {proxyStatus.data?.servers || 0}
                      </div>
                      <div style={{ fontSize: '14px', color: '#2a69ac' }}>Total Servers</div>
                    </div>
                    
                    <div style={{ 
                      backgroundColor: '#f0fff4', 
                      border: '1px solid #9ae6b4', 
                      borderRadius: '8px', 
                      padding: '16px', 
                      textAlign: 'center' 
                    }}>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#22543d' }}>
                        {proxyStatus.data?.healthy_servers || 0}
                      </div>
                      <div style={{ fontSize: '14px', color: '#2f855a' }}>Healthy Servers</div>
                    </div>
                  </div>

                  <div style={{ marginTop: '20px' }}>
                    <h4 style={{ color: '#2d3748' }}>🔗 LLM Client Configuration</h4>
                    <div style={{ 
                      backgroundColor: '#f7fafc', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px', 
                      padding: '16px' 
                    }}>
                      <p style={{ margin: '0 0 10px 0' }}>
                        Add this single endpoint to your LLM client:
                      </p>
                      <code style={{ 
                        backgroundColor: '#1a202c', 
                        color: '#f7fafc', 
                        padding: '8px 12px', 
                        borderRadius: '4px', 
                        display: 'block',
                        fontSize: '14px'
                      }}>
                        http://localhost:3000
                      </code>
                      <p style={{ margin: '10px 0 0 0', fontSize: '14px', color: '#718096' }}>
                        This replaces the need to configure multiple individual endpoints.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ 
                  backgroundColor: '#fed7d7', 
                  border: '1px solid #feb2b2', 
                  borderRadius: '8px', 
                  padding: '16px' 
                }}>
                  <h4 style={{ margin: '0 0 10px 0', color: '#742a2a' }}>
                    ❌ Proxy Not Running
                  </h4>
                  <p style={{ margin: '0 0 10px 0', color: '#9b2c2c' }}>
                    The MCP Hub proxy is not currently running. Start it to enable single-endpoint mode.
                  </p>
                  <button 
                    onClick={startProxy}
                    disabled={starting}
                    style={{ 
                      background: starting ? '#a0aec0' : '#48bb78', 
                      color: 'white', border: 'none', borderRadius: '6px', 
                      padding: '10px 20px', cursor: starting ? 'not-allowed' : 'pointer',
                      fontSize: '14px', fontWeight: 'bold'
                    }}
                  >
                    {starting ? '⏳ Starting...' : '🚀 Start Proxy Now'}
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'servers' && (
            <div>
              <h3 style={{ marginTop: 0, color: '#2d3748' }}>🔗 Backend Servers</h3>
              
              {servers.length === 0 ? (
                <div style={{ 
                  backgroundColor: '#fffbeb', 
                  border: '1px solid #f6e05e', 
                  borderRadius: '8px', 
                  padding: '16px' 
                }}>
                  <p style={{ margin: 0, color: '#744210' }}>
                    No backend servers found. Make sure your MCP services are running.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {servers.map((server) => (
                    <div 
                      key={server.name}
                      style={{ 
                        border: '1px solid #e2e8f0', 
                        borderRadius: '8px', 
                        padding: '16px',
                        backgroundColor: server.healthy ? '#f0fff4' : '#fed7d7'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontSize: '20px' }}>
                            {server.healthy ? '🟢' : '🔴'}
                          </span>
                          <div>
                            <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                              {server.name}
                            </div>
                            <div style={{ fontSize: '14px', color: '#666' }}>
                              {server.url}
                            </div>
                          </div>
                        </div>
                        
                        <div style={{ textAlign: 'right' }}>
                          {server.last_check && (
                            <div style={{ fontSize: '12px', color: '#666' }}>
                              Last check: {new Date(server.last_check).toLocaleTimeString()}
                            </div>
                          )}
                          {server.error_count > 0 && (
                            <div style={{ fontSize: '12px', color: '#e53e3e' }}>
                              Errors: {server.error_count}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {server.capabilities && Object.keys(server.capabilities).length > 0 && (
                        <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
                          Capabilities: {Object.keys(server.capabilities).join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'logs' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ margin: 0, color: '#2d3748' }}>📜 Proxy Logs</h3>
                <button 
                  onClick={fetchLogs}
                  style={{ 
                    background: '#4299e1', color: 'white', border: 'none', 
                    borderRadius: '6px', padding: '8px 16px', cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  🔄 Refresh
                </button>
              </div>
              
              <div style={{ 
                backgroundColor: '#1a202c', 
                color: '#f7fafc', 
                borderRadius: '8px', 
                padding: '16px', 
                fontSize: '12px', 
                fontFamily: 'monospace',
                height: '400px',
                overflow: 'auto',
                border: '1px solid #2d3748'
              }}>
                {logs ? (
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{logs}</pre>
                ) : (
                  <div style={{ color: '#a0aec0' }}>
                    No logs available. Logs are generated when proxy runs in background mode.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProxyManager;
