## 🚀 Step 1: Quick Docker Setup

```bash
# Run the environment setup
./docker_env_setup.sh

# Run the Docker manager setup
./docker_manager.sh setup
```

This will:
- ✅ **Create optimized Dockerfile** for Python 3.13
- ✅ **Set up docker-compose** with all services
- ✅ **Configure nginx reverse proxy**
- ✅ **Copy your Earth Engine credentials** into containers
- ✅ **Build the Docker image** with all dependencies

## 🌪️ Step 1: Start Your Containerized App

```bash
# Start just the dust predictor
./docker_manager.sh start

# OR start with full stack (nginx + monitoring)
./docker_manager.sh start-full
```

## 📊 Step 3: Access Your Dockerized Dashboard

Your app will be available at:
- 🌐 **Direct access**: http://localhost:5001
- 🌐 **Via nginx proxy**: http://localhost:80 (if using start-full)

## 🔧 Docker Management Commands

```bash
# Check status and health
./docker_manager.sh status

# View real-time logs
./docker_manager.sh logs

# Restart the application
./docker_manager.sh restart

# Stop the application
./docker_manager.sh stop

# Update the application (rebuild and restart)
./docker_manager.sh update

# Create backup of data
./docker_manager.sh backup

# Clean up containers and images
./docker_manager.sh cleanup
```
