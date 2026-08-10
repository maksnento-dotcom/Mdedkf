import asyncio
import logging
import random
import sqlite3
import time
import os
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand
from aiogram.enums import ParseMode

# ВСТАВЬ СЮДА ТОКЕН
TOKEN = "ВСТАВЬ_ТОКЕН_ТУТ"
ADMIN_IDS = [8203948836]

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    is_postgres = True
else:
    conn = sqlite3.connect("bolsheviks_test.db")
    is_postgres = False

cursor = conn.cursor()

# Универсальный знак авто-замены для БД (%s для PostgreSQL, ? для SQLite)
P = "%s" if is_postgres else "?"

cursor.execute(f"""
CREATE TABLE IF NOT EXISTS killers (
    userid BIGINT PRIMARY KEY, 
    firstname TEXT, 
    kills INTEGER DEFAULT 0, 
    coins INTEGER DEFAULT 0,
    lastkill BIGINT DEFAULT 0, 
    army TEXT DEFAULT 'Не выбран',
    class TEXT DEFAULT 'Пехота',
    shields INTEGER DEFAULT 0,
    boost_atk INTEGER DEFAULT 0,
    boost_coins INTEGER DEFAULT 0
)
""")
conn.commit()

def get_rank(kills: int) -> str:
    if kills >= 1500: return "🎖 Генерал"
    elif kills >= 920: return "🎖 Полковник"
    elif kills >= 780: return "🎖 Капитан"
    elif kills >= 670: return "🎖 Прапорщик"
    elif kills >= 450: return "🎖 Старший унтер‑офицер"
    elif kills >= 230: return "🎖 Младший унтер‑офицер"
    elif kills >= 100: return "🎖 Ефрейтор"
    else: return "🎖 Рядовой"

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="profile", description="Профиль и звание"),
        BotCommand(command="kill", description="Зарубить большевиков"),
        BotCommand(command="class", description="Выбрать класс"),
        BotCommand(command="shop", description="Магазин предметов"),
        BotCommand(command="army", description="Выбрать Белую Армию"),
        BotCommand(command="sostav", description="Состав выбранной армии"),
        BotCommand(command="top", description="Топ лучших гвардейцев"),
        BotCommand(command="armies", description="Рейтинг армий"),
        BotCommand(command="help", description="Справка по игре"),
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def startcmd(message: types.Message):
    clean_name = message.from_user.first_name.replace("<", "&lt;").replace(">", "&gt;")
    await message.answer(
        f"Здорово, {clean_name}! ⚔️\n\n"
        "Время очистить земли от большевиков!\n\n"
        "📌 <b>Основные команды:</b>\n"
        "⚔️ /kill — Пойти в атаку\n"
        "👤 /profile — Профиль и звание\n"
        "🪖 /class — Выбрать класс (Пехота/Кавалерия)\n"
        "🛒 /shop — Магазин усилений\n"
        "⚔️ /attack @username — Напасть на игрока\n"
        "🚩 /army — Выбрать Белую Армию (с баффами!)\n"
        "🏆 /top — Топ лучших рубаков",
        parse_mode=ParseMode.HTML
    )

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/help', 'help', 'помощь', 'хелп')))
async def helpcmd(message: types.Message):
    await message.answer(
        "📖 <b>ИНСТРУКЦИЯ И СПРАВКА ПО ИГРЕ</b>\n\n"
        "⚔️ <b>Атака (/kill):</b> Зарубите большевиков и получите монеты!\n\n"
        "🚩 <b>ТАКТИЧЕСКИЕ БАФФЫ АРМИЙ (/army):</b>\n"
        "• <b>Армия Колчака:</b> -5% к ранению | +10 мин КД\n"
        "• <b>Армия Деникина:</b> +5 монет за бой | +5% к ранению\n"
        "• <b>Армия Врангеля:</b> Щиты по 5 монет | Скип КД по 45 монет\n"
        "• <b>Армия Юденича:</b> -15 мин КД | -5 к макс. фрагам\n"
        "• <b>Армия Миллера:</b> Бусты по 50 монет | +15 мин КД\n"
        "• <b>Дроздовцы:</b> 10% шанс на Х2 фраги | /attack стоит 25 монет\n"
        "• <b>КОМУЧ:</b> Нападение на вас виснет +10м КД | 10% шанс x0.5 монет\n"
        "• <b>Войско Донское:</b> -10 мин КД | +10% к ранению\n\n"
        "🪖 <b>Базовые Классы:</b>\n"
        "• <b>Пехота:</b> 1-20 фрагов, КД 60 мин, Шанс ранения 20%\n"
        "• <b>Кавалерия:</b> 1-15 фрагов, КД 45 мин, Шанс ранения 10%",
        parse_mode=ParseMode.HTML
    )

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/profile', 'profile', 'профиль', 'паспорт')))
async def profilecmd(message: types.Message):
    userid = message.from_user.id
    cursor.execute(f"SELECT kills, coins, army, class, shields, boost_atk, boost_coins FROM killers WHERE userid = {P}", (userid,))
    row = cursor.fetchone()
    
    kills = row[0] if row else 0
    coins = row[1] if row else 0
    army = row[2] if row else "Не выбран"
    u_class = row[3] if row else "Пехота"
    shields = row[4] if row else 0
    b_atk = "✅ Активен (x2)" if row and row[5] else "❌ Нет"
    b_coins = "✅ Активен (x2)" if row and row[6] else "❌ Нет"
    
    rank = get_rank(kills)
    clean_name = message.from_user.first_name.replace("<", "&lt;").replace(">", "&gt;")
    
    await message.answer(
        f"🪪 <b>ПАСПОРТ ГВАРДЕЙЦА</b>\n\n"
        f"Боец: <b>{clean_name}</b>\n"
        f"🎖 Звание: <b>{rank}</b>\n"
        f"🪖 Класс: <b>{u_class}</b>\n"
        f"🚩 Армия: <b>{army}</b>\n"
        f"⚔️ Убито большевиков: <b>{kills}</b>\n"
        f"💰 Монеты: <b>{coins}</b>\n\n"
        f"🎒 <b>Инвентарь и Бусты:</b>\n"
        f"🛡 Щиты от ранений: <b>{shields} шт.</b>\n"
        f"⚡️ Буст Атаки: {b_atk}\n"
        f"🪙 Буст Монет: {b_coins}",
        parse_mode=ParseMode.HTML
    )

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/class', 'class', 'класс')))
async def classcmd(message: types.Message):
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🗡 Пехота (1-20 фрагов, КД 60м, Шанс ранения 20%)", callback_data="setclass_Пехота")],
            [types.InlineKeyboardButton(text="🐎 Кавалерия (1-15 фрагов, КД 45м, Шанс ранения 10%)", callback_data="setclass_Кавалерия")]
        ]
    )
    await message.answer("🪖 <b>Выбери свой класс войск:</b>", reply_markup=kb, parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: c.data and c.data.startswith('setclass_'))
