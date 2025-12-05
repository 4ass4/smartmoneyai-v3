# bot/notifications.py

import logging
from .formatting.signal_formatter import format_signal

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Менеджер отправки уведомлений в Telegram
    """

    def __init__(self, config):
        self.config = config
        self.bot = None  # Будет инициализирован при запуске
        # Используем TELEGRAM_CHAT_ID или TELEGRAM_ADMIN_ID как fallback
        self.chat_id = getattr(config, 'TELEGRAM_CHAT_ID', None) or getattr(config, 'TELEGRAM_ADMIN_ID', None)

    def set_bot(self, bot):
        """Установка бота"""
        self.bot = bot

    async def send_signal(self, signal_data, structure_data=None, liquidity_data=None, 
                         svd_data=None, ta_data=None, current_price=None):
        """
        Отправка сигнала в Telegram с детальными объяснениями
        
        Args:
            signal_data: данные сигнала от DecisionEngine
            structure_data: данные структуры рынка (опционально)
            liquidity_data: данные ликвидности (опционально)
            svd_data: данные SVD (опционально)
            ta_data: данные TA (опционально)
            current_price: текущая цена (опционально)
        """
        if not self.bot or not self.chat_id:
            logger.warning("Бот или chat_id не настроены")
            return

        try:
            message = format_signal(
                signal_data,
                structure_data=structure_data,
                liquidity_data=liquidity_data,
                svd_data=svd_data,
                ta_data=ta_data,
                current_price=current_price
            )
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("Сигнал отправлен в Telegram")
        except Exception as e:
            logger.error(f"Ошибка отправки сигнала: {e}", exc_info=True)

    async def send_alert(self, message):
        """
        Отправка произвольного уведомления
        
        Args:
            message: текст сообщения
        """
        if not self.bot or not self.chat_id:
            return

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

