FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the node code
COPY node.py .

# Expose the port
EXPOSE 8080

# Set environment variables
ENV NODE_ID=db-node-1
ENV MEMORY_LIMIT_MB=2048

# Run the application
CMD ["python", "node.py"]