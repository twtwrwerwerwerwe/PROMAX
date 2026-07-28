# -*- coding: utf-8 -*-
"""
bot/utils/text_templates.py — Botning barcha matnlari (o'zbek tilida).

Barcha foydalanuvchiga ko'rinadigan matnlar shu yerda markazlashgan —
matnni o'zgartirish uchun boshqa hech qanday faylni ochish shart emas.
"""
from __future__ import annotations


class T:
    """Text constants namespace."""

    # ---------------- START ----------------
    START_GREETING = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "🚖 Ushbu bot ko'plab yirik Telegram guruhlari bilan birgalikda ishlaydi "
        "va sizning e'loningizni ushbu guruhlarga avtomatik tarzda muntazam yuborib turadi.\n\n"
        "📢 Hozirda bot <b>{groups_count}</b> ta guruh bilan ishlamoqda.\n\n"
        "Davom etish uchun quyidagi tugmani bosing 👇"
    )
    CONTINUE_BUTTON = "➡️ Davom etish"
    GROUP_ONLY_IGNORED = ""  # bot guruhda umuman javob bermaydi

    # ---------------- PAYMENT ----------------
    CHOOSE_TARIFF = (
        "💳 <b>Tariflardan birini tanlang</b>\n\n"
        "Botdan foydalanish uchun quyidagi tariflardan birini tanlang:"
    )
    TARIFF_BUTTON_FMT = "{label} — {price} so'm"

    CHOOSE_PAYMENT_METHOD = (
        "💰 <b>To'lov usulini tanlang</b>\n\n"
        "Tanlangan tarif: <b>{tariff_label}</b>\n"
        "Narxi: <b>{price} so'm</b>"
    )
    PAY_METHOD_RECEIPT = "🧾 Chek orqali to'lash"
    PAY_METHOD_CLICK = "💳 Click"
    PAY_METHOD_PAYME = "💳 Payme"
    PAY_METHOD_CONTACT_ADMIN = "👨‍💻 Admin bilan bog'lanish"

    PAYMENT_METHOD_UNAVAILABLE = (
        "⚠️ Ushbu to'lov usuli hozircha mavjud emas.\n"
        "Iltimos boshqa usulni tanlang yoki administrator bilan bog'laning."
    )

    RECEIPT_CARD_INFO = (
        "🧾 <b>To'lov uchun karta ma'lumotlari</b>\n\n"
        "💳 Karta raqami: <code>{card_number}</code>\n"
        "👤 Egasi: {card_owner}\n\n"
        "To'lovni amalga oshirgach, <b>chek rasmini</b> shu yerga yuboring."
    )
    ASK_RECEIPT_PHOTO = "📸 Iltimos, to'lov chekining rasmini (screenshot) yuboring."
    RECEIPT_INVALID = "⚠️ Iltimos, faqat rasm (screenshot) yuboring."
    RECEIPT_RECEIVED = (
        "✅ Chek qabul qilindi.\n"
        "⏳ To'lovingiz administrator tomonidan tez orada tekshiriladi.\n"
        "Iltimos, biroz kuting."
    )

    CONTACT_ADMIN_PAYMENT = (
        "👨‍💻 <b>Administrator bilan bog'lanish</b>\n\n"
        "To'lov qilish uchun administratorga murojaat qiling:\n"
        "👤 {admin_name}\n"
        "📞 {admin_phone}\n\n"
        "So'rovingiz administratorga yuborildi."
    )

    PAYMENT_PENDING_ADMIN_NOTIFY = (
        "🆕 <b>Yangi to'lov so'rovi</b>\n\n"
        "👤 Foydalanuvchi: {user_display} (<code>{user_id}</code>)\n"
        "📦 Tarif: {tariff_label}\n"
        "💵 Narx: {price} so'm\n"
        "💳 Usul: {method_label}\n"
    )

    PAYMENT_APPROVED_USER = (
        "✅ <b>To'lov tasdiqlandi!</b>\n\n"
        "📦 Tarif: {tariff_label}\n"
        "{expiry_line}\n"
        "Endi botdan foydalanish uchun telefon raqamingizni yuboring."
    )
    PAYMENT_APPROVED_LIFETIME_LINE = "♾ Muddat: Umrbod"
    PAYMENT_APPROVED_EXPIRY_LINE = "📅 Amal qilish muddati: {end_date}"

    PAYMENT_REJECTED_USER = (
        "❌ <b>To'lovingiz rad etildi.</b>\n\n"
        "Sabab: {reason}\n\n"
        "Qaytadan urinib ko'ring yoki administrator bilan bog'laning:\n"
        "👤 {admin_name}\n"
        "📞 {admin_phone}"
    )

    PAYMENT_ALREADY_PROCESSED = "⚠️ Ushbu to'lov allaqachon ko'rib chiqilgan."

    ASK_PHONE = (
        "✅ To'lov tasdiqlandi.\n\n"
        "Endi botdan foydalanish uchun telefon raqamingizni yuboring."
    )
    ASK_PHONE_SHARE_BUTTON = "📱 Raqamni yuborish"
    PHONE_INVALID = (
        "⚠️ Telefon raqami noto'g'ri formatda.\n\n"
        "Iltimos quyidagicha yuboring:\n"
        "<code>998901234567</code> yoki <code>+998901234567</code>"
    )
    PHONE_SAVED = "✅ Telefon raqamingiz saqlandi: <b>{phone}</b>"

    # ---------------- MAIN MENU ----------------
    MAIN_MENU_TEXT = "🏠 <b>Asosiy menyu</b>\n\nQuyidagi bo'limlardan birini tanlang:"
    BTN_SEND_AD = "📢 E'lon yuborish"
    BTN_EMERGENCY_STOP = "⛔ To'liq to'xtatish"
    BTN_CONTACT_ADMIN = "👨‍💻 Admin bilan bog'lanish"
    BTN_ADMIN_PANEL = "🛠 Admin panel"

    # ---------------- ADVERTISEMENT CREATION ----------------
    ASK_AD_TEXT = (
        "📝 <b>E'lon matnini yuboring.</b>\n\n"
        "━━━━━━━━━━━━━━\n"
        "𝗠𝗜𝗦𝗢𝗟\n\n"
        "🚖 Toshkent ➜ Samarqand\n"
        "👤 2 ta odam olaman.\n"
        "🕒 Bugun soat 18:00.\n"
        "━━━━━━━━━━━━━━\n\n"
        "ℹ️ Agar telefon raqamingizni yozmasangiz, bot avtomatik ravishda "
        "profilingizda saqlangan telefon raqamingizni e'lon oxiriga qo'shib yuboradi."
    )
    AD_TEXT_TOO_LONG = "⚠️ E'lon matni juda uzun. Iltimos qisqaroq matn yuboring (maksimal {max_len} belgi)."
    AD_TEXT_EMPTY = "⚠️ Iltimos, matn ko'rinishida e'lon yuboring."

    ASK_INTERVAL = "⏰ <b>Intervalni tanlang.</b>"
    INTERVAL_BUTTON_FMT = "🕔 {minutes} minut"

    CONFIRM_AD_TEMPLATE = (
        "━━━━━━━━━━━━━━\n"
        "✅ <b>Ma'lumotlaringiz</b>\n\n"
        "📢 <b>E'lon:</b>\n{ad_text}\n"
        "━━━━━━━━━━━━━━\n"
        "⏰ <b>Interval:</b>\n{interval} minut\n"
        "━━━━━━━━━━━━━━"
    )
    BTN_START_AD = "▶️ Boshlash"
    BTN_CANCEL = "❌ Bekor qilish"

    AD_CANCELLED = "❌ Ma'lumotlar bekor qilindi.\n\n🏠 Asosiy menyuga qaytildi."

    AD_STARTED = (
        "✅ E'lon yuborish boshlandi.\n"
        "🟢 Holat: Aktiv\n"
        "━━━━━━━━━━━━━━\n"
        "⚠️ <b>Eslatma</b>\n\n"
        "Agar e'lonni to'xtatishni unutib qo'ysangiz, bot xavfsizlik uchun uni "
        "avtomatik ravishda 24 soatdan so'ng to'xtatadi."
    )

    ALREADY_ACTIVE_AD = (
        "⚠️ Sizda allaqachon aktiv e'lon mavjud.\n\n"
        "Avval uni to'xtating yoki tahrirlang."
    )

    SUBSCRIPTION_REQUIRED = (
        "⚠️ Botdan foydalanish uchun avval to'lov qilishingiz kerak."
    )
    SUBSCRIPTION_EXPIRED = (
        "⏰ Sizning obunangiz muddati tugadi.\n\n"
        "Botdan foydalanishni davom ettirish uchun qaytadan to'lov qiling."
    )
    SUBSCRIPTION_REMINDER_3DAY = (
        "🔔 Eslatma: obunangiz muddati <b>3 kundan</b> so'ng tugaydi.\n"
        "Muddatni uzaytirish uchun to'lov qiling."
    )
    SUBSCRIPTION_REMINDER_1DAY = (
        "🔔 Eslatma: obunangiz muddati <b>ertaga</b> tugaydi.\n"
        "Muddatni uzaytirish uchun to'lov qiling."
    )
    PHONE_NOT_REGISTERED = "⚠️ Avval telefon raqamingizni yuboring."

    # ---------------- ACTIVE AD PANEL ----------------
    AD_STATUS_PANEL_TEMPLATE = (
        "📢 <b>Sizning e'loningiz</b>\n\n"
        "{status_emoji} Holat: <b>{status_label}</b>\n"
        "⏰ Interval: {interval} minut\n"
        "📨 Yuborilgan xabarlar: {sent_count} ta\n"
        "🕐 Boshlangan vaqt: {started_at}\n"
    )
    BTN_PAUSE = "⏸ Pauza qilish"
    BTN_RESUME = "▶️ Davom ettirish"
    BTN_EDIT = "✏️ Tahrirlash"
    BTN_STOP = "⛔ To'xtatish"
    BTN_BACK = "⬅️ Ortga"

    AD_PAUSED = "⏸ E'lon vaqtinchalik pauza qilindi."
    AD_RESUMED = "▶️ E'lon davom ettirildi."
    AD_STOPPED = "⛔ E'lon to'xtatildi.\n\n🏠 Asosiy menyuga qaytildi."
    AD_AUTO_STOPPED = "⏰ 24 soat tugadi.\n\nE'lon avtomatik ravishda to'xtatildi."

    # ---------------- EDIT ----------------
    EDIT_CHOOSE_WHAT = "Nimani tahrirlamoqchisiz?"
    BTN_EDIT_TEXT = "📝 E'lonni"
    BTN_EDIT_INTERVAL = "⏰ Intervalni"
    BTN_EDIT_BOTH = "🔄 Ikkalasini ham"

    ASK_NEW_AD_TEXT = "📝 Yangi e'lonni yuboring."
    AD_TEXT_UPDATED = "✅ E'lon yangilandi.\n🚀 Yuborish davom ettirilmoqda."
    AD_INTERVAL_UPDATED = "✅ Interval yangilandi.\n⏰ Endi e'lon yangi interval bo'yicha yuboriladi."
    AD_BOTH_UPDATED = "✅ E'lon yangilandi.\n✅ Interval yangilandi.\n🟢 E'lon aktiv holatda davom etmoqda."

    # ---------------- EMERGENCY STOP ----------------
    EMERGENCY_STOP_DONE = (
        "✅ Barcha e'lon yuborish jarayonlari to'liq to'xtatildi.\n\n"
        "🏠 Asosiy menyuga qaytildi."
    )
    NO_ACTIVE_AD_TO_STOP = "ℹ️ Sizda hozircha to'xtatish uchun faol e'lon mavjud emas."

    # ---------------- CONTACT ADMIN ----------------
    CONTACT_ADMIN_TEXT = (
        "━━━━━━━━━━━━━━\n"
        "👨‍💻 <b>Administrator</b>\n\n"
        "Ism:\n{admin_name}\n\n"
        "Telefon:\n{admin_phone}\n"
        "━━━━━━━━━━━━━━\n\n"
        "Agar yordam kerak bo'lsa administrator bilan bog'lanishingiz mumkin."
    )
    BTN_PROFILE = "👤 Profilga o'tish"

    # ---------------- ADVERTISEMENT MESSAGE SENT TO GROUPS ----------------
    GROUP_AD_TEMPLATE = (
        "━━━━━━━━━━━━━━━━━━\n"
        "🚖 <b>SHAFYOR E'LONI</b>\n\n"
        "{ad_text}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    BTN_CONTACT_DRIVER = "📞 Shafyorga bog'lanish"

    # ---------------- ADMIN ----------------
    ADMIN_ACCESS_DENIED = "⛔ Sizda ushbu bo'limga kirish huquqi yo'q."
    ADMIN_PANEL_TITLE = "🛠 <b>Admin Panel</b>\n\nBo'limlardan birini tanlang:"
    BTN_ADMIN_STATS = "📊 Statistikalar"
    BTN_ADMIN_USERS = "👥 Foydalanuvchilar"
    BTN_ADMIN_PAYMENTS = "💳 To'lovlar"
    BTN_ADMIN_ACTIVE_ADS = "📢 Faol e'lonlar"
    BTN_ADMIN_STOPPED_ADS = "🛑 To'xtatilgan e'lonlar"
    BTN_ADMIN_GROUPS = "🏘 Guruhlarni boshqarish"
    BTN_ADMIN_SETTINGS = "⚙ Sozlamalar"

    ADMIN_STATS_TEMPLATE = (
        "📊 <b>Statistikalar</b>\n\n"
        "👥 Jami foydalanuvchilar: {total_users}\n"
        "✅ Faol obunalar: {active_subs}\n"
        "📢 Faol e'lonlar: {active_ads}\n"
        "🛑 To'xtatilgan e'lonlar: {stopped_ads}\n"
        "🏘 Faol guruhlar: {active_groups}\n"
        "💳 Kutilayotgan to'lovlar: {pending_payments}\n"
        "💰 Jami tasdiqlangan to'lovlar: {approved_payments}\n"
    )

    ADMIN_GROUPS_MENU_TITLE = "🏘 <b>Guruhlarni boshqarish</b>"
    BTN_ADD_GROUP = "➕ Guruh qo'shish"
    BTN_LIST_GROUPS = "📋 Guruhlar ro'yxati"
    BTN_DELETE_GROUP = "🗑 Guruhni o'chirish"
    BTN_REFRESH_GROUPS = "🔄 Yangilash"

    ASK_GROUP_ID = (
        "Guruh ID sini yuboring.\n\n"
        "Masalan:\n<code>-1001234567890</code>\n\n"
        "ℹ️ Telegram supergroup ID'lari odatda <code>-100</code> bilan boshlanadi."
    )
    GROUP_ADDED_OK = "✅ Guruh muvaffaqiyatli qo'shildi."
    GROUP_NOT_ADMIN = "❌ Bot ushbu guruhda administrator emas.\n\nAvval botni administrator qiling."
    GROUP_NOT_FOUND = "❌ Guruh topilmadi. Bot bu guruhga kira olmayapti."
    GROUP_NOT_A_GROUP = "❌ Berilgan ID guruh emas (kanal yoki shaxsiy chat)."
    GROUP_ALREADY_EXISTS = "⚠️ Ushbu guruh allaqachon ro'yxatda mavjud."
    GROUP_INVALID_ID = "⚠️ Guruh ID formati noto'g'ri. Raqamlardan iborat bo'lishi kerak, masalan -1001234567890"

    GROUPS_LIST_EMPTY = "ℹ️ Hozircha hech qanday guruh qo'shilmagan."
    GROUP_DELETE_CONFIRM = "Haqiqatan ham ushbu guruhni o'chirmoqchimisiz?\n\n🏘 {title}"
    BTN_YES = "✅ Ha"
    BTN_NO = "❌ Yo'q"
    GROUP_DELETED = "✅ Guruh o'chirildi."

    ADMIN_PAYMENTS_MENU_TITLE = "💳 <b>To'lovlar</b>"
    BTN_PENDING_PAYMENTS = "⏳ Kutilayotganlar"
    BTN_APPROVED_PAYMENTS = "✅ Tasdiqlanganlar"
    BTN_REJECTED_PAYMENTS = "❌ Rad etilganlar"
    PAYMENTS_LIST_EMPTY = "ℹ️ Bu ro'yximda hozircha to'lovlar yo'q."
    BTN_APPROVE = "✅ Tasdiqlash"
    BTN_REJECT = "❌ Rad etish"
    ASK_REJECT_REASON = "Rad etish sababini yozing:"
    PAYMENT_DECIDED_NOTICE_APPROVED = "✅ Tasdiqlandi (admin: {admin_name})"
    PAYMENT_DECIDED_NOTICE_REJECTED = "❌ Rad etildi (admin: {admin_name})\nSabab: {reason}"

    ADMIN_USERS_LIST_EMPTY = "ℹ️ Foydalanuvchilar topilmadi."
    ADMIN_USER_CARD = (
        "👤 <b>{display_name}</b>\n"
        "🆔 <code>{telegram_id}</code>\n"
        "📞 {phone}\n"
        "💳 Obuna holati: {sub_status}\n"
        "📅 Ro'yxatdan o'tgan: {created_at}\n"
    )
    BTN_BAN_USER = "🚫 Bloklash"
    BTN_UNBAN_USER = "✅ Blokdan chiqarish"
    USER_BANNED = "🚫 Foydalanuvchi bloklandi."
    USER_UNBANNED = "✅ Foydalanuvchi blokdan chiqarildi."
    USER_IS_BANNED_MSG = "⛔ Siz bloklangansiz. Botdan foydalana olmaysiz."

    ADMIN_ADS_LIST_EMPTY = "ℹ️ Bu ro'yxatda hozircha e'lonlar yo'q."
    BTN_FORCE_STOP = "⛔ Majburiy to'xtatish"
    AD_FORCE_STOPPED = "⛔ E'lon administrator tomonidan majburiy to'xtatildi."
    AD_FORCE_STOPPED_USER_NOTICE = "⛔ Sizning e'loningiz administrator tomonidan to'xtatildi."

    ADMIN_SETTINGS_TITLE = "⚙ <b>Sozlamalar</b>"
    ADMIN_SETTINGS_BODY = (
        "🔧 Bir vaqtning o'zida yuborish chegarasi: {concurrency}\n"
        "⏱ Guruhlarni tekshirish oralig'i: {group_check_hours} soat\n"
        "⏰ E'lon avtomatik to'xtash vaqti: {auto_stop_hours} soat\n"
    )

    BACK_TO_MAIN_MENU = "🏠 Asosiy menyuga qaytildi."
    GENERIC_ERROR = "⚠️ Kutilmagan xatolik yuz berdi. Iltimos qaytadan urinib ko'ring."
    UNKNOWN_CALLBACK = "⚠️ Ushbu tugma muddati eskirgan. Iltimos qaytadan boshlang."
