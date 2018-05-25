from bot import Bot
import logging
from report import Report
from twx.botapi import TelegramBot


logger = logging.getLogger(__name__)


class TelegramBot(Bot):
    def crawl(self, user):
        tb = TelegramBot(user.get_telegram_credentials())
        updates = tb.get_updates().wait()
        reports = []
        for update in updates:
            reports.append(Report(update.message.from.username,self,
                                  update.message.text,None,update.message.date))
        return reports

    def post(self, user, report):
        tb = TelegramBot(user.get_telegram_credentials())
        text = report.text
        if len(text) > 4096:
            text = text[:4096 - 4] + u' ...'
        try:
            for subscriber_id in user.get_telegram_subscribers():
                tb.send_message(subscriber_id, text).wait()
        except Exception:
            logger.error('Error telegramming: ' + user.get_city() + ': '
                         + report.id, exc_info=True)
