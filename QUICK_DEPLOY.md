# 🚀 БЫСТРОЕ РАЗВЕРТЫВАНИЕ НА СЕРВЕРЕ DEBIAN

## 📋 Команды для выполнения на сервере

### Вариант 1: Автоматический (рекомендуется)

```bash
# Скачайте и выполните скрипт развертывания
cd /opt
git clone https://github.com/4ass4/smartmoneyai-v3.git smartmoneyai-v3
cd smartmoneyai-v3
chmod +x SERVER_DEPLOY.sh
./SERVER_DEPLOY.sh
```

### Вариант 2: Ручной (пошагово)

#### 1. Установка зависимостей системы
```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv git
```

#### 2. Клонирование репозитория
```bash
cd /opt
git clone https://github.com/4ass4/smartmoneyai-v3.git
cd smartmoneyai-v3
```

#### 3. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 4. Установка Python зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Настройка .env файла
```bash
cp env.example .env
nano .env
# Заполните все секретные ключи:
# - TELEGRAM_BOT_TOKEN
# - BINGX_API_KEY
# - BINGX_API_SECRET
# - И другие параметры
```

#### 6. Создание директорий
```bash
mkdir -p logs data/cache data/samples
```

#### 7. Создание systemd службы
```bash
cat > /etc/systemd/system/smartmoneyai.service << 'EOF'
[Unit]
Description=SmartMoneyAI v3 Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/smartmoneyai-v3
Environment="PATH=/opt/smartmoneyai-v3/venv/bin"
ExecStart=/opt/smartmoneyai-v3/venv/bin/python /opt/smartmoneyai-v3/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

#### 8. Запуск службы
```bash
systemctl daemon-reload
systemctl enable smartmoneyai.service
systemctl start smartmoneyai.service
```

#### 9. Проверка статуса
```bash
systemctl status smartmoneyai.service
```

---

## 📊 УПРАВЛЕНИЕ СЛУЖБОЙ

### Просмотр статуса
```bash
systemctl status smartmoneyai.service
```

### Просмотр логов
```bash
# В реальном времени
journalctl -u smartmoneyai.service -f

# Последние 100 строк
journalctl -u smartmoneyai.service -n 100

# Логи приложения
tail -f /opt/smartmoneyai-v3/logs/smartmoney.log
```

### Управление службой
```bash
# Запуск
systemctl start smartmoneyai.service

# Остановка
systemctl stop smartmoneyai.service

# Перезапуск
systemctl restart smartmoneyai.service

# Отключение автозапуска
systemctl disable smartmoneyai.service
```

---

## 🔧 ОБНОВЛЕНИЕ

```bash
cd /opt/smartmoneyai-v3
systemctl stop smartmoneyai.service
git pull origin main
source venv/bin/activate
pip install --upgrade -r requirements.txt
systemctl start smartmoneyai.service
```

---

## 🐛 УСТРАНЕНИЕ ПРОБЛЕМ

### Служба не запускается
```bash
# Проверьте логи
journalctl -u smartmoneyai.service -n 50

# Проверьте .env файл
cat /opt/smartmoneyai-v3/.env

# Проверьте права доступа
ls -la /opt/smartmoneyai-v3/
```

### Ошибки Python
```bash
# Активируйте окружение и проверьте
cd /opt/smartmoneyai-v3
source venv/bin/activate
python main.py
```

### Проблемы с API
```bash
# Проверьте подключение
curl https://open-api.bingx.com/openApi/swap/v2/quote/klines?symbol=BTC-USDT&interval=15m&limit=10
```

---

## ✅ ПРОВЕРКА РАБОТЫ

1. **Проверьте статус службы:**
   ```bash
   systemctl status smartmoneyai.service
   ```

2. **Проверьте логи:**
   ```bash
   journalctl -u smartmoneyai.service -f
   ```

3. **Проверьте Telegram бота:**
   - Отправьте `/start` боту
   - Отправьте `/status` - должен ответить
   - Отправьте `/signal` - должен вернуть анализ

---

## 🔐 БЕЗОПАСНОСТЬ

1. **Не храните .env в git** (уже в .gitignore)
2. **Ограничьте доступ к .env:**
   ```bash
   chmod 600 /opt/smartmoneyai-v3/.env
   ```
3. **Используйте firewall:**
   ```bash
   ufw allow 22/tcp  # SSH
   ufw enable
   ```

---

Готово! 🎉

