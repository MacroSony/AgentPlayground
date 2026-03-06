# agent/Dockerfile
FROM python:3.12-slim

# Install basic system dependencies the agent might want to use
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m -u 1000 agentuser
USER agentuser

# Pre-configure Git for the agent
RUN git config --global init.defaultBranch main

# Add GitHub to known_hosts to avoid interactive prompts
RUN mkdir -p /home/agentuser/.ssh \
    && ssh-keyscan github.com >> /home/agentuser/.ssh/known_hosts

WORKDIR /app

# Copy the agent's initial brain (the loop)
COPY --chown=agentuser:agentuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --user

COPY --chown=agentuser:agentuser loop.py .
COPY --chown=agentuser:agentuser supervisor.py .

# The agent's loop will start here
CMD ["python", "supervisor.py"]