async def processclasschoice(callbackquery: types.CallbackQuery):
    newclass = callbackquery.data.replace('setclass_', '')
    userid = callbackquery.from_user.id
    firstname = callbackquery.from_user.first_name
    currenttime = int(time.time())
    
    cursor.execute(f"SELECT class, lastkill FROM killers WHERE userid = {P}", (userid,))
    row = cursor.fetchone()
    
    u_class = row[0] if row else "Пехота"
    lastkill = row[1] if row else 0
    cooldown_sec = 2700 if u_class == "Кавалерия" else 3600
    
    if (currenttime - lastkill) < cooldown_sec:
        timeleft = cooldown_sec - (currenttime - lastkill)
        await callbackquery.answer(f"❌ Нельзя менять класс во время перезарядки! Подожди: {timeleft // 60} мин.", show_alert=True)
        return

    if is_postgres:
        cursor.execute(f"INSERT INTO killers (userid, firstname, class) VALUES ({P}, {P}, {P}) ON CONFLICT(userid) DO UPDATE SET firstname = EXCLUDED.firstname, class = EXCLUDED.class", (userid, firstname, newclass))
    else:
        cursor.execute(f"INSERT INTO killers (userid, firstname, class) VALUES ({P}, {P}, {P}) ON CONFLICT(userid) DO UPDATE SET firstname = {P}, class = {P}", (userid, firstname, newclass, firstname, newclass))
    conn.commit()
    
    await callbackquery.answer(f"Выбран класс: {newclass}!")
    await callbackquery.message.edit_text(f"🪖 Теперь ты сражаешься как: <b>{newclass}</b>!", parse_mode=ParseMode.HTML)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/kill', 'kill', 'зарубить', 'рубить')))
