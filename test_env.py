"""
Тестовый скрипт для проверки загрузки .env файла
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# Пробуем разные способы загрузки
env_path = Path('.env')
print(f"Путь к .env: {env_path.absolute()}")
print(f"Файл существует: {env_path.exists()}")

if env_path.exists():
    print(f"Размер файла: {env_path.stat().st_size} байт")
    
    # Загружаем
    result = load_dotenv(dotenv_path=env_path, override=True)
    print(f"Результат load_dotenv: {result}")
    
    # Проверяем переменные
    print("\n=== ПРОВЕРКА ПЕРЕМЕННЫХ ===")
    vars_to_check = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_ADMIN_ID',
        'TELEGRAM_CHAT_ID',
        'BINGX_API_KEY',
        'BINGX_API_SECRET',
        'DEFAULT_SYMBOLS',
        'KLINE_INTERVAL'
    ]
    
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            # Показываем только первые 20 символов для безопасности
            display = value[:20] + '...' if len(value) > 20 else value
            print(f"✅ {var}: {display}")
        else:
            print(f"❌ {var}: NOT SET")
    
    # Показываем все переменные окружения, начинающиеся с TELEGRAM или BINGX
    print("\n=== ВСЕ ПЕРЕМЕННЫЕ С TELEGRAM/BINGX ===")
    for key, value in os.environ.items():
        if 'TELEGRAM' in key or 'BINGX' in key:
            display = value[:20] + '...' if len(value) > 20 else value
            print(f"{key}: {display}")
else:
    print("❌ Файл .env не найден!")

