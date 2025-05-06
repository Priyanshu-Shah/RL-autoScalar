/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds
  const [lastUpdated, setLastUpdated] = useState(null);

  // Node endpoints
  const NODE_ENDPOINTS = [
    { id: 'web-node-1', url: 'http://localhost:8081/metrics' },
    { id: 'db-node-1', url: 'http://localhost:8082/metrics' },
    { id: 'worker-node-1', url: 'http://localhost:8083/metrics' },
  ];

  // Get status color based on CPU and memory usage
  const getStatusColor = (cpuLoad, memoryUsage, allocatedMemory) => {
    const memoryPercent = memoryUsage / allocatedMemory * 100;
    
    if (cpuLoad > 80 || memoryPercent > 80) {
      return '#ff5252'; // Red - Alert
    } else if (cpuLoad > 60 || memoryPercent > 60) {
      return '#ffb142'; // Orange - Warning
    } else {
      return '#2ed573'; // Green - Normal
    }
  };
  
  // Format memory values
  const formatMemory = (value) => {
    return `${Math.round(value)} MB`;
  };
  
  // Fetch all node metrics
  const fetchNodeData = async () => {
    try {
      setLoading(true);
      const nodeData = await Promise.all(
        NODE_ENDPOINTS.map(async (node) => {
          try {
            const response = await fetch(node.url);
            if (!response.ok) {
              throw new Error(`Failed to fetch ${node.id}`);
            }
            const data = await response.json();
            console.log(`Fetched data for ${node.id}:`, data);
            return { ...data, isOnline: true };
          } catch (error) {
            console.error(`Error fetching ${node.id}:`, error);
            // Return offline node with default values
            return {
              nodeId: node.id,
              memoryUsage: 0,
              cpuLoad: 0,
              allocatedMemory: 0,
              status: "Offline",
              timestamp: Date.now(),
              isOnline: false
            };
          }
        })
      );
      
      setNodes(nodeData);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError("Failed to fetch node metrics");
      console.error("Error fetching node metrics:", err);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch and setup interval
  useEffect(() => {
    fetchNodeData();
    
    const intervalId = setInterval(fetchNodeData, refreshInterval);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [refreshInterval]);

  // Handle refresh interval change
  const handleRefreshChange = (e) => {
    const value = parseInt(e.target.value, 10);
    setRefreshInterval(value);
  };

  // Manual refresh button handler
  const handleManualRefresh = () => {
    fetchNodeData();
  };

  return (
    <div className="dashboard">
      <header className="header">
        <div className="header-left">
          <h1>RL-autoScalar</h1>
          {lastUpdated && <span className="last-updated">Last updated: {lastUpdated}</span>}
        </div>
        <div className="refresh-controls">
          <span>Auto-refresh: </span>
          <select value={refreshInterval} onChange={handleRefreshChange}>
            <option value={2000}>2 seconds</option>
            <option value={5000}>5 seconds</option>
            <option value={10000}>10 seconds</option>
            <option value={30000}>30 seconds</option>
          </select>
          <button onClick={handleManualRefresh} className="refresh-button">
            Refresh Now
          </button>
        </div>
      </header>
      
      {loading && nodes.length === 0 && (
        <div className="loading">Loading node data...</div>
      )}
      
      {error && (
        <div className="error-message">
          {error} <button onClick={fetchNodeData}>Try Again</button>
        </div>
      )}
      
      <div className="nodes-grid">
        {nodes.map((node) => (
          <div 
            key={node.nodeId} 
            className={`node-card ${!node.isOnline ? 'offline' : ''}`}
          >
            <div className="node-header">
              <h2>{node.nodeId}</h2>
              <span 
                className="status-indicator" 
                style={{ 
                  backgroundColor: node.isOnline 
                    ? getStatusColor(node.cpuLoad, node.memoryUsage, node.allocatedMemory)
                    : '#888' 
                }}
              ></span>
            </div>
            
            <div className="metrics">
              <div className="metric">
                <div className="metric-name">Status</div>
                <div className="metric-value">{node.isOnline ? node.status : 'Offline'}</div>
              </div>

              <div className="metric">
                <div className="metric-name">CPU Load</div>
                <div className="metric-value">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ 
                        width: `${node.isOnline ? Math.min(100, node.cpuLoad) : 0}%`,
                        backgroundColor: node.isOnline 
                          ? getStatusColor(node.cpuLoad, 0, 1) 
                          : '#555'
                      }}
                    ></div>
                  </div>
                  <span className="value-text">{node.isOnline ? `${Math.round(node.cpuLoad)}%` : 'N/A'}</span>
                </div>
              </div>
              
              <div className="metric">
                <div className="metric-name">Memory Usage</div>
                <div className="metric-value">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ 
                        width: node.isOnline 
                          ? `${Math.min(100, (node.memoryUsage / node.allocatedMemory) * 100)}%` 
                          : '0%',
                        backgroundColor: node.isOnline 
                          ? getStatusColor(0, node.memoryUsage, node.allocatedMemory) 
                          : '#555'
                      }}
                    ></div>
                  </div>
                  <span className="value-text">
                    {node.isOnline 
                      ? `${formatMemory(node.memoryUsage)} / ${formatMemory(node.allocatedMemory)}` 
                      : 'N/A'
                    }
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <footer>
        <p>RL-autoScalar Dashboard • Blockchain-Powered Auto-Scaling System</p>
      </footer>
    </div>
  )
}

export default App