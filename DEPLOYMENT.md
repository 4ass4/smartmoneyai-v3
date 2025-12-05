# 🚀 РАЗВЕРТЫВАНИЕ SmartMoneyAI v3 НА СЕРВЕРЕ

## 📋 ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ

### На сервере должны быть установлены:
- Python 3.8+
- pip
- git
- systemd (для Linux) или службы Windows (для Windows Server)

---

## 🔧 ШАГ 1: ПОДКЛЮЧЕНИЕ К СЕРВЕРУ

### Linux (SSH):
```bash
ssh user@your-server-ip
```

### Windows Server:
Подключитесь через Remote Desktop или PowerShell Remoting

---

## 📥 ШАГ 2: КЛОНИРОВАНИЕ РЕПОЗИТОРИЯ

```bash
# Перейдите в нужную директорию
cd /opt  # или /home/user или другая директория

# Клонируйте репозиторий
git clone https://github.com/your-username/smartmoneyai-v3.git
cd smartmoneyai-v3
```

---

## 🐍 ШАГ 3: УСТАНОВКА ЗАВИСИМОСТЕЙ

```bash
# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ ШАГ 4: НАСТРОЙКА КОНФИГУРАЦИИ

### Создайте файл `.env`:

```bash
# Скопируйте пример
cp .env.example .env

# Отредактируйте .env файл
nano .env  # или vim .env
```

### Заполните все необходимые параметры:
- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
- `TELEGRAM_ADMIN_ID` - ваш Telegram ID
- `BINGX_API_KEY` - API ключ BingX
- `BINGX_API_SECRET` - секретный ключ BingX
- Остальные параметры по необходимости

---

## 🧪 ШАГ 5: ТЕСТИРОВАНИЕ

```bash
# Проверьте подключение к API
python test_api.py

# Проверьте SVD API
python test_svd_api.py

# Проверьте полный анализ
python test_analysis.py
```

---

## 🔄 ШАГ 6: ЗАПУСК КАК СЛУЖБЫ

### Linux (systemd):

#### Создайте файл службы:
```bash
sudo nano /etc/systemd/system/smartmoneyai.service
```

#### Содержимое файла:
```ini
[Unit]
Description=SmartMoneyAI v3 Trading Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/smartmoneyai-v3
Environment="PATH=/opt/smartmoneyai-v3/venv/bin"
ExecStart=/opt/smartmoneyai-v3/venv/bin/python /opt/smartmoneyai-v3/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Активируйте и запустите службу:
```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable smartmoneyai.service

# Запустите службу
sudo systemctl start smartmoneyai.service

# Проверьте статус
sudo systemctl status smartmoneyai.service

# Просмотр логов
sudo journalctl -u smartmoneyai.service -f
```

### Windows (NSSM - Non-Sucking Service Manager):

#### Установите NSSM:
```powershell
# Скачайте NSSM с https://nssm.cc/download
# Распакуйте и добавьте в PATH
```

#### Создайте службу:
```powershell
nssm install SmartMoneyAI "C:\path\to\venv\Scripts\python.exe" "C:\path\to\smartmoneyai-v3\main.py"
nssm set SmartMoneyAI AppDirectory "C:\path\to\smartmoneyai-v3"
nssm set SmartMoneyAI DisplayName "SmartMoneyAI v3"
nssm set SmartMoneyAI Description "Smart Money Analysis Bot"
nssm set SmartMoneyAI Start SERVICE_AUTO_START
nssm start SmartMoneyAI
```

### Windows (Task Scheduler):

1. Откройте Task Scheduler
2. Create Basic Task
3. Название: SmartMoneyAI
4. Trigger: When the computer starts
5. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\smartmoneyai-v3`

---

## 📊 ШАГ 7: МОНИТОРИНГ

### Просмотр логов:

#### Linux:
```bash
# Логи systemd
sudo journalctl -u smartmoneyai.service -f

# Логи приложения
tail -f logs/smartmoney.log
```

#### Windows:
```powershell
# Логи приложения
Get-Content logs\smartmoney.log -Wait -Tail 50
```

---

## 🔄 ШАГ 8: ОБНОВЛЕНИЕ

```bash
# Остановите службу
sudo systemctl stop smartmoneyai.service  # Linux
# или
Stop-Service SmartMoneyAI  # Windows

# Обновите код
git pull origin main

# Перезапустите службу
sudo systemctl start smartmoneyai.service  # Linux
# или
Start-Service SmartMoneyAI  # Windows
```

---

## 🛠️ УСТРАНЕНИЕ ПРОБЛЕМ

### Бот не запускается:
1. Проверьте `.env` файл - все ли токены заполнены
2. Проверьте логи: `logs/smartmoney.log`
3. Проверьте подключение к интернету
4. Проверьте доступность BingX API

### Ошибки API:
1. Проверьте API ключи в `.env`
2. Проверьте лимиты API BingX
3. Проверьте формат символа (должен быть BTC-USDT)

### Служба не запускается:
1. Проверьте права доступа к файлам
2. Проверьте путь к Python в службе
3. Проверьте логи systemd: `sudo journalctl -u smartmoneyai.service`

---

## 🔐 БЕЗОПАСНОСТЬ

1. **НЕ коммитьте `.env` файл в git!**
2. Используйте сильные пароли для API ключей
3. Ограничьте доступ к серверу (firewall)
4. Регулярно обновляйте зависимости: `pip install --upgrade -r requirements.txt`

---

## 📝 ПРОВЕРКА РАБОТЫ

После запуска проверьте:

1. **Telegram бот отвечает:**
   - Отправьте `/start` боту
   - Отправьте `/status` - должен показать статус

2. **Анализ работает:**
   - Отправьте `/signal` - должен вернуть сигнал
   - Отправьте `/analysis` - должен вернуть глубокий анализ

3. **Автоматические сигналы:**
   - Подождите несколько минут
   - Должны прийти автоматические сигналы (если есть)

---

## 🎯 ГОТОВО!

Система развернута и работает! 🎉

Для управления используйте:
- `systemctl start/stop/restart smartmoneyai.service` (Linux)
- Или через Task Scheduler / Services (Windows)

