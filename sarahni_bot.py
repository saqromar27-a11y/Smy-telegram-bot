from datetime import datetime
import telebot

BOT_TOKEN = "9262966665:AAHbFP00rSTC82VnJC02W17XSe7R-qQaFHw"
OWNER_ID = 5565386577

bot = telebot.TeleBot(BOT_TOKEN)

# تخزين في الذاكرة للربط والحظر والردود وتتبع المستخدمين الجدد
code_to_user = {}
user_to_code = {}
blocked_by_owner = set()
reply_target_by_msg = {}
seen_users = set()


def get_or_create_code(user_id):
  if user_id in user_to_code:
    return user_to_code[user_id]
  code = f"A{100 + len(code_to_user) + 1}"
  code_to_user[code] = user_id
  user_to_code[user_id] = code
  return code


def now_formatted():
  return datetime.now().strftime("%Y/%m/%d - %H:%M:%S")


def format_user_name(chat_obj):
  if not chat_obj:
    return "مستخدم"
  full_name = (
      f"{chat_obj.first_name or ''} {chat_obj.last_name or ''}".strip()
  )
  if full_name:
    return full_name
  if getattr(chat_obj, "username", None):
    return f"@{chat_obj.username}"
  return "مستخدم"


def notify_owner_if_new_user(user):
  if not user or user.id in seen_users:
    return
  seen_users.add(user.id)
  if user.id == OWNER_ID:
    return

  name = format_user_name(user)
  username = f"@{user.username}" if user.username else "لا يوجد"
  time_str = now_formatted()

  try:
    bot.send_message(
        OWNER_ID,
        f"🆕 مستخدم جديد بدأ استخدام البوت:\n"
        f"• الاسم: {name}\n"
        f"• اليوزر: {username}\n"
        f"• المعرف (ID): {user.id}\n"
        f"• الوقت: {time_str}",
    )
  except Exception:
    pass


def build_user_home_text(bot_username, user_id):
  my_link = f"https://t.me/{bot_username}?start={user_id}"
  return (
      "▪️ بوت صارحني\n\n"
      "▫️ احصل على نقد بناء بسرية تامة من زملائك في العمل وأصدقائك.\n\n"
      "🌐 احصل على الرابط الخاص بك .\n"
      "💌 إقرأ ما كتبه الناس عنك .\n"
      "--------------------------\n\n"
      f"رابطك الخاص:\n{my_link}"
  )


def build_target_prompt_text(target_name):
  return (
      "▪️ اهلاً بك ..\n"
      f"▫️ سوف يتم إرسال الرسالة الى ({target_name}) بسرية تامة .\n"
      "▫️ صارحني انا مستعد لمواجهة الصراحة .\n"
      "▫️ اكتب ماتريد او ارسل ماتريد (صوره، صوت، فيديو..) في هذه المحدثة"
      f" وسوف يتم إرسالها إلى ({target_name})."
  )


def forward_media_or_text(message, target_id, sender_code):
  time_str = now_formatted()
  header = (
      f"📩 وصلتك مصارحة جديدة:\n"
      f"⏱وقت الرسالة: {time_str}\n"
      f"🏷️ الكود: #{sender_code}\n"
  )
  footer = "\n----\n💡 يمكنك الرد بعمل رد على هذه الرسالة ."

  if message.content_type == "text":
    sent = bot.send_message(target_id, f"{header}\n{message.text}{footer}")
  elif message.content_type == "photo":
    caption = (
        f"{header}\n{message.caption}{footer}"
        if message.caption
        else f"{header}{footer}"
    )
    sent = bot.send_photo(
        target_id, message.photo[-1].file_id, caption=caption
    )
  elif message.content_type == "voice":
    sent = bot.send_voice(
        target_id, message.voice.file_id, caption=f"{header}{footer}"
    )
  elif message.content_type == "video":
    caption = (
        f"{header}\n{message.caption}{footer}"
        if message.caption
        else f"{header}{footer}"
    )
    sent = bot.send_video(
        target_id, message.video.file_id, caption=caption
    )
  elif message.content_type == "audio":
    caption = (
        f"{header}\n{message.caption}{footer}"
        if message.caption
        else f"{header}{footer}"
    )
    sent = bot.send_audio(
        target_id, message.audio.file_id, caption=caption
    )
  elif message.content_type == "document":
    caption = (
        f"{header}\n{message.caption}{footer}"
        if message.caption
        else f"{header}{footer}"
    )
    sent = bot.send_document(
        target_id, message.document.file_id, caption=caption
    )
  elif message.content_type == "video_note":
    sent = bot.send_video_note(target_id, message.video_note.file_id)
    follow = bot.send_message(target_id, f"{header}{footer}")
    reply_target_by_msg[follow.message_id] = (message.from_user.id, sender_code)
    return sent
  elif message.content_type == "sticker":
    sent = bot.send_sticker(target_id, message.sticker.file_id)
    follow = bot.send_message(target_id, f"{header}{footer}")
    reply_target_by_msg[follow.message_id] = (message.from_user.id, sender_code)
    return sent
  else:
    bot.send_message(
        message.chat.id, "هذا النوع من الرسائل غير مدعوم حالياً."
    )
    return None

  reply_target_by_msg[sent.message_id] = (message.from_user.id, sender_code)
  return sent