async def killcmd(message: types.Message):
    userid = message.from_user.id
    firstname = message.from_user.first_name
    currenttime = int(time.time())
    
    cursor.execute(f"SELECT kills, coins, lastkill, army, class, shields, boost_atk, boost_coins FROM killers WHERE userid = {P}", (userid,))
    row = cursor.fetchone()
    
    kills = row[0] if row else 0
    coins = row[1] if row else 0
    lastkill = row[2] if row else 0
    army = row[3] if row else "Не выбран"
    u_class = row[4] if row else "Пехота"
    shields = row[5] if row else 0
    b_atk = row[6] if row else 0
    b_coins = row[7] if row else 0
    
    cooldown_sec = 2700 if u_class == "Кавалерия" else 3600
    injury_chance = 10 if u_class == "Кавалерия" else 20
    max_kills = 15 if u_class == "Кавалерия" else 20
    bonus_coins = 0

    if army == "Армия Колчака":
        injury_chance -= 5
        cooldown_sec += 600
    elif army == "Армия Деникина":
        bonus_coins += 5
        injury_chance += 5
    elif army == "Армия Юденича":
        cooldown_sec -= 900
        max_kills = max(1, max_kills - 5)
    elif army == "Армия Миллера":
        cooldown_sec += 900
    elif army == "Войско Донское":
        cooldown_sec -= 600
        injury_chance += 10

    injury_chance = max(0, min(100, injury_chance))

    if (currenttime - lastkill) < cooldown_sec:
        timeleft = cooldown_sec - (currenttime - lastkill)
        await message.answer(f"⏳ Шашка затупилась! Отдохни ещё <b>{timeleft // 60}</b> мин. <b>{timeleft % 60}</b> сек.", parse_mode=ParseMode.HTML)
        return

    if random.randint(1, 100) <= injury_chance:
        if shields > 0:
            cursor.execute(f"UPDATE killers SET shields = shields - 1 WHERE userid = {P}", (userid,))
            conn.commit()
            await message.answer("🛡 <b>Вас пытались ранить в бою!</b> Но ваш Щит принял удар на себя!", parse_mode=ParseMode.HTML)
        else:
            penalty_time = currenttime + 1200
            if is_postgres:
                cursor.execute(f"INSERT INTO killers (userid, firstname, lastkill) VALUES ({P}, {P}, {P}) ON CONFLICT(userid) DO UPDATE SET lastkill = EXCLUDED.lastkill", (userid, firstname, penalty_time))
            else:
                cursor.execute(f"INSERT INTO killers (userid, firstname, lastkill) VALUES ({P}, {P}, {P}) ON CONFLICT(userid) DO UPDATE SET lastkill = {P}", (userid, firstname, penalty_time, penalty_time))
            conn.commit()
            await message.answer("🩸 <b>ВАШЕ БОЕВОЕ РАНЕНИЕ!</b> +20 минут к кулдауну!", parse_mode=ParseMode.HTML)
            return

    gainedkills = random.randint(1, max_kills)
    is_drozd_crit = False
    if army == "Дроздовская дивизия" and random.randint(1, 100) <= 10:
        gainedkills *= 2
        is_drozd_crit = True

    if b_atk == 1: gainedkills *= 2
    gainedcoins = gainedkills + bonus_coins

    is_komuch_debuff = False
    if army == "Армия КОМУЧа" and random.randint(1, 100) <= 10:
        gainedcoins = max(1, gainedcoins // 2)
        is_komuch_debuff = True

    if b_coins == 1: gainedcoins *= 2
        
    old_rank = get_rank(kills)
    new_rank = get_rank(kills + gainedkills)

    if is_postgres:
        cursor.execute(f"""
            INSERT INTO killers (userid, firstname, kills, coins, lastkill, army, class, boost_atk, boost_coins) 
            VALUES ({P}, {P}, {P}, {P}, {P}, {P}, {P}, 0, 0) 
            ON CONFLICT(userid) DO UPDATE SET 
                firstname = EXCLUDED.firstname, kills = killers.kills + EXCLUDED.kills, coins = killers.coins + EXCLUDED.coins, lastkill = EXCLUDED.lastkill, boost_atk = 0, boost_coins = 0
        """, (userid, firstname, gainedkills, gainedcoins, currenttime, army, u_class))
    else:
        cursor.execute(f"""
            INSERT INTO killers (userid, firstname, kills, coins, lastkill, army, class, boost_atk, boost_coins) 
            VALUES ({P}, {P}, {P}, {P}, {P}, {P}, {P}, 0, 0) 
            ON CONFLICT(userid) DO UPDATE SET 
                firstname = {P}, kills = kills + {P}, coins = coins + {P}, lastkill = {P}, boost_atk = 0, boost_coins = 0
        """, (userid, firstname, gainedkills, gainedcoins, currenttime, army, u_class, firstname, gainedkills, gainedcoins, currenttime))
    conn.commit()
    
    msg_text = f"⚔️ Взмах шашки! Вы зарубили <b>{gainedkills}</b> большевиков!\n💰 Получено монет: <b>+{gainedcoins}</b>"
    if is_drozd_crit: msg_text += "\n🦅 <b>ПСИХИЧЕСКАЯ АТАКА!</b> Дроздовский бафф удвоил ваши фраги!"
    if is_komuch_debuff: msg_text += "\n📜 <b>НАЛОГИ КОМУЧа!</b> Вы получили в 2 раза меньше монет!"
    
    if old_rank != new_rank:
        msg_text += f"\n\n🎉 <b>ПОЗДРАВЛЯЕМ С ПОВЫШЕНИЕМ!</b> Новое звание: <b>{new_rank}</b>!"
    
    await message.answer(msg_text, parse_mode=ParseMode.HTML)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/shop', 'shop', 'магазин', 'лавка')))
async def shopcmd(message: types.Message):
    userid = message.from_user.id
    cursor.execute(f"SELECT army FROM killers WHERE userid = {P}", (userid,))
    row = cursor.fetchone()
    army = row[0] if row else "Не выбран"

    shield_price = 5 if army == "Армия Врангеля" else 10
    skip_price = 45 if army == "Армия Врангеля" else 40
    boost_price = 50 if army == "Армия Миллера" else 60

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=f"⏳ Скип кулдауна ({skip_price} монет)", callback_data="buy_skip")],
            [types.InlineKeyboardButton(text=f"🛡 Щит от ранений/атак ({shield_price} монет)", callback_data="buy_shield")],
            [types.InlineKeyboardButton(text=f"⚡️ Усилитель атаки x2 ({boost_price} монет)", callback_data="buy_batk")],
            [types.InlineKeyboardButton(text=f"💰 Усилитель монет x2 ({boost_price} монет)", callback_data="buy_bcoins")]
        ]
    )
    await message.answer("🛒 <b>ПОЛКОВАЯ ЛАВКА И МАГАЗИН:</b>", reply_markup=kb, parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: c.data and c.data.startswith('buy_'))
