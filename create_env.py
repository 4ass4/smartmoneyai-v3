"""
Скрипт для создания .env файла из шаблона env.example
ВНИМАНИЕ: Этот скрипт копирует env.example в .env
Вы должны вручную заполнить все секретные ключи в .env файле!
"""
from pathlib import Path
import shutil

def create_env_from_example():
    """Создает .env файл из env.example"""
    example_path = Path('env.example')
    env_path = Path('.env')
    
    if not example_path.exists():
        print(f"❌ Файл {example_path} не найден!")
        print("Создайте файл env.example с шаблоном настроек")
        return
    
    # Копируем пример
    shutil.copy(example_path, env_path)
    
    print(f"✅ Файл .env создан из {example_path}")
    print(f"📝 ВАЖНО: Заполните все секретные ключи в файле .env!")
    print(f"   - TELEGRAM_BOT_TOKEN")
    print(f"   - BINGX_API_KEY и BINGX_API_SECRET")
    print(f"   - OPENAI_API_KEY (если используется)")
    print(f"   - И другие необходимые параметры")

if __name__ == "__main__":
    create_env_from_example()