@bot.message_handler(commands=["start"])
def handle_start(message):
  notify_owner_if_new_user(message.from_user)
  me = bot.get_me()
  parts = message.text.split(maxsplit=1)

  if len(parts) > 1 and parts[1].strip().isdigit():
    target_id = int(parts[1].strip())
    if target_id != message.from_user.id:
      try:
        target_chat = bot.get_chat(target_id)
        target_name = format_user_name(target_chat)
      except Exception:
        target_name = "مستخدم"

      bot.send_message(
          message.chat.id, build_target_prompt_text(target_name)
      )
      bot.register_next_step_handler(
          message, lambda m: process_incoming_confession(m, target_id)
      )
      return

  bot.send_message(
      message.chat.id, build_user_home_text(me.username, message.from_user.id)
  )


def process_incoming_confession(message, target_id):
  if message.text and message.text.startswith("/"):
    bot.send_message(
        message.chat.id, "تم إلغاء الإرسال. أرسل /start للمتابعة."
    )
    return

  if target_id == OWNER_ID and message.from_user.id in blocked_by_owner:
    bot.send_message(message.chat.id, "عذراً، لا يمكن إرسال الرسالة.")
    return

  sender_code = get_or_create_code(message.from_user.id)
  try:
    sent = forward_media_or_text(message, target_id, sender_code)
    if sent:
      bot.send_message(
          message.chat.id,
          "✅ تم إرسال رسالتك بشكل مجهول.\n"
          "💡 عندما يصلك رد، قم بالرد على رسالة البوت لمتابعة المحادثة.",
      )
  except Exception:
    bot.send_message(
        message.chat.id,
        "تعذر إرسال الرسالة، تأكد أن صاحب الرابط قد بدأ المحادثة مع البوت.",
    )


@bot.message_handler(commands=["حظر", "block"])
def handle_ban_reply(message):
  if message.from_user.id != OWNER_ID:
    return
  if not message.reply_to_message:
    bot.send_message(
        message.chat.id, "قم بالرد على الرسالة ثم اكتب /حظر"
    )
    return
  target_info = reply_target_by_msg.get(message.reply_to_message.message_id)
  if not target_info:
    bot.send_message(message.chat.id, "لم يتم العثور على بيانات هذه الرسالة.")
    return
  sender_id, sender_code = target_info
  blocked_by_owner.add(sender_id)
  bot.send_message(message.chat.id, f"تم حظر المرسل ({sender_code}).")


@bot.message_handler(commands=["unblock"])
def handle_unblock(message):
  if message.from_user.id != OWNER_ID:
    return
  parts = message.text.split(maxsplit=1)
  if len(parts) < 2:
    bot.send_message(message.chat.id, "اكتب: /unblock الكود")
    return
  code = parts[1].strip().lstrip("#")
  sender_id = code_to_user.get(code)
  if sender_id and sender_id in blocked_by_owner:
    blocked_by_owner.remove(sender_id)
    bot.send_message(message.chat.id, f"تم فك الحظر عن ({code}).")
  else:
    bot.send_message(message.chat.id, "الكود غير موجود أو غير محظور.")