async def processbuy(callbackquery: types.CallbackQuery):
    item = callbackquery.data.replace('buy_', '')
    userid = callbackquery.from_user.id
    
    cursor.execute(f"SELECT coins, shields, boost_atk, boost_coins, army FROM killers WHERE userid = {P}", (userid,))
    row = cursor.fetchone()
    coins = row[0] if row else 0
    army = row[4] if row else "Не выбран"
    
    shield_price = 5 if army == "Армия Врангеля" else 10
    skip_price = 45 if army == "Армия Врангеля" else 40
    boost_price = 50 if army == "Армия Миллера" else 60

    if item == "skip":
        if coins < skip_price:
            await callbackquery.answer(f"❌ Не хватает монет!", show_alert=True)
            return
        cursor.execute(f"UPDATE killers SET coins = coins - {P}, lastkill = 0 WHERE userid = {P}", (skip_price, userid))
        conn.commit()
        await callbackquery.answer("✅ Кулдаун сброшен!", show_alert=True)
        
    elif item == "shield":
        if coins < shield_price:
            await callbackquery.answer(f"❌ Не хватает монет!", show_alert=True)
            return
        cursor.execute(f"UPDATE killers SET coins = coins - {P}, shields = shields + 1 WHERE userid = {P}", (shield_price, userid))
        conn.commit()
        await callbackquery.answer("🛡 Куплен 1 Щит!", show_alert=True)
        elif item == "batk":
        if coins < boost_price:
            await callbackquery.answer(f"❌ Не хватает монет!", show_alert=True)
            return
        cursor.execute(f"UPDATE killers SET coins = coins - {P}, boost_atk = 1 WHERE userid = {P}", (boost_price, userid))
        conn.commit()
        await callbackquery.answer("⚡️ Буст атаки x2 куплен!", show_alert=True)

    elif item == "bcoins":
        if coins < boost_price:
            await callbackquery.answer(f"❌ Не хватает монет!", show_alert=True)
            return
        cursor.execute(f"UPDATE killers SET coins = coins - {P}, boost_coins = 1 WHERE userid = {P}", (boost_price, userid))
        conn.commit()
        await callbackquery.answer("💰 Буст монет x2 куплен!", show_alert=True)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/attack', 'attack', 'напасть')))
