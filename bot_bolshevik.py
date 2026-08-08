import asyncio
import logging
import random
import sqlite3
import time
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand
from aiogram.enums import ParseMode

TOKEN = "8725576726:AAG8qfH0hzkM_Z7EpVJKw8t-WZm0lJbmiGs"

KILLCOOLDOWN = 3600 

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("bolsheviks.db")
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS killers (userid INTEGER PRIMARY KEY, firstname TEXT, kills INTEGER DEFAULT 0, lastkill INTEGER DEFAULT 0, army TEXT DEFAULT 'Не выбран')")
conn.commit()

# Регистрация меню команд в Telegram
async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="profile", description="Мой профиль и статистика"),
        BotCommand(command="kill", description="Зарубить большевиков"),
        BotCommand(command="army", description="Выбрать Белую Армию"),
        BotCommand(command="sostav", description="Состав выбранной армии"),
        BotCommand(command="top", description="Топ лучших гвардейцев"),
        BotCommand(command="armies", description="Рейтинг и общая статистика армий"),
        BotCommand(command="help", description="Справка по игре"),
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def startcmd(message: types.Message):
    await message.answer(
        f"Здорово, {message.from_user.first_name}! ⚔️\n\n"
        "Время очистить земли от большевиков!\n\n"
        "📌 Основные команды:\n"
        "⚔️ /kill (или 'зарубить') — Пойти в атаку\n"
        "👤 /profile (или 'профиль') — Твоя статистика\n"
        "🚩 /army (или 'армия') — Выбрать свою армию\n"
        "👥 /sostav (или 'состав') — Участники твоей армии\n"
        "🏆 /top — Топ лучших рубаков\n"
        "📊 /armies — Общая статистика и рейтинг армий\n"
        "❓ /help — Полная справка"
    )

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/help', 'help', 'помощь', 'хелп')))
async def helpcmd(message: types.Message):
    await message.answer(
        "📖 ИНСТРУКЦИЯ И СПРАВКА ПО ИГРЕ\n\n"
        "⚔️ Атака (/kill или 'зарубить'):\n"
        "Каждый час вы можете совершить набег и зарубить от 1 до 15 большевиков. Все фраги идут в ваш личный счёт и в счёт вашей Армии!\n\n"
        "👤 Профиль (/profile или 'профиль'):\n"
        "Просмотр вашей личной статистики и выбранного полка.\n\n"
        "🚩 Выбор Армии (/army или 'армия'):\n"
        "Выберите один из 5 легендарных полков. Ваши очки поднимают армию в общем рейтинге!\n\n"
        "👥 Состав Армии (/sostav или 'состав'):\n"
        "Показывает список бойцов вашей армии с кликабельными ссылками на их профили.\n\n"
        "📊 Статистика (/armies и /top):\n"
        "Следите за общим счетчиком уничтоженных большевиков и лидерами фронта!"
    )

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/profile', 'profile', 'профиль', 'паспорт', '/me')))
async def profilecmd(message: types.Message):
    userid = message.from_user.id
    cursor.execute("SELECT kills, army FROM killers WHERE userid = ?", (userid,))
    row = cursor.fetchone()
    
    kills = row[0] if row else 0
    army = row[1] if row else "Не выбран"
    
    # Ссылка на профиль игрока
    user_link = f"<a href='tg://user?id={userid}'>{message.from_user.first_name}</a>"
    
    await message.answer(
        f"🪪 <b>ПАСПОРТ ГВАРДЕЙЦА</b>\n\n"
        f"Боец: {user_link}\n"
        f"🚩 Армия: <b>{army}</b>\n"
        f"⚔️ Зарублено большевиков: <b>{kills}</b>",
        parse_mode=ParseMode.HTML
    )

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/army', 'army', 'армия', 'полк')))
async def armycmd(message: types.Message):
    cursor.execute("SELECT army FROM killers WHERE userid = ?", (message.from_user.id,))
    row = cursor.fetchone()
    currentarmy = row[0] if row else "Не выбран"
    
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❄️ Армия Колчака", callback_data="set_Армия Колчака")],
            [types.InlineKeyboardButton(text="⚜️ Армия Деникина", callback_data="set_Армия Деникина")],
            [types.InlineKeyboardButton(text="🛡 Армия Врангеля", callback_data="set_Армия Врангеля")],
            [types.InlineKeyboardButton(text="⚔️ Армия Юденича", callback_data="set_Армия Юденича")],
            [types.InlineKeyboardButton(text="🌲 Армия Миллера", callback_data="set_Армия Миллера")]
        ]
    )
    
    await message.answer(
        f"🚩 Твоя текущая армия: {currentarmy}\n\nВыбери армию, за которую будешь сражаться:",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data and c.data.startswith('set_'))
