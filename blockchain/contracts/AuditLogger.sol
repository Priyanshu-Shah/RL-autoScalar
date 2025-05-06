// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.19;

contract AuditLogger {
    enum NodeStatus { Normal, Scaling, Alert }
    
    struct NodeMetrics {
        string nodeId;
        uint256 timestamp;
        uint256 memoryUsage; // MB
        uint256 cpuLoad; // percentage (0-100)
        uint256 allocatedMemory; // MB
        NodeStatus status; // Normal, Scaling, Alert
        string scaleAction; // scale_up, scale_down, none
    }
    
    struct ScalingEvent {
        string nodeId;
        uint256 timestamp;
        string action;
        string reason;  
        address initiator; // address of initiator (RL model or manual)
    }
    
    event MetricsLogged(string indexed nodeId, uint256 timestamp, NodeStatus status);
    event ScalingActionPerformed(string indexed nodeId, string action, uint256 timestamp);
    
    // historical data
    NodeMetrics[] public nodeMetricsHistory;
    ScalingEvent[] public scalingEventHistory;
    
    mapping(string => NodeMetrics) public latestNodeMetrics;
    mapping(address => bool) public authorizedLoggers;

    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only contract owner can call this function");
        _;
    }
    modifier onlyAuthorized() {
        require(authorizedLoggers[msg.sender] || msg.sender == owner, "Caller not authorized");
        _;
    }
    
    constructor() {
        owner = msg.sender;
        authorizedLoggers[msg.sender] = true;
    }

    function addAuthorizedLogger(address _logger) external onlyOwner {
        authorizedLoggers[_logger] = true;
    }
    function removeAuthorizedLogger(address _logger) external onlyOwner {
        authorizedLoggers[_logger] = false;
    }
    
    function logNodeMetrics(
        string calldata _nodeId,
        uint256 _memoryUsage,
        uint256 _cpuLoad,
        uint256 _allocatedMemory,
        NodeStatus _status
    ) external onlyAuthorized {
        uint256 timestamp = block.timestamp;
        NodeMetrics memory metrics = NodeMetrics({
            nodeId: _nodeId,
            timestamp: timestamp,
            memoryUsage: _memoryUsage,
            cpuLoad: _cpuLoad,
            allocatedMemory: _allocatedMemory,
            status: _status,
            scaleAction: "none"
        });
        latestNodeMetrics[_nodeId] = metrics; //latest
        nodeMetricsHistory.push(metrics); //history
        emit MetricsLogged(_nodeId, timestamp, _status); //log
    }
    
    function logScalingAction(
        string calldata _nodeId,
        string calldata _action,
        string calldata _reason
    ) external onlyAuthorized {
        uint256 timestamp = block.timestamp;
        ScalingEvent memory event_ = ScalingEvent({
            nodeId: _nodeId,
            timestamp: timestamp,
            action: _action,
            reason: _reason,
            initiator: msg.sender
        });
        if (bytes(latestNodeMetrics[_nodeId].nodeId).length > 0) {
            latestNodeMetrics[_nodeId].scaleAction = _action;
            latestNodeMetrics[_nodeId].status = NodeStatus.Scaling;
        } //update
        scalingEventHistory.push(event_); //history
        emit ScalingActionPerformed(_nodeId, _action, timestamp); //log
    }
    
    function getLatestNodeMetrics(string calldata _nodeId) external view returns (NodeMetrics memory) {
        return latestNodeMetrics[_nodeId];
    }
    function getMetricsHistoryLength() external view returns (uint256) {
        return nodeMetricsHistory.length;
    }
    function getScalingEventsLength() external view returns (uint256) {
        return scalingEventHistory.length;
    }

    function getNodeMetricsHistory(
        string calldata _nodeId,
        uint256 _startIndex,
        uint256 _count
    ) external view returns (NodeMetrics[] memory) {
        require(_startIndex + _count <= nodeMetricsHistory.length, "Index out of bounds");
        uint256 matchCount = 0;
        for (uint256 i = _startIndex; i < _startIndex + _count; i++) {
            if (keccak256(bytes(nodeMetricsHistory[i].nodeId)) == keccak256(bytes(_nodeId))) {
                matchCount++;
            }
        }
        NodeMetrics[] memory result = new NodeMetrics[](matchCount);
        uint256 resultIndex = 0;
        for (uint256 i = _startIndex; i < _startIndex + _count; i++) {
            if (keccak256(bytes(nodeMetricsHistory[i].nodeId)) == keccak256(bytes(_nodeId))) {
                result[resultIndex] = nodeMetricsHistory[i];
                resultIndex++;
            }
        }
        return result;
    }
}