async def attackcmd(message: types.Message):
    if not message.reply_to_message:
        await message.answer("⚠️ Чтобы напасть на игрока, ответьте (Reply) командой /attack!", parse_mode=ParseMode.HTML)
        return

    attacker_id = message.from_user.id
    target_id = message.reply_to_message.from_user.id
    if attacker_id == target_id: return

    cursor.execute(f"SELECT coins, army FROM killers WHERE userid = {P}", (attacker_id,))
    row_att = cursor.fetchone()
    att_coins = row_att[0] if row_att else 0
    att_army = row_att[1] if row_att else "Не выбран"
    attack_cost = 25 if att_army == "Дроздовская дивизия" else 15

    if att_coins < attack_cost:
        await message.answer(f"❌ Нападение стоит {attack_cost} монет!", parse_mode=ParseMode.HTML)
        return

    cursor.execute(f"SELECT shields, lastkill, army FROM killers WHERE userid = {P}", (target_id,))
    row_tar = cursor.fetchone()
    tar_shields = row_tar[0] if row_tar else 0
    tar_lastkill = row_tar[1] if row_tar else 0
    tar_army = row_tar[2] if row_tar else "Не выбран"

    cursor.execute(f"UPDATE killers SET coins = coins - {P} WHERE userid = {P}", (attack_cost, attacker_id))
    target_name = message.reply_to_message.from_user.first_name.replace("<", "&lt;").replace(">", "&gt;")

    if tar_shields > 0:
        cursor.execute(f"UPDATE killers SET shields = shields - 1 WHERE userid = {P}", (target_id,))
        conn.commit()
        await message.answer(f"🛡 <b>НАПАДЕНИЕ ОТБИТО!</b> У <b>{target_name}</b> был ЩИТ!", parse_mode=ParseMode.HTML)
    else:
        currenttime = int(time.time())
        penalty_sec = 600 if tar_army == "Армия КОМУЧа" else 1200
        new_kd = max(currenttime, tar_lastkill) + penalty_sec
        cursor.execute(f"UPDATE killers SET lastkill = {P} WHERE userid = {P}", (new_kd, target_id))
        conn.commit()
        await message.answer(f"⚔️ <b>УСПЕШНАЯ ВЫЛАЗКА!</b> +{penalty_sec // 60} минут к кулдауну <b>{target_name}</b>!", parse_mode=ParseMode.HTML)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/army', 'army', 'армия')))
async def armycmd(message: types.Message):
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="❄️ Армия Колчака (-5% ранение | +10м КД)", callback_data="set_Армия Колчака")],
            [types.InlineKeyboardButton(text="⚜️ Армия Деникина (+5 монет за бой | +5% ранение)", callback_data="set_Армия Деникина")],
            [types.InlineKeyboardButton(text="🛡 Армия Врангеля (Щит 5 монет | СкипКД 45 монет)", callback_data="set_Армия Врангеля")],
            [types.InlineKeyboardButton(text="⚔️ Армия Юденича (-15м КД | -5 макс. фрагов)", callback_data="set_Армия Юденича")],
            [types.InlineKeyboardButton(text="🌲 Армия Миллера (Бусты 50 монет | +15м КД)", callback_data="set_Армия Миллера")],
            [types.InlineKeyboardButton(text="🦅 Дроздовская дивизия (10% Крит X2 | /attack 25м)", callback_data="set_Дроздовская дивизия")],
            [types.InlineKeyboardButton(text="📜 Армия КОМУЧа (+10м КД при атаке | 10% x0.5 монет)", callback_data="set_Армия КОМУЧа")],
            [types.InlineKeyboardButton(text="🐎 Войско Донское (-10м КД | +10% ранение)", callback_data="set_Войско Донское")]
        ]
    )
    await message.answer("🚩 <b>Выбери Белую Армию:</b>", reply_markup=kb, parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: c.data and c.data.startswith('set_'))
