

import logging
import requests
import soundfile as sf
import speech_recognition as sr
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType

TELEGRAM_KEY = 'PASTE YOUR TOKEN HERE'  
VOICE_LANGUAGE = 'ru-RU'
MAX_MESSAGE_SIZE = 50 * 1024 * 1024  # 50 MB (ограничение Telegram на размер файла)
MAX_MESSAGE_DURATION = 120  # seconds (ограничение Telegram на длительность аудиосообщения)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_KEY)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_prompt(message: Message):
    reply = "Привет! Я бот для расшифровки голосовых сообщений. Просто добавьте меня в чат, и я буду автоматически преобразовывать все голосовые сообщения в текст."
    await message.reply(reply)


@dp.message(F.content_type.in_({ContentType.VOICE, ContentType.VIDEO_NOTE}))
async def echo_voice(message: Message):
    data = message.voice or message.video_note
    if (data.file_size > MAX_MESSAGE_SIZE) or (data.duration > MAX_MESSAGE_DURATION):
        reply = ' '.join((
            "Голосовое сообщение слишком большое.",
            "Максимальная длительность: {} сек.".format(MAX_MESSAGE_DURATION),
            "Попробуйте сказать что-то покороче.",
        ))
        await message.reply(reply)
        return

    file_info = await bot.get_file(data.file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

    file_path = await download_file(file_url)

    await convert_to_pcm16(file_path)

    text = await process_audio_file("new.wav")

    if not text:
        await message.reply("Не удалось распознать голосовое сообщение.", reply_to_message_id=message.message_id)
        return

    await message.reply(f"🎙 Расшифровка:\n{text}", reply_to_message_id=message.message_id)


async def download_file(file_url: str) -> str:
    file_path = "voice_message.ogg"
    response = requests.get(file_url)
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return file_path


async def convert_to_pcm16(file_path: str):
    data, samplerate = sf.read(file_path)
    sf.write('new.wav', data, samplerate, subtype='PCM_16')


async def process_audio_file(file_path: str) -> str:
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language=VOICE_LANGUAGE)
        return text
    except sr.UnknownValueError:
        return None
    except Exception as e: 
        logging.error(f"Error during speech recognition: {e}")
        return None


if __name__ == '__main__':
    dp.run_polling(bot)

