import asyncio
import logging
import random
import sqlite3
import time
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

TOKEN = "8725576726:AAE0XMB8k5Po1hyGUamhCGrMq1USs7aZ_EA"

KILLCOOLDOWN = 3600 

session = AiohttpSession()
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

conn = sqlite3.connect("bolsheviks.db")
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS killers (userid INTEGER PRIMARY KEY, firstname TEXT, kills INTEGER DEFAULT 0, lastkill INTEGER DEFAULT 0, army TEXT DEFAULT 'Не выбран')")
conn.commit()

@dp.message(Command("start"))
async def startcmd(message: types.Message):
    await message.answer(
        f"Здорово, {message.from_user.first_name}! ⚔️\n\n"
        "Время очистить земли Белой Армии!\n\n"
        "Команды:\n"
        "⚔️ /kill (или 'зарубить') — Пойти в атаку\n"
        "🚩 /army (или 'армия') — Выбрать свою армию\n"
        "🏆 /top — Топ главных рубаков\n"
        "📊 /armies — Рейтинг армий"
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

        await message.answer(f"⏳ Шашка затупилась! Отдохни ещё {timestr} перед следующим набегом.")
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
        
    text = "🏆 Топ лучших гвардейцев:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for index, (name, kills, userid, army) in enumerate(topusers, start=1):
        place = medals[index-1] if index <= 3 else f"{index}."
        playername = name if name else f"Казак {userid}"
        armyinfo = f" [{army}]" if army and army != 'Не выбран' else ""
        text += f"{place} {playername}{armyinfo} — {kills} большевиков\n"
        
    await message.answer(text)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/armies', 'armies', 'армии', 'отряды')))
async def armiescmd(message: types.Message):
    cursor.execute("SELECT army, SUM(kills) as totalkills FROM killers WHERE army != 'Не выбран' GROUP BY army ORDER BY totalkills DESC")
    armiestop = cursor.fetchall()
    
    if not armiestop:
        await message.answer("Пока ни одна армия не вступила в бой! Выбери армию командой /army и сделай первый замах!")
        return
        
    text = "📊 РЕЙТИНГ БЕЛЫХ АРМИЙ:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for index, (armyname, totalkills) in enumerate(armiestop, start=1):
        place = medals[index-1] if index <= 3 else f"{index}."
        text += f"{place} {armyname} — {totalkills} большевиков\n"
        
    await message.answer(text)

# Веб-сервер для обмана Render (чтобы не усыплял бота)
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.00.0000", port)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())