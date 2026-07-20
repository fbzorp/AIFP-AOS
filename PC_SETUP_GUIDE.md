# PC Setup Guide — AiFinPay AOS Development

Complete step-by-step to get your PC ready for the 14-day project.

---

## Step 0: Check Your System

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| Storage | 20 GB free | 50 GB free |
| OS | Windows 10/11, macOS 12+, or Linux | Ubuntu 22.04 LTS |
| CPU | 4 cores | 8 cores |
| Internet | Stable connection | Broadband |

### Verify Your Specs

**Windows:**
```powershell
# Press Win + R, type: msinfo32
# Or in PowerShell:
Get-ComputerInfo | Select TotalPhysicalMemory, CsProcessors
```

**macOS:**
```bash
# Click Apple menu > About This Mac
# Or in Terminal:
system_profiler SPHardwareDataType | grep "Memory\|Processor"
```

**Linux:**
```bash
free -h                    # RAM
cat /proc/cpuinfo | grep "model name" | head -1   # CPU
df -h /                    # Disk space
```

---

## Step 1: Install Git

**Windows:**
```powershell
# Download from https://git-scm.com/download/win
# Or use winget:
winget install --id Git.Git -e --source winget
```

**macOS:**
```bash
# Install Xcode Command Line Tools (includes git)
xcode-select --install

# Or use Homebrew:
brew install git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install -y git
```

**Verify:**
```bash
git --version
# Should show: git version 2.40+ (any recent version works)
```

**Configure Git:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git config --global init.defaultBranch main
```

---

## Step 2: Install Docker & Docker Compose

Docker runs your entire stack (PostgreSQL, Redis, API, Worker, Frontend) in isolated containers.

### Windows

```powershell
# 1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
# 2. Run installer
# 3. During setup, check "Use WSL 2 instead of Hyper-V" (recommended)
# 4. Restart when prompted

# 5. In PowerShell (Admin), enable WSL 2:
wsl --install
# Restart PC

# 6. Open Docker Desktop, go to Settings:
#    - General: Start Docker Desktop when you log in
#    - Resources > WSL Integration: Enable integration with your default WSL distro
#    - Apply & Restart
```

### macOS

```bash
# Option A: Docker Desktop (easiest)
# Download: https://www.docker.com/products/docker-desktop
# Drag to Applications, open, grant permissions

