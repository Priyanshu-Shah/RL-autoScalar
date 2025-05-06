import os
import time
import json
import random
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Node2')

# Configuration
NODE_ID = os.environ.get("NODE_ID", "db-node-1")
MEMORY_LIMIT_MB = int(os.environ.get("MEMORY_LIMIT_MB", "2048"))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "nodeId": NODE_ID})

@app.route('/metrics', methods=['GET'])
def metrics():
    """Return hardcoded metrics"""
    # Simulate some randomness for realism
    cpu_variation = random.uniform(-10, 10)
    memory_variation = random.uniform(-100, 100)
    
    metrics = {
        "nodeId": NODE_ID,
        "memoryUsage": 1024 + memory_variation,  # MB
        "cpuLoad": 60 + cpu_variation,  # percentage
        "allocatedMemory": MEMORY_LIMIT_MB,
        "status": "Normal",
        "timestamp": time.time()
    }
    
    logger.info(f"Reporting metrics: {json.dumps(metrics)}")
    return jsonify(metrics)

if __name__ == "__main__":
    logger.info(f"Starting Database Node {NODE_ID}")
    app.run(host='0.0.0.0', port=8080)