async def processarmychoice(callbackquery: types.CallbackQuery):
    armyname = callbackquery.data.replace('set_', '')
    userid = callbackquery.from_user.id
    firstname = callbackquery.from_user.first_name
    
    if is_postgres:
        cursor.execute(f"INSERT INTO killers (userid, firstname, army) VALUES ({P}, {P}, {P}) ON CONFLICT(userid) DO UPDATE SET firstname = EXCLUDED.firstname, army = EXCLUDED.army", (userid, firstname, armyname))
    else:
        cursor.execute(f"INSERT INTO killers (userid, firstname, army) VALUES ({P}, {P}, {P}) ON CONFLICT(userid) DO UPDATE SET firstname = {P}, army = {P}", (userid, firstname, armyname, firstname, armyname))
    conn.commit()
    
    await callbackquery.answer(f"Ты вступил в: {armyname}!")
    await callbackquery.message.edit_text(f"⚔️ Отлично! Теперь ты сражаешься за: <b>{armyname}</b>!", parse_mode=ParseMode.HTML)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/sostav', 'sostav', 'состав')))
async def sostavcmd(message: types.Message):
    userid = message.from_user.id
    cursor.execute(f"SELECT army FROM killers WHERE userid = {P}", (userid,))
    row = cursor.fetchone()
    
    if not row or row[0] == "Не выбран":
        await message.answer("Ты еще не выбрал армию! Напиши /army.", parse_mode=ParseMode.HTML)
        return
        
    armyname = row[0]
    cursor.execute(f"SELECT firstname, kills, userid FROM killers WHERE army = {P} ORDER BY kills DESC LIMIT 20", (armyname,))
    members = cursor.fetchall()
    
    text = f"👥 <b>СОСТАВ ПОЛКА [{armyname}]:</b>\n\n"
    for index, (name, kills, member_id) in enumerate(members, start=1):
        player_name = name.replace("<", "&lt;").replace(">", "&gt;") if name else f"Казак {member_id}"
        text += f"{index}. <b>{player_name}</b> ({get_rank(kills)}) — <b>{kills}</b> фрагов\n"
        
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/top', 'top', 'топ')))
async def topcmd(message: types.Message):
    cursor.execute("SELECT firstname, kills, army FROM killers ORDER BY kills DESC LIMIT 10")
    topusers = cursor.fetchall()
    
    text = "🏆 <b>Топ лучших гвардейцев:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for index, (name, kills, army) in enumerate(topusers, start=1):
        place = medals[index-1] if index <= 3 else f"{index}."
        armyinfo = f" [{army}]" if army and army != 'Не выбран' else ""
        player_name = name.replace("<", "&lt;").replace(">", "&gt;") if name else "Неизвестный"
        text += f"{place} <b>{player_name}</b>{armyinfo} — {get_rank(kills)} (<b>{kills}</b> фрагов)\n"
        
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(lambda msg: msg.text and msg.text.lower().startswith(('/armies', 'armies', 'армии')))
async def armiescmd(message: types.Message):
    cursor.execute("SELECT SUM(kills) FROM killers")
    total_all_kills = cursor.fetchone()[0] or 0

    cursor.execute("SELECT army, SUM(kills) as totalkills FROM killers WHERE army != 'Не выбран' GROUP BY army ORDER BY totalkills DESC")
    armiestop = cursor.fetchall()
    
    text = f"📊 <b>ОБЩАЯ СТАТИСТИКА ФРОНТА:</b>\n💀 Всего убито большевиков: <b>{total_all_kills}</b>\n\n🚩 <b>РЕЙТИНГ АРМИЙ:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for index, (armyname, totalkills) in enumerate(armiestop, start=1):
        place = medals[index-1] if index <= 3 else f"{index}."
        text += f"{place} <b>{armyname}</b> — <b>{totalkills}</b> большевиков\n"
        
    await message.answer(text, parse_mode=ParseMode.HTML)

async def main():
    logging.basicConfig(level=logging.INFO)
    await setup_bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


