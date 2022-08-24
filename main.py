from telegram.ext import CallbackContext,Handler,Filters,Dispatcher,Updater,CommandHandler,MessageHandler,MessageFilter,BaseFilter,Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent, KeyboardButton, ReplyKeyboardMarkup,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
import os
PORT = int(os.environ.get('PORT', '8443'))
import datetime
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
update = Updater('5591645553:AAEbvWbYTgVjFexAAAcMLnsf_No1uSD_gkk',use_context=True)


ADMINS = {
    'NARENGI':'133473427',
    'NABAT':'5182966885',
}

KEYS = {
    'NARENGI':'🍊',
    'NABAT':'🪴',
    # 'HARDO':'باهم.',
    'LAGHV':'👈🏻',
}
BANLIST = []
LASTS = {

}
LASTSADMINS = {

}
def start(update:Updater,context:CallbackContext):
    id = update.effective_chat.id
    admin = False
    admins = ''
    for i in ADMINS:
        if str(id) == ADMINS[i]:
            admin = True
            admins = i
    if admin:
        context.bot.send_message(chat_id=id,text=f'سلام {admins} .=)')
    else:
        name = ''
        # {'last_name': '\u200c\u200cAmani', 'id': 133473427, 'first_name': '\u200c\u200c\u200c\u200cMohaّmadreza', 'type': 'private'}
        # for i in ADMINS:
        name = ''
        last_name = ''
        username = ''
        url = 'tg://openmessage?user_id=%d'%id
        try:
            name = update.effective_chat.first_name
        except:
            pass
        try:
            last_name = update.effective_chat.last_name
        except:
            pass
        try:
            username = '@' + update.effective_chat.username
        except:
            pass
        text = f""" یه نفر جدید ربات رو استارت زد:
    name = {name + ' ' +last_name}
    username = {username}
    url = {url}
        """
        for i in ADMINS:
            context.bot.send_message(chat_id=ADMINS[i],text=text)
        welcome ='''
        سلام. ^^ 
    به ربات ما خوش اومدی، لطفا برای پیام دادن از کلیدهای زیر استفاده کن.
    🍊 برای پیام دادن به نارنگی؛
    🪴 برای پیام دادن به نبات.'''
        buttons = [
        # [KeyboardButton(KEYS['HARDO'])],
        [KeyboardButton(KEYS['NABAT']), KeyboardButton(KEYS['NARENGI'])]]
        reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        context.bot.send_message(chat_id=id,text=welcome,reply_markup=reply_markup)
def laghv(update:Updater,context:CallbackContext,text,id):
    matn = "به صفحه اصلی برگشتی. :'("
    buttons = [
    # [KeyboardButton(KEYS['HARDO'])],
    [KeyboardButton(KEYS['NABAT']), KeyboardButton(KEYS['NARENGI'])]]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    context.bot.send_message(chat_id=id,text=matn,reply_markup=reply_markup)
def laghv_admin(update:Updater,context:CallbackContext,text,id):
    matn = "به صفحه اصلی بازگشتید."
    buttons = [
    []]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    context.bot.send_message(chat_id=id,text=matn,reply_markup=reply_markup)
def admin():
    pass
def to(update:Updater,context:CallbackContext,text,id):
    
    if text == '🍊':
        name = 'نارنگی🍊'
        LASTS[id] = 'NARENGI'
    else:
        name = 'نبات🪴'
        LASTS[id] = 'NABAT'
    matn = f'''
در حال پیام دادن به {name} هستی. 
لطفا متن، عکس، آهنگ یا هرچیز دیگه‎ای که دوست داری رو برام بفرست.

برای برگشت از دستور 👈🏻 استفاده کن.  ^^'''
    buttons = [
    [KeyboardButton(KEYS['LAGHV'])]]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    context.bot.send_message(chat_id=id,text=matn,reply_markup=reply_markup)
