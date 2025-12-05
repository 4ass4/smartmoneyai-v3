# 🔧 Настройка .env файла

## Быстрый старт

1. **Скопируйте файл `env.example` в `.env`**:
   ```bash
   # Windows
   copy env.example .env
   
   # Linux/Mac
   cp env.example .env
   ```

2. **Откройте `.env` и заполните все значения**

## Важные настройки

### Telegram Bot
- `TELEGRAM_BOT_TOKEN` - токен от @BotFather
- `TELEGRAM_ADMIN_ID` - ваш ID от @userinfobot
- `TELEGRAM_CHAT_ID` - ID чата (если не указан, используется ADMIN_ID)

### BingX API
- `BINGX_API_KEY` - ваш API ключ
- `BINGX_API_SECRET` - ваш Secret ключ

### Торговые настройки
- `DEFAULT_SYMBOLS` - символ для торговли (например, BTCUSDT)
- `UPDATE_INTERVAL` - интервал обновления в секундах (180 = 3 минуты)
- `KLINE_INTERVAL` - таймфрейм для анализа (15m, 1h, 4h, 1D)
- `KLINE_LIMIT` - количество свечей (максимум 100 для BingX)

## Пример заполненного .env

```env
TELEGRAM_BOT_TOKEN=6652525680:AAGmA7o4mlo8xBHSe8teD56zwETBd3RMBUQ
TELEGRAM_ADMIN_ID=1013787473
TELEGRAM_CHAT_ID=1013787473

EXCHANGE=BINGX

BINGX_API_KEY=ваш_ключ
BINGX_API_SECRET=ваш_secret

DEFAULT_SYMBOLS=BTCUSDT
UPDATE_INTERVAL=180
KLINE_INTERVAL=15m
KLINE_LIMIT=100
```

## ⚠️ Важно

- **НЕ коммитьте `.env` файл в Git!** Он содержит секретные данные
- Файл `env.example` - это шаблон без реальных значений
- Все реальные токены и ключи должны быть только в `.env`