# أمر خاص بالمالك فقط لكشف الاسم واليوزر والـ ID بالكود بدون أي إشعار للطرف الآخر
@bot.message_handler(commands=["info"])
def handle_info(message):
  if message.from_user.id != OWNER_ID:
    return
  parts = message.text.split(maxsplit=1)
  if len(parts) < 2:
    bot.send_message(message.chat.id, "اكتب: /info الكود")
    return
  code = parts[1].strip().lstrip("#")
  sender_id = code_to_user.get(code)
  if not sender_id:
    bot.send_message(message.chat.id, "الكود غير موجود.")
    return
  try:
    chat_info = bot.get_chat(sender_id)
    full_name = (
        f"{chat_info.first_name or ''} {chat_info.last_name or ''}".strip()
    )
    username = f"@{chat_info.username}" if chat_info.username else "لا يوجد"
    bot.send_message(
        message.chat.id,
        f"الاسم: {full_name or 'غير متوفر'}\n"
        f"اليوزر: {username}\n"
        f"المعرف (ID): {sender_id}",
    )
  except Exception as e:
    bot.send_message(message.chat.id, f"تعذر جلب المعلومات: {e}")


@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "voice",
        "video",
        "audio",
        "document",
        "video_note",
        "sticker",
    ],
    func=lambda m: m.reply_to_message is not None,
)
def handle_reply_back(message):
  target_info = reply_target_by_msg.get(message.reply_to_message.message_id)
  if not target_info:
    return
  original_sender_id, _ = target_info
  replier_code = get_or_create_code(message.from_user.id)
  time_str = now_formatted()
  reply_prefix = (
      f"💭 جاءك رد جديد:\n"
      f"⏱وقت الرسالة: {time_str}\n"
      f"🏷️ الكود: #{replier_code}\n\n"
  )
  reply_suffix = "\n\n----\n💡 يمكنك الرد بعمل رد على هذه الرسالة ."

  try:
    if message.content_type == "text":
      sent = bot.send_message(
          original_sender_id,
          f"{reply_prefix}{message.text}{reply_suffix}",
      )
    elif message.content_type == "photo":
      cap = (
          f"{reply_prefix}{message.caption}{reply_suffix}"
          if message.caption
          else f"{reply_prefix}{reply_suffix}"
      )
      sent = bot.send_photo(
          original_sender_id, message.photo[-1].file_id, caption=cap
      )
    elif message.content_type == "voice":
      sent = bot.send_voice(
          original_sender_id,
          message.voice.file_id,
          caption=f"{reply_prefix}{reply_suffix}",
      )
    elif message.content_type == "video":
      cap = (
          f"{reply_prefix}{message.caption}{reply_suffix}"
          if message.caption
          else f"{reply_prefix}{reply_suffix}"
      )
      sent = bot.send_video(
          original_sender_id, message.video.file_id, caption=cap
      )
    elif message.content_type == "audio":
      cap = (
          f"{reply_prefix}{message.caption}{reply_suffix}"
          if message.caption
          else f"{reply_prefix}{reply_suffix}"
      )
      sent = bot.send_audio(
          original_sender_id, message.audio.file_id, caption=cap
      )
    elif message.content_type == "document":
      cap = (
          f"{reply_prefix}{message.caption}{reply_suffix}"
          if message.caption
          else f"{reply_prefix}{reply_suffix}"
      )
      sent = bot.send_document(
          original_sender_id, message.document.file_id, caption=cap
      )
    elif message.content_type == "video_note":
      sent = bot.send_video_note(original_sender_id, message.video_note.file_id)
      follow = bot.send_message(
          original_sender_id, f"{reply_prefix}{reply_suffix}"
      )
      reply_target_by_msg[follow.message_id] = (message.from_user.id, "")
      bot.send_message(message.chat.id, "✅ تم إرسال ردك.")
      return
    elif message.content_type == "sticker":
      sent = bot.send_sticker(original_sender_id, message.sticker.file_id)
      follow = bot.send_message(
          original_sender_id, f"{reply_prefix}{reply_suffix}"
      )
      reply_target_by_msg[follow.message_id] = (message.from_user.id, "")
      bot.send_message(message.chat.id, "✅ تم إرسال ردك.")
      return
    else:
      return

    reply_target_by_msg[sent.message_id] = (
        message.from_user.id,
        replier_code,
    )
    bot.send_message(message.chat.id, "✅ تم إرسال ردك.")
  except Exception:
    bot.send_message(message.chat.id, "تعذر إرسال الرد.")


print("البوت يعمل...")
bot.infinity_polling(skip_pending=True)