def toAdmin(update:Updater,context:CallbackContext, admin, message):
    id = ADMINS[admin]
    senderID = update.effective_chat.id
    buttons = [
    [KeyboardButton(KEYS['LAGHV'])]]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    matn = 'پیام شما ارسال شد. '
    context.bot.send_message(chat_id=senderID,text=matn,reply_markup=reply_markup)
    mid = context.bot.forward_message(chat_id=id,from_chat_id=senderID,message_id= message.message_id).message_id
    if senderID not in BANLIST:
        keyboard = [
                    [InlineKeyboardButton("نمایش اطلاعات", callback_data=f'show_{senderID}')],
                    [InlineKeyboardButton("مسدود کردن", callback_data=f'ban_{senderID}')],
                    [InlineKeyboardButton("پاسخ دادن", callback_data=f'answer_{senderID}')]
                ]
    else:
        keyboard = [
                    [InlineKeyboardButton("نمایش اطلاعات", callback_data=f'show_{senderID}')],
                    [InlineKeyboardButton("لفو مسدودیت", callback_data=f'unban_{senderID}')],
                    [InlineKeyboardButton("پاسخ دادن", callback_data=f'answer_{senderID}')]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=id,text='اطلاعات کاربر', reply_markup=reply_markup)
def from_admin(update:Updater,context:CallbackContext):
    id = update.effective_chat.id
    getterID = LASTSADMINS[str(id)]
    # LASTSADMINS.pop[str(id)]
    message = update.message.message_id
    context.bot.copyMessage(chat_id=getterID,from_chat_id=id,message_id=message)
    context.bot.send_message(chat_id=id,text='پیام شما با موفقیت ارسال شد.')
    buttons = [
    [KeyboardButton(KEYS['LAGHV'])]]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def sendMessage(update:Updater,context:CallbackContext):
    id = update.effective_chat.id
    admin = False
    for i in ADMINS:
        if str(id) == ADMINS[i]:
            admin = True
    if admin:
        text = update.message.text
        if text == '👈🏻':
            laghv_admin(update,context,text,id)
        elif str(id) not in LASTSADMINS:
            context.bot.send_message(chat_id=id,text='متوجه نشدم باید چیکار کنم.')
        else:
            from_admin(update,context)
    else:
        if id in BANLIST:
            context.bot.send_message(chat_id=id,text='شما مسدود هستید.')
            return
        text = update.message.text
        if text == '🍊' or text == '🪴':
            to(update,context,text,id)
        elif text == '👈🏻':
            laghv(update,context,text,id)
        elif id in LASTS:
            if LASTS[id] == 'NABAT':
                toAdmin(update,context, 'NABAT', update.message)
            elif LASTS[id] == 'NARENGI':
                toAdmin(update,context, 'NARENGI', update.message)
            elif str(id) not in LASTS:
                context.bot.send_message(chat_id=id,text='متوجه نشدم باید چیکار کنم.')
def press_button_callback(update:Updater,context:CallbackContext):
    data:str = update.callback_query.data
    id = update.callback_query.message.chat.id
    if data.startswith('show'):
        context.bot.send_message(chat_id=id,text='tg://openmessage?user_id='+data.split('_')[1])
    if data.startswith('ban'):
        context.bot.send_message(chat_id=id,text='یوزر مورد نظر بن شد. :(')
        BANLIST.append(data.split('_')[1])
    if data.startswith('unban'):
        context.bot.send_message(chat_id=id,text='یوزر مورد نظر از مسدودیت خارج شد.')
        BANLIST.remove(data.split('_')[1])
    if data.startswith('answer'):
        context.bot.send_message(chat_id=id,text='داری به نمیدونم کی کی پاسخ میدی. لطفا متنت رو بفرست.')
        LASTSADMINS[str(id)]=data.split('_')[1]
def main():
    dispatcher = update.dispatcher
    startHandler = CommandHandler('start',start)
    dispatcher.add_handler(startHandler)
    dispatcher.add_handler(MessageHandler(Filters.all,sendMessage))
    update.dispatcher.add_handler(CallbackQueryHandler(press_button_callback))
    update.start_webhook(
            listen="0.0.0.0",
            port=int(PORT),
            url_path='5591645553:AAEbvWbYTgVjFexAAAcMLnsf_No1uSD_gkk',
            webhook_url='https://tele2430.herokuapp.com/' + '5591645553:AAEbvWbYTgVjFexAAAcMLnsf_No1uSD_gkk'
        )

    update.idle()

if __name__ == '__main__':
    main()
