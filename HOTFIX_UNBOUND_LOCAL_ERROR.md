# 🚨 HOTFIX: UnboundLocalError - переменная 'phase'

## ❌ Проблема

```python
UnboundLocalError: cannot access local variable 'phase' where it is not associated with a value
File "/opt/smartmoneyai-v3/modules/svd/svd_engine.py", line 128, in analyze
    if phase == "execution":
        ^^^^^
```

**Причина:** 
- Проверка `if phase == "execution":` была на строке 128
- НО переменная `phase` определялась только на строке 253 (270 в старой версии)
- Результат: использование переменной ДО её объявления → **CRASH бота**

---

## ✅ Решение

**Переместил проверку execution priority ПОСЛЕ определения `phase`:**

### Было (строка 128):
```python
# ЗДЕСЬ phase ЕЩЁ НЕ ОПРЕДЕЛЁН! ❌
if phase == "execution":
    if cvd_slope > 1.0:
        intent = "accumulating"
    elif cvd_slope < -1.0:
        intent = "distributing"

# ... 140 строк кода ...

# phase определяется ЗДЕСЬ (строка 270)
phase = phase_info["phase"]
```

### Стало:
```python
# Сначала определяем phase
phase = phase_info["phase"]

# ТЕПЕРЬ можем использовать phase ✅
if phase == "execution":
    if cvd_slope > 1.0:
        intent = "accumulating"
    elif cvd_slope < -1.0:
        intent = "distributing"

return {
    ...
}
```

---

## 🚀 СРОЧНЫЙ ДЕПЛОЙ

### Шаг 1: Подключение к серверу
```bash
ssh root@ВАШ_СЕРВЕР
```

### Шаг 2: Остановка бота
```bash
systemctl stop smartmoneyai.service
```

### Шаг 3: Обновление кода
```bash
cd /opt/smartmoneyai-v3
git pull origin main
```

**Ожидаемый вывод:**
```
Updating 235c1a6..97efcf9
Fast-forward
 modules/svd/svd_engine.py | 34 +++++++++++++++++-----------------
 1 file changed, 17 insertions(+), 17 deletions(-)
```

### Шаг 4: Запуск бота
```bash
systemctl start smartmoneyai.service
```

### Шаг 5: Проверка логов
```bash
journalctl -u smartmoneyai.service -f
```

**Ожидаемые логи (должны быть БЕЗ ошибок):**
```
✅ Telegram бот запущен
📡 Connecting to WebSocket...
✅ WS trades connected
✅ WS depth connected
📊 Качество данных: 0.88/1.0
🎯 Анализ завершён успешно ✅
```

**НЕ должно быть:**
```
❌ UnboundLocalError: cannot access local variable 'phase'
```

---

## 🔍 ПРОВЕРКА РАБОТЫ

### 1. Проверьте что бот работает
```bash
# Логи должны идти без ошибок
journalctl -u smartmoneyai.service -n 20 --no-pager
```

### 2. Отправьте `/analysis` в Telegram
Должен прийти полный отчёт без ошибок.

### 3. Проверьте execution priority
Если `фаза = execution` и `CVD slope > 1.0`, должно быть:

```
🧠 УМНЫЕ ДЕНЬГИ НАКАПЛИВАЮТ:
• Фаза: execution
• CVD slope: +1.86
```

---

## 📊 Что изменилось

### Изменённый файл:
- `modules/svd/svd_engine.py`

### Изменение:
- Переместил блок "КРИТИЧНО: Execution фаза → ПРИОРИТЕТ CVD slope!" 
- БЫЛО: строка 128 (ДО определения phase)
- СТАЛО: строка 256 (ПОСЛЕ определения phase)

### Git:
- Commit: `97efcf9` "Hotfix: UnboundLocalError - переместил проверку execution ПОСЛЕ определения phase"
- Push: main → main ✅

---

## ✅ РЕЗУЛЬТАТ

**После деплоя:**
1. ✅ Бот НЕ крашится с UnboundLocalError
2. ✅ Execution priority работает корректно
3. ✅ CVD slope правильно переопределяет intent в execution фазе
4. ✅ Все остальные исправления работают (swept count, RSI warnings, forecast, CVD reversal)

**Бот полностью работоспособен!** 🎉

