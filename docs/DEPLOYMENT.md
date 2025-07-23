# Atlas Code V5 Deployment Guide

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (recommended: Python 3.11)
- **pip** package manager
- **OpenRouter API Key** ([Get one here](https://openrouter.ai/))
- **4GB+ RAM** (8GB recommended for optimal performance)
- **50MB+ disk space**

### Installation Options

#### Option 1: Direct Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/atlas-code-v5.git
cd atlas-code-v5

# Install Python dependencies
pip install -r requirements.txt

# Set up API key
export OPENROUTER_API_KEY="your-api-key-here"

# Make executable
chmod +x atlas-code-v5

# Test installation
./atlas-code-v5 --version
```

#### Option 2: Virtual Environment (Isolated)

```bash
# Clone and enter directory
git clone https://github.com/your-org/atlas-code-v5.git
cd atlas-code-v5

# Create virtual environment
python -m venv atlas-env
source atlas-env/bin/activate  # On Windows: atlas-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
export OPENROUTER_API_KEY="your-api-key-here"

# Test
./atlas-code-v5 "Hello, Atlas!"
```

#### Option 3: Docker (Containerized)

```bash
# Build Docker image
docker build -t atlas-code-v5 .

# Run with API key
docker run -e OPENROUTER_API_KEY="your-key" atlas-code-v5 "write a hello world program"
```

---

## ⚙️ Configuration

### 1. API Key Setup

**Environment Variable (Recommended):**
```bash
export OPENROUTER_API_KEY="your-actual-api-key"
```

**Persistent Setup (Linux/macOS):**
```bash
echo 'export OPENROUTER_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

**Windows PowerShell:**
```powershell
$env:OPENROUTER_API_KEY="your-key"
# For persistent: setx OPENROUTER_API_KEY "your-key"
```

### 2. Configuration Files

Create `config/api_keys.json` (optional, not recommended for production):
```json
{
  "openrouter_api_key": "your-key-here"
}
```

### 3. Custom Settings

Edit `config/settings.json` to customize:
```json
{
  "user_preferences": {
    "default_language": "python",
    "preferred_tier": "standard",
    "max_budget_per_session": 2.0
  },
  "system_settings": {
    "timeout_seconds": 30,
    "log_level": "INFO"
  }
}
```

---

## 🔧 Advanced Configuration

### Model Tier Customization

Edit `config/model_tiers.json` to add custom models or adjust budgets:

```json
{
  "tiers": {
    "premium": {
      "models": [
        {
          "name": "anthropic/claude-3.5-sonnet",
          "cost_input": 0.003,
          "cost_output": 0.015
        }
      ]
    }
  },
  "budget_limits": {
    "daily_budget": 20.00,
    "session_budget": 5.00
  }
}
```

### Intent Routing Rules

Customize `config/intent_routes.json` for specific use cases:

```json
{
  "routing_rules": {
    "my_custom_intent": {
      "default_tier": "premium",
      "keywords": ["custom", "special"],
      "patterns": ["do something special"]
    }
  }
}
```

### Security Settings

Modify `config/settings.json` for code execution security:

```json
{
  "code_execution": {
    "enable_execution": true,
    "sandboxed": true,
    "timeout_seconds": 10,
    "allowed_imports": ["math", "json", "datetime"],
    "blocked_imports": ["os", "subprocess", "socket"]
  }
}
```

---

## 🏗️ Production Deployment

### System Service (Linux)

Create `/etc/systemd/system/atlas-code-v5.service`:

```ini
[Unit]
Description=Atlas Code V5 Service
After=network.target

[Service]
Type=simple
User=atlas
WorkingDirectory=/opt/atlas-code-v5
ExecStart=/opt/atlas-code-v5/atlas-code-v5 --interactive
Environment=OPENROUTER_API_KEY=your-key-here
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable atlas-code-v5
sudo systemctl start atlas-code-v5
sudo systemctl status atlas-code-v5
```

### Docker Production Setup

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

USER 1000:1000
EXPOSE 8080

CMD ["./atlas-code-v5", "--interactive"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  atlas-code-v5:
    build: .
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    ports:
      - "8080:8080"
```

Deploy:
```bash
docker-compose up -d
```

### Kubernetes Deployment

**k8s-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atlas-code-v5
spec:
  replicas: 2
  selector:
    matchLabels:
      app: atlas-code-v5
  template:
    metadata:
      labels:
        app: atlas-code-v5
    spec:
      containers:
      - name: atlas-code-v5
        image: atlas-code-v5:latest
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: atlas-secrets
              key: openrouter-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Secret
metadata:
  name: atlas-secrets
type: Opaque
data:
  openrouter-key: <base64-encoded-key>
```

Deploy:
```bash
kubectl apply -f k8s-deployment.yaml
```

---

## 📊 Monitoring & Logging

### Log Configuration

Set log level in `config/settings.json`:
```json
{
  "system_settings": {
    "log_level": "INFO",
    "enable_telemetry": true
  },
  "error_handling": {
    "error_log_file": "./logs/errors.log",
    "save_failed_requests": true
  }
}
```

### Health Checks

Built-in health check endpoint:
```bash
./atlas-code-v5 --health-check
```

### Performance Monitoring

View usage statistics:
```bash
./atlas-code-v5 --stats
```

Monitor costs:
```bash
./atlas-code-v5 --budget-status
```

### Log Analysis

Check error logs:
```bash
tail -f logs/errors.log
```

Performance logs:
```bash
cat data/performance.jsonl | jq '.'
```

---

## 🧪 Testing Deployment

### Basic Functionality Test

```bash
# Test basic query
./atlas-code-v5 "write hello world in python"

# Test file context
echo "def broken_func():" > test.py
./atlas-code-v5 --file test.py "fix this syntax error"

# Test interactive mode
./atlas-code-v5 --interactive
```

### Performance Test

```bash
# Run mock test suite
cd tests
python mock_framework.py

# Load test (if implemented)
./atlas-code-v5 --load-test --queries 100
```

### Security Test

```bash
# Test sandboxing
./atlas-code-v5 "import os; os.system('ls')"  # Should be blocked

# Test timeout
./atlas-code-v5 "while True: pass"  # Should timeout
```

---

## 🔐 Security Best Practices

### API Key Security

1. **Never commit API keys** to version control
2. **Use environment variables** in production
3. **Rotate keys regularly** (monthly recommended)
4. **Monitor API usage** for anomalies

### Code Execution Security

```json
{
  "code_execution": {
    "sandboxed": true,
    "timeout_seconds": 10,
    "max_memory_mb": 100,
    "blocked_imports": [
      "subprocess", "os", "sys", "socket", 
      "urllib", "requests", "http"
    ],
    "restricted_paths": [
      "/etc", "/usr", "/bin", "/var"
    ]
  }
}
```

### Network Security

- **Use HTTPS** for all API communications
- **Implement rate limiting** in production
- **Monitor for suspicious patterns**
- **Use firewall rules** to restrict access

---

## 📈 Scaling & Performance

### Horizontal Scaling

For high-volume deployments:

1. **Load Balancer** (nginx/HAProxy)
2. **Multiple instances** behind proxy
3. **Shared configuration** via network storage
4. **Centralized logging** (ELK stack)

### Performance Optimization

```json
{
  "system_settings": {
    "enable_caching": true,
    "cache_duration_hours": 24,
    "max_context_length": 50000
  },
  "api_configuration": {
    "rate_limits": {
      "requests_per_minute": 120,
      "tokens_per_minute": 100000
    }
  }
}
```

### Resource Limits

**Recommended specs by usage:**

| Usage Level | CPU | RAM | Storage | Max Users |
|-------------|-----|-----|---------|-----------|
| Development | 1 core | 2GB | 1GB | 1-5 |
| Small Team | 2 cores | 4GB | 5GB | 5-20 |
| Department | 4 cores | 8GB | 20GB | 20-100 |
| Enterprise | 8+ cores | 16GB+ | 100GB+ | 100+ |

---

## 🔄 Updates & Maintenance

### Version Updates

```bash
# Backup current installation
cp -r atlas-code-v5 atlas-code-v5-backup

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Test new version
./atlas-code-v5 --version
./atlas-code-v5 "test query"
```

### Database Maintenance

Clean old data:
```bash
# Clean logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete

# Compress old performance data
gzip data/performance.jsonl

# Clean memory cache
rm data/semantic_embeddings.pkl
```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh - Daily backup script

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/atlas-code-v5"

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup configuration
cp -r config/ $BACKUP_DIR/$DATE/

# Backup data
cp -r data/ $BACKUP_DIR/$DATE/

# Backup logs (last 7 days)
find logs/ -mtime -7 -exec cp {} $BACKUP_DIR/$DATE/ \;

# Compress backup
tar -czf $BACKUP_DIR/atlas-v5-$DATE.tar.gz $BACKUP_DIR/$DATE/
rm -rf $BACKUP_DIR/$DATE

echo "Backup completed: atlas-v5-$DATE.tar.gz"
```

---

## 🆘 Troubleshooting

### Common Issues

**1. API Key Not Found**
```
Error: OpenRouter API key not found
```
**Solution:** Set environment variable or check config file

**2. Import Errors**
```
ImportError: No module named 'requests'
```
**Solution:** Install dependencies: `pip install -r requirements.txt`

**3. Permission Denied**
```
PermissionError: [Errno 13] Permission denied: './atlas-code-v5'
```
**Solution:** Make executable: `chmod +x atlas-code-v5`

**4. Timeout Errors**
```
Error: Request timeout for model anthropic/claude-3.5-sonnet
```
**Solution:** Increase timeout in settings or check network

### Debug Mode

Enable detailed logging:
```bash
export ATLAS_DEBUG=1
./atlas-code-v5 --verbose "debug query"
```

### Recovery Procedures

**1. Reset Configuration**
```bash
cp config/settings.json config/settings.json.backup
git checkout config/settings.json
```

**2. Clear Cache**
```bash
rm -rf data/semantic_embeddings.pkl
rm -rf data/memory.jsonl
```

**3. Factory Reset**
```bash
git checkout .
pip install -r requirements.txt
```

---

## 📞 Support

### Self-Help Resources

- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory  
- **Test Suite**: `python tests/mock_framework.py`

### Getting Help

1. **Check logs**: `tail -f logs/errors.log`
2. **Run diagnostics**: `./atlas-code-v5 --diagnose`
3. **Test components**: `python tests/mock_framework.py`

### Reporting Issues

Include in bug reports:
- Atlas Code V5 version
- Python version
- Operating system
- Error logs
- Steps to reproduce

---

**🎉 Congratulations! Atlas Code V5 is now deployed and ready to revolutionize your coding workflow.**