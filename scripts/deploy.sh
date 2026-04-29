#!/bin/bash
# Deploy script - transfers project to Raspberry Pi Zero W

PI_USER="dani"
PI_HOST="192.168.0.204"
PI_PASS="26021980"
PI_PATH="/home/dani/reloj_despertador"

echo "=== Deploying Reloj Despertador ==="

# Create directories on Pi
sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_HOST "mkdir -p $PI_PATH/src/{hardware,graphics/icons,ui,services,assets/fonts,assets/sounds} $PI_PATH/config $PI_PATH/scripts $PI_PATH/tests $PI_PATH/docs"

# Transfer files
echo "Transferring files..."
sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=no -r src/* $PI_USER@$PI_HOST:$PI_PATH/src/
sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=no config/* $PI_USER@$PI_HOST:$PI_PATH/config/
sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=no scripts/* $PI_USER@$PI_HOST:$PI_PATH/scripts/
sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=no requirements.txt $PI_USER@$PI_HOST:$PI_PATH/

# Install dependencies
echo "Installing Python dependencies..."
sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=no $PI_USER@$PI_HOST "pip3 install -r $PI_PATH/requirements.txt"

echo "=== Deploy complete ==="
echo "To run: ssh $PI_USER@$PI_HOST 'cd $PI_PATH && python3 src/main.py'"
