from telebot import TeleBot
from telebot.types import Message
from telebot.custom_filters import SimpleCustomFilter
from telebot.util import extract_arguments
from y2mate_api import first_query, second_query, third_query, appdir, Handler
from dotenv import load_dotenv
from os import getenv, remove
from json import dumps

load_dotenv()

handler = Handler("")

bot = TeleBot(
    token=getenv("telegram-api-token"),
    disable_web_page_preview=False,
)

bot.remove_webhook()

admin_id = int(getenv("telegram-admin-id", 0))

quality: dict[int, str] = {}

metadata = {
    "TOTAL_USERS": 0,
    "AUDIO_DOWNLOADS": 0,
    "VIDEO_DOWNLOADS": 0,
}

available_qualities = (
    "4k",
    "1080p",
    "720p",
    "480p",
    "360p",
    "240p",
    "144p",
    "auto",
    "best",
    "worst",
)

usage_info = (
    "Download youtube videos and audios :\n"
    "Available commands : \n"
    "/audio - Download only the audio of  a video.\n"
    "/video - Download video\n"
    "/quality - Set new video quality.\n\n"
    "Just append video title/id/url to these commands."
)

cache_dir = appdir.user_cache_dir


def text_is_required(func):
    """Decorator to ensure commands are followed by a value"""

    def decorator(message: Message):
        if not extract_arguments(message.text):
            bot.reply_to(message, f"Text is required!")
        else:
            try:
                return func(message)
            except Exception as e:
                bot.reply_to(
                    message,
                    f"Error occurred - {e.args[1] if e.args and len(e.args)>1 else e}",
                )

    return decorator


def make_media_info(meta: dict) -> str:
    print(meta)
    info = (
        f"Title : {meta.get('title')}\n"
        f"Size : {meta.get('size')}\n"
        f"Quality : {meta.get('q')}({meta.get('f')})\n"
        f"dlink : {meta.get('dlink')}"
    )
    return info


@bot.message_handler(commands=["start"])
def echo_usage_info(message: Message):
    """Send back usage info"""
    metadata["TOTAL_USERS"] += 1
    bot.reply_to(message, usage_info)


@bot.message_handler(commands=["audio"])
@text_is_required
def download_and_send_audio_file(message: Message):
    """Sends audio version of a video"""
    query = extract_arguments(message.text)
    fq = first_query(query).main()
    sq = second_query(fq).main()
    third_dict = third_query(sq).main(format="mp3")
    metadata["AUDIO_DOWNLOADS"] += 1
    bot.send_message(
        message.chat.id,
        make_media_info(third_dict),
    )
    bot.send_chat_action(message.chat.id, "upload_audio")
    saved_to = handler.save(third_dict, cache_dir, progress_bar=False)
    bot.send_audio(
        message.chat.id,
        open(saved_to, "rb"),
        title=third_dict.get("title", "Unknown title"),
    )
    try:
        remove(saved_to)
    except:
        pass


@bot.message_handler(commands=["video"])
@text_is_required
def download_and_send_video_file(message: Message):
    """Sends video"""
    query = extract_arguments(message.text)
    fq = first_query(query).main()
    sq = second_query(fq).main()
    user_video_quality = quality.get(message.from_user.id, "720p")
    third_dict = third_query(sq).main(format="mp4", quality=user_video_quality)
    metadata["VIDEO_DOWNLOADS"] += 1
    bot.send_message(
        message.chat.id,
        make_media_info(third_dict),
    )
    bot.send_chat_action(message.chat.id, "upload_video")
    saved_to = handler.save(third_dict, cache_dir, progress_bar=False)
    bot.send_video(
        message.chat.id, open(saved_to, "rb"), caption=third_dict.get("title")
    )
    try:
        remove(saved_to)
    except:
        pass


@bot.message_handler(commands=["quality"])
@text_is_required
def set_new_video_quality(message: Message):
    """Set Video quality"""
    text = extract_arguments(message.text)
    if text in available_qualities:
        quality[message.from_user.id] = text
        bot.reply_to(message, "New video quality set : " + text)
    else:
        bot.reply_to(
            message, f'Qualities should be one of : [{", ".join(available_qualities)}]'
        )


@bot.message_handler(commands=["stats"], is_admin=True)
def show_users_count_to_admin(message: Message):
    bot.send_message(
        message.chat.id, f"```json\n{dumps(metadata, indent=4)}\n```", "Markdown"
    )


@bot.message_handler(commands=["myid"])
def echo_user_telegram_id(message: Message):
    bot.reply_to(message, f"Your telegram ID is : {message.from_user.id}")


class IsAdminFilter(SimpleCustomFilter):

    key: str = "is_admin"

    @staticmethod
    def check(message: Message):
        return message.from_user.id == admin_id


bot.add_custom_filter(IsAdminFilter())

if __name__ == "__main__":
    print("Infinity polling ...")
    bot.infinity_polling()
