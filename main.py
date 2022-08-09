import jdatetime, datetime
import time
from telegram.ext import Updater, CommandHandler
import telegram

token = "5474969554:AAHmxmLxMWGe13LfTpLfGJ_1hUWOAkAgQNk"
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


def sendMessage():
    while True:
        for ID in IDS:
            con.edit_message_text(
                chat_id=ID, message_id=messageIDS[IDS.index(ID)], text=tarikh()
            )

        time.sleep(1)

thre = threading.Thread(target=sendMessage)
thre.start()


def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    user = update.message.from_user
    update.message.reply_text(
        "سلام {} عزیز به ربات ما خوش آمدید.".format(user.first_name)
    )
    IDS.append(user.id)
    messageIDS.append(con.send_message(chat_id=user.id, text=tarikh()).message_id)
    print(user.id)
    print(messageIDS[IDS.index(user.id)])


def main():
    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)
    updater.start_polling()
    updater.idle()

main()
