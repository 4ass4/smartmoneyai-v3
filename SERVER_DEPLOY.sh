#!/bin/bash
# Скрипт для развертывания SmartMoneyAI v3 на сервере Debian

set -e  # Остановка при ошибке

echo "🚀 Начало развертывания SmartMoneyAI v3..."

# 1. Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get install -y python3 python3-pip python3-venv git

# 2. Создание директории для проекта
echo "📁 Создание директории проекта..."
PROJECT_DIR="/opt/smartmoneyai-v3"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 3. Клонирование репозитория
echo "📥 Клонирование репозитория..."
if [ -d ".git" ]; then
    echo "   Репозиторий уже существует, обновляем..."
    git pull origin main
else
    git clone https://github.com/4ass4/smartmoneyai-v3.git .
fi

# 4. Создание виртуального окружения
echo "🐍 Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 5. Установка зависимостей
echo "📚 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Создание .env файла (если не существует)
echo "⚙️ Настройка .env файла..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "   ✅ Файл .env создан из env.example"
        echo "   ⚠️ ВАЖНО: Отредактируйте .env и заполните все секретные ключи!"
        echo "   nano $PROJECT_DIR/.env"
    else
        echo "   ❌ Файл env.example не найден!"
    fi
else
    echo "   ✅ Файл .env уже существует"
fi

# 7. Создание директорий для логов и данных
echo "📂 Создание директорий..."
mkdir -p logs
mkdir -p data/cache
mkdir -p data/samples

# 8. Создание systemd службы
echo "🔧 Создание systemd службы..."
SERVICE_FILE="/etc/systemd/system/smartmoneyai.service"
cat > $SERVICE_FILE << EOF
[Unit]
Description=SmartMoneyAI v3 Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 9. Перезагрузка systemd и запуск службы
echo "🔄 Настройка службы..."
systemctl daemon-reload
systemctl enable smartmoneyai.service

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Отредактируйте .env файл: nano $PROJECT_DIR/.env"
echo "   2. Запустите службу: systemctl start smartmoneyai"
echo "   3. Проверьте статус: systemctl status smartmoneyai"
echo "   4. Просмотр логов: journalctl -u smartmoneyai -f"
echo ""
