import json
import time
import logging
from enum import IntEnum
from typing import Dict, Any
from web3 import Web3
from web3.exceptions import ContractLogicError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AuditLogger')

class NodeStatus(IntEnum):
    """Enum mapping to the NodeStatus in the Solidity contract"""
    Normal = 0
    Scaling = 1
    Alert = 2

class AuditLogger:
    def __init__(
        self, 
        contract_address: str, 
        private_key: str,
        web3_provider_uri: str = "http://localhost:8545",
        abi_path: str = "contracts/abi/AuditLogger.json"
    ):
        """
            contract_address (str): The deployed AuditLogger contract address
            private_key (str): Private key for the account used to sign transactions
            web3_provider_uri (str): URI for the Web3 provider
            abi_path (str): Path to the contract ABI JSON file
        """
        self.web3 = Web3(Web3.HTTPProvider(web3_provider_uri))
        try:
            with open(abi_path, 'r') as f:
                contract_abi = json.load(f)
        except FileNotFoundError:
            logger.error(f"Contract ABI file not found at {abi_path}")
            raise FileNotFoundError(f"Contract ABI file not found: {abi_path}")
        
        # Create contract instance
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.contract = self.web3.eth.contract(address=self.contract_address, abi=contract_abi)
        
        # Set up account for sending transactions
        self.account = self.web3.eth.account.from_key(private_key)
        self.address = self.account.address
        logger.info(f"Connected to contract at {contract_address} using account {self.address}")
        self._check_authorization()
    
    def _check_authorization(self) -> None:
        """
        Check if the current account is authorized to log data.
        Raises an exception if unauthorized.
        """
        try:
            is_authorized = self.contract.functions.authorizedLoggers(self.address).call()
            if not is_authorized:
                owner = self.contract.functions.owner().call()
                if self.address.lower() != owner.lower():
                    logger.warning(f"Account {self.address} is not authorized to log data")
                    raise ValueError(f"Account {self.address} is not authorized to log metrics")
        except Exception as e:
            logger.error(f"Error checking authorization: {str(e)}")
            raise
    
    def _send_transaction(self, function, gas_limit=300000) -> str:
        """
        Helper method to send a transaction to the blockchain.
        
        Args:
            function: The contract function to call
            gas_limit: Maximum gas to use
            
        Returns:
            str: Transaction hash
        """
        try:
            # Get the latest nonce
            nonce = self.web3.eth.get_transaction_count(self.address)
            
            # Build the transaction
            txn = function.build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': gas_limit,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send the transaction
            signed_txn = self.web3.eth.account.sign_transaction(txn, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info(f"Transaction successful: {self.web3.to_hex(tx_hash)}")
                return self.web3.to_hex(tx_hash)
            else:
                logger.error(f"Transaction failed: {self.web3.to_hex(tx_hash)}")
                raise Exception(f"Transaction failed: {self.web3.to_hex(tx_hash)}")
                
        except ContractLogicError as e:
            logger.error(f"Contract logic error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            raise
    
    def log_node_metrics(
        self,
        node_id: str,
        memory_usage: int,  # MB
        cpu_load: int,      # Percentage 0-100
        allocated_memory: int,  # MB
        status: NodeStatus = NodeStatus.Normal
    ) -> str:
        """
        Returns:
            str: Transaction hash
        """
        logger.info(f"Logging metrics for node {node_id}: "
                  f"CPU: {cpu_load}%, Memory: {memory_usage}/{allocated_memory}MB, Status: {status.name}")
        
        # Call the contract function
        function = self.contract.functions.logNodeMetrics(
            node_id,
            memory_usage,
            cpu_load,
            allocated_memory,
            int(status)
        )
        
        return self._send_transaction(function)
    
    def log_scaling_action(
        self,
        node_id: str,
        action: str,
        reason: str
    ) -> str:
        """
        Log a scaling action to the blockchain.
        
        Args:
            node_id (str): Node identifier
            action (str): Action taken (e.g., "scale_up", "scale_down")
            reason (str): Reason for scaling
            
        Returns:
            str: Transaction hash
        """
        logger.info(f"Logging scaling action for node {node_id}: {action} - {reason}")
        
        # Call the contract function
        function = self.contract.functions.logScalingAction(
            node_id,
            action,
            reason
        )
        
        return self._send_transaction(function)
    
    def get_latest_node_metrics(self, node_id: str) -> Dict[str, Any]:
        """
        Get the latest metrics for a node.
        
        Args:
            node_id (str): Node identifier
            
        Returns:
            Dict[str, Any]: Latest metrics
        """
        try:
            metrics = self.contract.functions.getLatestNodeMetrics(node_id).call()
            
            # Convert to a more usable dictionary
            result = {
                'nodeId': metrics[0],
                'timestamp': metrics[1],
                'memoryUsage': metrics[2],
                'cpuLoad': metrics[3],
                'allocatedMemory': metrics[4],
                'status': NodeStatus(metrics[5]).name,
                'scaleAction': metrics[6]
            }
            
            # Add a human-readable timestamp
            result['datetime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result['timestamp']))
            
            return result
        except Exception as e:
            logger.error(f"Error getting latest metrics for {node_id}: {str(e)}")
            raise
    
    def get_node_metrics_history(self, node_id: str, start_index: int = 0, count: int = 10) -> list:
        """
        Get historical metrics for a node.
        
        Args:
            node_id (str): Node identifier
            start_index (int): Starting index in the history array
            count (int): Number of records to retrieve
            
        Returns:
            list: List of metrics dictionaries
        """
        try:
            metrics_list = self.contract.functions.getNodeMetricsHistory(node_id, start_index, count).call()
            
            # Convert to list of dictionaries with readable fields
            result = []
            for metrics in metrics_list:
                entry = {
                    'nodeId': metrics[0],
                    'timestamp': metrics[1],
                    'memoryUsage': metrics[2],
                    'cpuLoad': metrics[3],
                    'allocatedMemory': metrics[4],
                    'status': NodeStatus(metrics[5]).name,
                    'scaleAction': metrics[6],
                    'datetime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metrics[1]))
                }
                result.append(entry)
                
            return result
        except Exception as e:
            logger.error(f"Error getting metrics history for {node_id}: {str(e)}")
            raise


if __name__ == "__main__":
    # These should be loaded from environment variables or config in production
    CONTRACT_ADDRESS = "0x123...456"
    PRIVATE_KEY = "0xabc...def"
    
    try:
        # Initialize the audit logger
        audit_logger = AuditLogger(
            contract_address=CONTRACT_ADDRESS,
            private_key=PRIVATE_KEY,
            web3_provider_uri="http://localhost:8545",
            abi_path="blockchain/contracts/abi/AuditLogger.json"
        )
        
        # Example: Log node metrics
        tx_hash = audit_logger.log_node_metrics(
            node_id="node-1",
            memory_usage=1024,  # MB
            cpu_load=75,        # 75%
            allocated_memory=2048,  # MB
            status=NodeStatus.Normal
        )
        print(f"Metrics logged with transaction: {tx_hash}")
        
        # Example: Log a scaling action
        tx_hash = audit_logger.log_scaling_action(
            node_id="node-1",
            action="scale_up",
            reason="High CPU load detected by RL model"
        )
        print(f"Scaling action logged with transaction: {tx_hash}")
        
        # Example: Get latest metrics for a node
        latest_metrics = audit_logger.get_latest_node_metrics("node-1")
        print(f"Latest metrics: {json.dumps(latest_metrics, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in audit logger example: {str(e)}")