# Option B: Homebrew (lighter, no GUI)
brew install --cask docker
# Or for CLI-only:
brew install docker docker-compose
```

### Linux (Ubuntu/Debian)

```bash
# Remove old versions if any
sudo apt remove docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (run without sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### Verify Docker

```bash
docker --version
# Docker version 24.0+, build xxx

docker compose version
# Docker Compose version v2.20+

# Test with hello-world
docker run hello-world
# Should print: "Hello from Docker!"
```

---

## Step 3: Install Python 3.11+

**Windows:**
```powershell
# Download from https://www.python.org/downloads/
# Check "Add Python to PATH" during install
# Or use winget:
winget install Python.Python.3.11
```

**macOS:**
```bash
brew install python@3.11
# Add to PATH:
echo 'export PATH="/opt/homebrew/opt/python@3.11/libexec/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Linux:**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Make python3.11 the default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

**Verify:**
```bash
python3 --version
# Python 3.11.x

pip3 --version
# pip 23.x+
```

---

## Step 4: Install Node.js 20+ (for Frontend)

**Windows:**
```powershell
# Download from https://nodejs.org/ (LTS version)
# Or use winget:
winget install OpenJS.NodeJS.LTS
```

**macOS:**
```bash
brew install node@20
echo 'export PATH="/opt/homebrew/opt/node@20/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Linux:**
```bash
# Using NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

**Verify:**
```bash
node --version
# v20.x.x

npm --version
# 10.x.x
```

---

## Step 5: Install Aider (AI Coding Assistant)

```bash
# Install the installer
pip install aider-install

# Run the installer
aider-install

# Verify
aider --version
# aider 0.60+
```

**Configure API Key:**
```bash
# Create .env file in your home directory or project root
# Get DeepSeek API key from: https://platform.deepseek.com/

echo 'DEEPSEEK_API_KEY=sk-your-key-here' > ~/.aider.env

# Or set directly:
export DEEPSEEK_API_KEY=sk-your-key-here
```

---

## Step 6: Install OpenHands (Optional — for Complex Tasks)

```bash
# Pull the Docker image
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.18-nikolaik
docker pull docker.all-hands.dev/all-hands-ai/openhands:0.18

# Create a launch script
mkdir -p ~/bin
cat > ~/bin/openhands << 'EOF'
#!/bin/bash
WORKSPACE=${1:-$(pwd)}
docker run -it --rm \
  -e SANDBOX_USER_ID=$(id -u) \
  -e WORKSPACE_MOUNT_PATH=$WORKSPACE \
  -v $WORKSPACE:/opt/workspace_base \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  --name openhands-app \
  docker.all-hands.dev/all-hands-ai/openhands:0.18
EOF
chmod +x ~/bin/openhands

# Add to PATH
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc on macOS
source ~/.bashrc
```

---

## Step 7: Clone the Repository

```bash
# Create projects directory
mkdir -p ~/projects
cd ~/projects

# Clone your repo (replace with actual URL)
git clone https://github.com/your-org/aifp-aos.git
cd aifp-aos

# Verify you're on main branch
git branch
# * main
```

---

## Step 8: Create Environment File

```bash
# Copy template
cp .env.template .env

# Edit .env with your values
# Use nano, vim, or any text editor
nano .env
```

**Required variables:**
```env
# Database (local Docker)
DATABASE_URL=postgresql+asyncpg://aifp:devpassword@localhost:5432/aifp_dev

# Redis (local Docker)
REDIS_URL=redis://localhost:6379/0

# API Keys (for AI agents)
DEEPSEEK_API_KEY=sk-your-key-here
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# OPENAI_API_KEY=sk-your-key-here

# AiFinPay SDK
AIFP_API_KEY=your-aifp-key
AIFP_BASE_URL=https://api.aifinpay.com

# Social Media (for publishing agent)
# X_API_KEY=...
# X_API_SECRET=...
# TELEGRAM_BOT_TOKEN=...

# Environment
ENV=development
LOG_LEVEL=INFO
```

---

## Step 9: Start the Development Stack

```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up -d

# Watch logs
docker-compose -f docker-compose.dev.yml logs -f

# Check all services are running
docker ps

# Expected output:
# CONTAINER ID   IMAGE              STATUS          PORTS
# xxxx           aifp-aos-api       Up 10 seconds   0.0.0.0:8000->8000/tcp
# xxxx           aifp-aos-worker    Up 10 seconds
# xxxx           postgres:15        Up 10 seconds   0.0.0.0:5432->5432/tcp
# xxxx           redis:7            Up 10 seconds   0.0.0.0:6379->6379/tcp
# xxxx           aifp-aos-frontend  Up 10 seconds   0.0.0.0:3000->3000/tcp
```

---

## Step 10: Run Database Migrations

```bash
# Enter the API container
docker-compose -f docker-compose.dev.yml exec api bash

# Inside container:
alembic upgrade head

# Exit
exit
```

---

## Step 11: Verify Everything Works

### Test API
```bash
# In browser or curl:
curl http://localhost:8000/health
# {"status": "ok", "version": "0.1.0"}

# API docs:
# Open http://localhost:8000/docs (Swagger UI)
# Open http://localhost:8000/redoc (ReDoc)
```

### Test Frontend
```bash
# Open http://localhost:3000
# Should show the AiFinPay AOS dashboard
```

### Test Database
```bash
docker-compose -f docker-compose.dev.yml exec postgres psql -U aifp -d aifp_dev -c "\dt"
# Should list all tables
```

### Test Redis
```bash
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
# PONG
```

---

## Step 12: Run Tests

```bash
# Run all tests
docker-compose -f docker-compose.dev.yml exec api pytest tests/ -v

# Run specific agent tests
docker-compose -f docker-compose.dev.yml exec api pytest tests/agents/test_growth_orchestrator.py -v
```

---

## Daily Development Commands

```bash
# Start the day
cd ~/projects/aifp-aos
git pull origin main
docker-compose -f docker-compose.dev.yml up -d

# Code with Aider
aider --config .aider.conf.yml

# Check logs
docker-compose -f docker-compose.dev.yml logs -f api
docker-compose -f docker-compose.dev.yml logs -f worker

# Run tests
docker-compose -f docker-compose.dev.yml exec api pytest tests/ -v

# Stop for the day
docker-compose -f docker-compose.dev.yml down

# Or keep running in background
docker-compose -f docker-compose.dev.yml up -d
```

---

## Troubleshooting

### Docker won't start (Windows)
```powershell
# Ensure WSL 2 is default
wsl --set-default-version 2

# Update WSL
wsl --update

# Restart Docker Desktop
```

### Port already in use
```bash
# Find what's using port 8000
sudo lsof -i :8000
# Kill it: kill -9 <PID>

# Or change ports in docker-compose.dev.yml
```

### Permission denied (Linux)
```bash
# Re-add to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo (not recommended)
sudo docker-compose -f docker-compose.dev.yml up -d
```

### Out of memory during build
```bash
# Increase Docker memory limit:
# Docker Desktop > Settings > Resources > Memory > 4 GB+

# Or use --build-arg to limit parallel jobs:
docker-compose -f docker-compose.dev.yml build --parallel 1
```

### Aider can't find API key
```bash
# Check it's set:
echo $DEEPSEEK_API_KEY

# If empty, source your .env:
export $(grep -v '^#' .env | xargs)

# Or add to shell profile:
echo 'export DEEPSEEK_API_KEY=sk-your-key' >> ~/.bashrc
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Start stack | `docker-compose -f docker-compose.dev.yml up -d` |
| Stop stack | `docker-compose -f docker-compose.dev.yml down` |
| View logs | `docker-compose -f docker-compose.dev.yml logs -f` |
| Restart service | `docker-compose -f docker-compose.dev.yml restart api` |
| Run migrations | `docker-compose exec api alembic upgrade head` |
| Run tests | `docker-compose exec api pytest tests/ -v` |
| Enter container | `docker-compose exec api bash` |
| Check DB | `docker-compose exec postgres psql -U aifp -d aifp_dev` |
| Check Redis | `docker-compose exec redis redis-cli` |
| Code with AI | `aider --config .aider.conf.yml` |
| OpenHands | `openhands ~/projects/aifp-aos` |
| Git status | `git status` |
| Commit & push | `git add . && git commit -m "feat: ..." && git push` |

---

## What You Have Now

✅ Git configured  
✅ Docker + Docker Compose installed  
✅ Python 3.11+ installed  
✅ Node.js 20+ installed  
✅ Aider (AI coding) installed  
✅ OpenHands (complex tasks) installed  
✅ Repository cloned  
✅ Environment file configured  
✅ Full stack running locally  
✅ Database migrated  
✅ All services verified  

**You're ready to start Day 1.**
