import jdatetime, datetime
import time
from telegram.ext import Updater, CommandHandler
import telegram

token = "5514946113:AAEn2d3NH6Y8DfzfC8upN8Ir3rbReOnPdg0"
updater = Updater(token)
dispatcher = updater.dispatcher
IDS = []
IDS2 = []
messageIDS = []
import threading

con = updater.bot


def tarikh():
    return jdatetime.datetime.now().strftime(
        "%A, %d %B %Y %H:%M:%S"
    ) + '\n' + datetime.datetime.now().strftime("%A, %d %B %Y %H:%M:%S")


# def sendMessage():
#     while True:
#         for ID in IDS:
#             con.edit_message_text(
#                 chat_id=ID, message_id=messageIDS[IDS.index(ID)], text=tarikh()
#             )

#         time.sleep(1)

# thre = threading.Thread(target=sendMessage)
# thre.start()


def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    for i in range(100000):
        update.message.reply_text(
        "niloo khare {}".format(i)
        )


def main():
    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)
    updater.start_polling()
    updater.idle()

main()