async def processarmychoice(callbackquery: types.CallbackQuery):
    armyname = callbackquery.data.replace('set_', '')
    userid = callbackquery.from_user.id
    firstname = callbackquery.from_user.first_name
    
    cursor.execute("INSERT INTO killers (userid, firstname, army) VALUES (?, ?, ?) ON CONFLICT(userid) DO UPDATE SET firstname = ?, army = ?", (userid, firstname, armyname, firstname, armyname))
    conn.commit()
    
    await callbackquery.answer(f"Ты вступил в: {armyname}!")
    await callbackquery.message.edit_text(f"⚔️ Отлично! Теперь ты сражаешься за: {armyname}!")

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/sostav', 'sostav', 'состав')))
async def sostavcmd(message: types.Message):
    userid = message.from_user.id
    cursor.execute("SELECT army FROM killers WHERE userid = ?", (userid,))
    row = cursor.fetchone()
    
    if not row or row[0] == "Не выбран":
        await message.answer("Ты еще не выбрал армию! Напиши /army, чтобы примкнуть к полку.")
        return
        
    armyname = row[0]
    cursor.execute("SELECT firstname, kills, userid FROM killers WHERE army = ? ORDER BY kills DESC LIMIT 20", (armyname,))
    members = cursor.fetchall()
    
    text = f"👥 <b>СОСТАВ ПОЛКА [{armyname}]:</b>\n\n"
    for index, (name, kills, member_id) in enumerate(members, start=1):
        player_name = name if name else f"Казак {member_id}"
        user_link = f"<a href='tg://user?id={member_id}'>{player_name}</a>"
        text += f"{index}. {user_link} — {kills} большевиков\n"
        
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/kill', 'kill', 'зарубить', 'рубить')))
async def killcmd(message: types.Message):
    userid = message.from_user.id
    firstname = message.from_user.first_name
    currenttime = int(time.time())
    
    cursor.execute("SELECT kills, lastkill, army FROM killers WHERE userid = ?", (userid,))
    row = cursor.fetchone()
    
    kills = row[0] if row else 0
    lastkill = row[1] if row else 0
    army = row[2] if row else "Не выбран"
    
    timepassed = currenttime - lastkill
    if timepassed < KILLCOOLDOWN:
        timeleft = KILLCOOLDOWN - timepassed
        if timeleft >= 3600:
            hours = timeleft // 3600
            minutes = (timeleft % 3600) // 60
            timestr = f"{hours} ч. {minutes} мин."
        elif timeleft >= 60:
            minutes = timeleft // 60
            seconds = timeleft % 60
            timestr = f"{minutes} мин. {seconds} сек."
        else:
            timestr = f"{timeleft} сек."

        await message.answer(f"⏳Шашка затупилась! Отдохни ещё {timestr} перед следующим набегом.")
        return

    gainedkills = random.randint(1, 15)
    newtotal = kills + gainedkills
    
    cursor.execute("INSERT INTO killers (userid, firstname, kills, lastkill, army) VALUES (?, ?, ?, ?, ?) ON CONFLICT(userid) DO UPDATE SET firstname = ?, kills = kills + ?, lastkill = ?", (userid, firstname, gainedkills, currenttime, army, firstname, gainedkills, currenttime))
    conn.commit()
    
    phrases = [
        f"⚔️ Вы выехали в поле и зарубили {gainedkills} большевиков!",
        f"🪓 Взмах шашки! Минус {gainedkills} большевиков!",
        f"🐎 Удачная засада! Зарублено {gainedkills} большевиков!"
    ]
    randomphrase = random.choice(phrases)
    
    await message.answer(f"{randomphrase}\n\n🚩 Твоя армия: {army}\n📊 Всего тобой зарублено: {newtotal}")

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/top', 'top', 'топ')))
async def topcmd(message: types.Message):
    cursor.execute("SELECT firstname, kills, userid, army FROM killers ORDER BY kills DESC LIMIT 10")
    topusers = cursor.fetchall()
    
    if not topusers:
        await message.answer("В топе пока пусто! Напиши 'зарубить', чтобы стать первым!")
        return
        
    text = "🏆 <b>Топ лучших гвардейцев:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for index, (name, kills, userid, army) in enumerate(topusers, start=1):
        place = medals[index-1] if index <= 3 else f"{index}."
        playername = name if name else f"Казак {userid}"
        user_link = f"<a href='tg://user?id={userid}'>{playername}</a>"
        armyinfo = f" [{army}]" if army and army != 'Не выбран' else ""
        text += f"{place} {user_link}{armyinfo} — {kills} большевиков\n"
        
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/armies', 'armies', 'армии', 'отряды')))
async def armiescmd(message: types.Message):
    # Общая сумма убитых большевиков
    cursor.execute("SELECT SUM(kills) FROM killers")
    total_all_kills = cursor.fetchone()[0] or 0

    cursor.execute("SELECT army, SUM(kills) as totalkills FROM killers WHERE army != 'Не выбран' GROUP BY army ORDER BY totalkills DESC")
    armiestop = cursor.fetchall()
    
    text = f"📊 <b>ОБЩАЯ СТАТИСТИКА ФРОНТА:</b>\n"
    text += f"💀 Всего ликвидировано большевиков: <b>{total_all_kills}</b>\n\n"
    text += "🚩 <b>РЕЙТИНГ БЕЛЫХ АРМИЙ:</b>\n\n"
    
    if not armiestop:
        text += "Пока ни одна армия не вступила в бой! Выбери армию командой /army и сделай первый замах!"
    else:
        medals = ["🥇", "🥈", "🥉"]
        for index, (armyname, totalkills) in enumerate(armiestop, start=1):
            place = medals[index-1] if index <= 3 else f"{index}."
            text += f"{place} {armyname} — {totalkills} большевиков\n"
        
    await message.answer(text, parse_mode=ParseMode.HTML)

async def handle_ping(request):
    return web.Response(text="Bot is active")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    await setup_bot_commands(bot)
    
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
