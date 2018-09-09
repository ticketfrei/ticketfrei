from bot import Bot
import logging
from report import Report
from twx.botapi import TelegramBot as Telegram


logger = logging.getLogger(__name__)


class TelegramBot(Bot):
    def crawl(self, user):
        tb = Telegram(user.get_telegram_credentials())
        updates = tb.get_updates().wait()
        reports = []
        for update in updates:
            if update.message.text.lower() == "/start":
                user.add_telegram_subscribers(update.message.sender.id)
                tb.send_message(update.message.sender.id, "You are now \
                        subscribed to report notifications.")
                #TODO: /start message should be set in frontend
            elif update.message.text.lower() == "/stop":
                user.remove_telegram_subscribers(update.message.sender.id)
                tb.send_message(update.message.sender.id, "You are now \
                        unsubscribed from report notifications.")
                #TODO: /stop message should be set in frontend
            elif update.message.text.lower() == "/help":
                tb.send_message(update.message.sender.id, "Send reports here to \
                        share them with other users. Use /start and /stop to \
                        be included/excluded.")
                #TODO: /help message should be set in frontend
            else:
                reports.append(Report(update.message.sender.username, self,
                               update.message.text, None, update.message.date))
        return reports

    def post(self, user, report):
        tb = Telegram(user.get_telegram_credentials())
        text = report.text
        if len(text) > 4096:
            text = text[:4096 - 4] + u' ...'
        try:
            for subscriber_id in user.get_telegram_subscribers():
                tb.send_message(subscriber_id, text).wait()
        except Exception:
            logger.error('Error telegramming: ' + user.get_city() + ': '
                         + report.id, exc_info=True)
