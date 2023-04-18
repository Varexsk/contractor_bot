#
# Основной код бота
#

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor
from aiogram.utils.exceptions import MessageNotModified, MessageToDeleteNotFound
from typing import Set

import cnt_logging
import handlers
from cnt_logging import cnt_logger
from db import database

api_token = '5263646133:AAGc8B-LJShL_PjmMiRN5hI_pPm_wYhjoPE'
# api_token = '5278381984:AAFRjCY3JLxegDUaq36zVuGsZzLpj7e_AZI'
bot = Bot(token=api_token)
dp = Dispatcher(bot, storage=MemoryStorage())

region_names = ["СПБ", "МСКиМО", "СЗФО", "ЦФО", "ПФО", "УФО", "СФО", "ЮФО"]


class ContractorState(StatesGroup):
    wait_phone = State()
    wait_fullname = State()
    wait_reg = State()
    wait_agent_type = State()


class RequestState(StatesGroup):
    wait_type = State()
    wait_name = State()
    wait_image = State()
    wait_text = State()


class AdminState(StatesGroup):
    wait_admin_pass = State()
    wait_reg = State()


class PriceState(StatesGroup):
    wait_price = State()


class EditState(StatesGroup):
    wait_text = State()


class GetInfoState(StatesGroup):
    wait_info = State()
    wait_reply_info = State()


@dp.message_handler(state='*', commands=['admin'])
async def admin(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Введите пароль')
    await AdminState.wait_admin_pass.set()


@dp.message_handler(state='*', commands=['start'])
async def process_start_command(message: types.Message, state: FSMContext):
    await state.finish()
    await contractor_start(message)


@dp.message_handler(state='*', commands=['help'])
async def process_start_command(message: types.Message, state: FSMContext):
    await state.finish()
    await help_info(message)


async def help_info(message: types.Message):
    await message.answer(text="""
    <i>Для каждого зарегистрированного пользователя чат абсолютно приватный. Все заявки отображаются лично для Вас. 
    Информация никому не распространяется.</i>
    
    Инструкция пользования:
    1. Пройдите регистрацию.
        1. 1. Введите ваш номер телефона для связи с вами в случае выигрыша тендора. Enter для следующего шага.
            Телефон должен быть длинной в 11 цифр, включая "8" в начале номера телефона.
        1. 2. Напишите название вашей организации. Enter для следующего шага.
        1. 3. Выберите регион(ы), ваша организация в которой может выполнить условия по заявке.
        1. 4. Выберите по какому типу работает ваша организация: АХО или реклама.
    2. Нажмите на кнопку "Обновить заявки", чтобы увидеть актуальные и принять по ним участие.
        Заявки будут отображаться по Вашим регионам и по Вашему типу.
        В появившемся списке можно увидеть последнюю предложенную минимальную стоимость.
    3. Для участия в ценовой гонке установите свою стоимость, нажав на кнопку "Предложить свою цену"
        3. 1. Введите сумму. Enter для следующего шага.
    Кнопка "Обновить" показывает последнюю минимальную стоимость и отображает информацию о Вашей цене.
    Дополнительно отображается информация лидирует ли Ваша предложенная стоимость.
    По кнопке "Задать вопрос" Вы переходите на анонимный приватный диалог.
    Вы можете задать вопрос по заявке заказчику. Ответ по вопросу Вы получите также приватно в этом чате от лица бота.
    
    <i>Разработано командой ARP ООО "ВсеИнструменты.Ру"</i>
    """,
                         parse_mode=types.ParseMode.HTML)


@dp.message_handler(state=AdminState.wait_admin_pass)
async def set_admin(message: types.Message, state: FSMContext):
    if message.text != 'ViBi12002022':
        await message.answer('Неправильный пароль. Введите заново:')
        return
    await state.finish()
    rg = types.InlineKeyboardMarkup(row_width=4).add(
        *[types.InlineKeyboardButton(text=x, callback_data=f'chooseReg_admin_{x}') for x in region_names]
    )
    await message.answer("Выберите регион(ы)", reply_markup=rg)
    await AdminState.next()


@dp.callback_query_handler(lambda c: c.data.startswith('chooseReg'),
                           state='*')
async def call_set_region(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    agent_type = data[1]
    reg = data[2]
    accept_btn = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(text='Подтвердить', callback_data=f'acceptReg_{agent_type}')
    )
    if 'choose_rg_msg' in (s := await state.get_data()) and 'chosen_regs' in s:
        msg_id = s.get('choose_rg_msg')
        chosen_regs = set(s.get('chosen_regs'))
        if reg in chosen_regs:
            if len(chosen_regs) <= 1:
                await call.answer()
                return
            chosen_regs.remove(reg)
        else:
            chosen_regs.add(reg)
        try:
            regs = ", ".join([rg for rg in chosen_regs])
            msg = await bot.edit_message_text(chat_id=call.message.chat.id,
                                              message_id=msg_id,
                                              text=f'Вы выбрали: <b>{regs}</b>',
                                              parse_mode=types.ParseMode.HTML,
                                              reply_markup=accept_btn)
            msg_id = msg.message_id
        except MessageNotModified as e:
            cnt_logger.error(e)
        finally:
            await call.answer()
    else:
        chosen_regs = {reg}
        msg = await call.message.answer(f'Вы выбрали: <b>{reg}</b>',
                                        parse_mode=types.ParseMode.HTML,
                                        reply_markup=accept_btn)
        msg_id = msg.message_id
    await state.update_data(choose_rg_msg=msg_id, chosen_regs=chosen_regs)
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('acceptReg'), state='*')
async def accept_reg(call: types.CallbackQuery, state: FSMContext):
    call_data = call.data.split('_')
    if call_data[1] == 'admin':
        await get_admin_region(call, state)
    else:
        await get_contr_region(call, state)


async def get_admin_region(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    if 'chosen_regs' not in state_data:
        await call.message.answer('Не выбраны регионы')
        return
    chosen_regs = state_data.get('chosen_regs')
    await database.add_user(call.from_user.id, '', '', ', '.join(chosen_regs), 0)
    await admin_login(call.message)
    await state.finish()


async def admin_login(message: types.Message):
    btn = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn.add(
        types.KeyboardButton('Создать заявку'),
        types.KeyboardButton('Архивировать заявку'),
        types.KeyboardButton('Список моих заявок'),
        types.KeyboardButton('Архив заявок')
    )
    await message.answer('Авторизация выполнена. Вам доступны функции администратора',
                         reply_markup=btn)


@dp.message_handler(text='Архив заявок')
async def archive_request(message: types.Message, state: FSMContext):
    await state.finish()
    admin_list = await handlers.get_admin_list()
    if not admin_list or message.from_user.id not in admin_list:
        return
    await request_list_admin(message, state, archive=1)


@dp.message_handler(text="Список моих заявок")
async def request_list_admin(message: types.Message, state: FSMContext, archive=0):
    await state.finish()
    if not (admin_id_list := await handlers.get_admin_list()) or message.from_user.id not in admin_id_list:
        return
    request_list = await handlers.get_all_requests(tg_id=message.from_user.id, is_archived=archive)
    if not request_list:
        await message.answer('У вас нет заявок')
        return
    for request in request_list:
        admin_request_menu = types.InlineKeyboardMarkup().add(*[
            types.InlineKeyboardButton('Информация о предложенных ценах',
                                       callback_data=f'get_contractor_{request.id}'),
            types.InlineKeyboardButton('Редактировать Техническое Задание',
                                       callback_data=f'edit_request_{request.id}')
        ])
        await message.answer(f'Заявка с именем <b>{request.title}</b>',
                             reply_markup=admin_request_menu,
                             parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(lambda c: c.data.startswith('edit_request'))
async def edit_request(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer('Введите новое Техническое Задание')
    request_id = call.data.split('_')[2]
    await EditState.wait_text.set()
    await state.update_data(request_id=request_id)


@dp.message_handler(state=EditState.wait_text)
async def text_to_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    request_id = data.get('request_id')
    await database.update_request_text(message.text, request_id)
    await message.answer('Техническое Задание успешно изменено')
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('get_contractor'))
async def get_contractor(call: types.CallbackQuery):
    request_id = call.data.split('_')[2]
    await call.answer()

    min_price_data_list = await handlers.get_min_price_data_list(request_id)
    if not min_price_data_list:
        await call.message.answer('По данному заказу цен нет ☹️')
        return
    flag = False
    for price_data in min_price_data_list:
        cont = await handlers.get_user_data(price_data.tg_id)
        if not cont:
            flag |= False
            continue
        admin_price_menu = types.InlineKeyboardMarkup()
        admin_price_menu.add(types.InlineKeyboardButton('Сделать победителем',
                                                        callback_data=f'winner_{cont.tg_id}_{request_id}'))
        await call.message.answer(f"Заявка №{price_data.request_id}\n"
                                  f"Телефон: <b>{cont.phone}</b>\n"
                                  f"Имя: <b>{cont.fullname}</b>\n"
                                  f"Минимальная цена: <pre>{price_data.price}</pre> ₽\n"
                                  f"Тип: <b>{REQ_TYPE[cont.agent_type - 1]}</b>",
                                  reply_markup=admin_price_menu,
                                  parse_mode=types.ParseMode.HTML)
        flag |= True
    if not flag:
        await error(call.message, 'no user data by PRICE.TG_ID')


@dp.callback_query_handler(lambda c: c.data.startswith('winner'))
async def set_winner(call: types.CallbackQuery):
    v = call.data.split('_')
    tg_id = v[1]
    request_id = v[2]
    await send_message_to_contractor(message=call.message,
                                     from_user=call.from_user,
                                     request_id=request_id,
                                     tg_id=tg_id)
    await database.archive_request(request_id)
    await call.answer()


async def contractor_start(message: types.Message):
    user = await handlers.get_user_data(message.from_user.id)
    if user:
        if user.agent_type == 0:
            await admin_login(message)
            return
        await contractor_login(message)
        return
        # TODO: Сделать возможность перерегистрации
    await message.answer('Привет! Бот создан для проведения тендера компанией "ВсеИнструменты.ру"\n\n'
                         'Для связи заказчика с Вами, напишите ваш <b>телефон</b>:',
                         parse_mode=types.ParseMode.HTML)
    await ContractorState.wait_phone.set()


@dp.message_handler(state=ContractorState.wait_phone)
async def get_phone(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('Телефон должен содержать только числа. Введите заново:')
        return
    if len(message.text) != 11:
        await message.answer('Телефон должен состоять из 11 цифр. Введите заново:')
        return
    await state.update_data(phone=message.text)
    await message.answer('Название вашей организации:')
    await ContractorState.next()


@dp.message_handler(state=ContractorState.wait_fullname)
async def get_fullname(message: types.Message, state: FSMContext):
    if '"' in message.text:
        message.text = message.text.replace('"', "'")
    await state.update_data(org_name=message.text)
    rg = types.InlineKeyboardMarkup(row_width=4).add(
        *[types.InlineKeyboardButton(text=x, callback_data=f'chooseReg_contr_{x}') for x in region_names]
    )
    await message.answer("Выберите регион(ы): ", reply_markup=rg)
    await ContractorState.next()


async def get_contr_region(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    if 'chosen_regs' not in state_data:
        await call.message.answer('Не выбраны регионы')
        return
    await call.answer()
    agent_names = {
        "АХО": 1,
        "Реклама": 2,
    }
    button_type = types.InlineKeyboardMarkup(row_width=1).add(
        *[types.InlineKeyboardButton(text=x, callback_data=f'agent_{y}') for x, y in agent_names.items()]
    )
    await call.message.answer("Выберите тип предоставляемых услуг:", reply_markup=button_type)


@dp.callback_query_handler(lambda c: c.data.startswith('agent'), state='*')
async def get_agent_type(call: types.CallbackQuery, state: FSMContext):
    agent_type = call.data.split("_")[1]
    state_data = await state.get_data()
    await call.answer()
    phone = state_data.get("phone")
    org_name = state_data.get("org_name")
    chosen_regs = state_data.get("chosen_regs")
    await state.finish()
    await database.add_user(call.from_user.id, phone,
                            org_name, ', '.join(chosen_regs), agent_type)
    await contractor_login(call.message)


async def contractor_login(message: types.Message):
    contractor_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    contractor_menu.add(types.KeyboardButton('Обновить список заявок'))
    await message.answer(f'Вы успешно авторизованы',
                         reply_markup=contractor_menu)


@dp.message_handler(text="Создать заявку")
async def create_request(message: types.Message):
    admin_list = await handlers.get_admin_list()
    if not admin_list or message.from_user.id not in admin_list:
        return
    btn = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton(text='АХО', callback_data='req_create_aho'),
        types.InlineKeyboardButton(text='Реклама', callback_data='req_create_ad')
    )
    await message.answer('Выберите тип заявки', reply_markup=btn)
    await RequestState.wait_type.set()


@dp.callback_query_handler(lambda c: c.data.startswith('req_create'), state=RequestState.wait_type)
async def call_req_type_create(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    await state.update_data(req_type=1 if data[2] == 'aho' else 2)
    await call.message.answer('Введите название заявки:')
    await RequestState.wait_name.set()


@dp.message_handler(state=RequestState.wait_name)
async def get_name_request(message: types.Message, state: FSMContext):
    # TODO Сделать проверку на уникальные названия заявок
    await database.create_request(0, message.from_user.id, message.text, 0)
    request_id = await handlers.get_request_id(message.text, message.from_user.id)
    if not request_id:
        await error(message, [message.text, message.from_user.id])
        return
    await message.answer('Прикрепите фотографии объекта заявки:')
    await state.update_data(id_request=request_id)
    await RequestState.wait_image.set()


photo_delivered: Set[int] = set()


# todo: пофиксить прикрепление других картинок ТЗ из-за неправильного условия инкрементатора айди заявки

async def image_buffer(user: types.User):
    if user.id in photo_delivered:
        return
    photo_delivered.add(user.id)
    await bot.send_message(user.id, "Введите техническое задание:")
    await RequestState.wait_text.set()


@dp.message_handler(state=RequestState.wait_image, content_types='photo')
async def get_image(message: types.Message, state: FSMContext):
    data = await state.get_data()
    request_id = data.get('id_request')
    file_id = message.photo[-1].file_id
    await database.add_image(request_id, file_id)
    await image_buffer(message.from_user)


async def do_prices_btn():
    pass


@dp.message_handler(state=RequestState.wait_text)
async def get_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    id_request = data.get('id_request')
    req_type = data.get('req_type')
    await state.finish()
    await database.update_request_text(message.text, id_request)
    await database.update_request_type(req_type, id_request)
    photo_delivered.clear()
    save_request_menu = types.InlineKeyboardMarkup()
    save_request_menu.add(types.InlineKeyboardButton('Отправить заявку',
                                                     callback_data=f'send_request_{id_request}'))
    save_request_menu.add(types.InlineKeyboardButton('Отменить заявку',
                                                     callback_data=f'cancel_request_{id_request}'))
    await message.answer('Заявка успешно создана', reply_markup=save_request_menu)


# Обработка кнопки "Отправить заявку"
@dp.callback_query_handler(lambda c: c.data.startswith('send_'))
async def key_send_request(call: types.CallbackQuery):
    await send_message_to_contractor(message=call.message,
                                     from_user=call.from_user,
                                     request_id=call.data.split('_')[2])
    await call.answer()


# Обработка кнопки "Отменить заявку"
@dp.callback_query_handler(lambda c: c.data.startswith('cancel_'))
async def key_cancel_request(call: types.CallbackQuery):
    await database.delete_request(call.data.split('_')[2])
    await call.message.answer('Заявка успешно отменена')
    await call.answer()


# todo не выводится сообщение о пустых заказов у которых тип другой
# Обработка кнопки "Удалить заявку"
@dp.message_handler(text="Архивировать заявку")
async def remove_request(message: types.Message):
    admin_list = await handlers.get_admin_list()
    if not admin_list or message.from_user.id not in admin_list:
        return
    requests = await handlers.get_all_requests(tg_id=message.from_user.id, is_archived=0)
    if not requests:
        await message.answer('У вас нет заявок')
        return
    keys = types.InlineKeyboardMarkup()
    keys.add(*[types.InlineKeyboardButton(text=req.title, callback_data=f'req_{req.id}') for req in requests])
    await message.answer('Выберете заявку на архивирование:', reply_markup=keys)


# Функция удаление заявки
@dp.callback_query_handler(lambda c: c.data.startswith('req_'), state='*')
async def select_request(call: types.CallbackQuery):
    data = call.data.split('_')[1]
    await database.archive_request(data)
    await call.message.answer(f'Заявка была успешно архивирована!')


# Функция отправки сообщений исполнителям. Если есть tg_id, то отправляется одному пользователю
async def send_message_to_contractor(message: types.Message, from_user, request_id, tg_id=None):
    request_data = await handlers.get_request_data(request_id)
    if not request_data:
        await error(message, request_id)
        return
    if tg_id:
        await bot.send_message(tg_id,
                               f'Вы выиграли тендер по заявке <b>{request_data.title}</b> \n\n'
                               f'Скоро с вами свяжется менеджер для уточнения деталей',
                               parse_mode=types.ParseMode.HTML)
        await message.edit_text('Информация отправлена пользователю')
        return
    author_data = await handlers.get_user_data(from_user.id)
    if not author_data:
        await error(message, 'await handlers.get_user_data(message.from_user.id)')
        return
    tg_id_list = await handlers.get_users_tg(author_data.regions, request_data.type)
    if not tg_id_list:
        await message.answer('Некому отправлять')
        return
    for tg_id in tg_id_list:
        await req_send(tg_id, request_data)
    await message.answer('Заявка отправлена исполнителям')


async def req_send(tg_id, request_data):
    media = []
    image_list = await handlers.get_images(request_data.id)
    if image_list:
        for image_data in image_list:
            media.append(types.InputMediaPhoto(image_data.file_id))
    request_menu_contractor = req_menu(request_data.id)
    msg_to_send = await reload_request_description(tg_id, request_data)
    msg_media = await bot.send_media_group(tg_id, media)
    msg_text = await bot.send_message(tg_id, msg_to_send,
                                      parse_mode=types.ParseMode.HTML,
                                      reply_markup=request_menu_contractor)
    return msg_media, msg_text


# Кнопка "Предложить цену"
@dp.callback_query_handler(lambda c: c.data.startswith('set_price'))
async def call_set_price(call: types.CallbackQuery, state: FSMContext):
    request_id = call.data.split('_')[2]
    await call.answer()
    await call.message.answer('Введите стоимость:')
    await PriceState.wait_price.set()
    await state.update_data(request_id=request_id)


# Обработка кнопки "задать вопрос"
@dp.callback_query_handler(lambda c: c.data.startswith('getInfo'))
async def call_get_info(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    request_id = call.data.split('_')[1]
    await call.message.answer('Задайте вопрос:')
    await GetInfoState.wait_info.set()
    await state.update_data(get_info_req_id=request_id)


@dp.message_handler(state=GetInfoState.wait_info)
async def message_get_info(message: types.Message, state: FSMContext):
    request_id = (await state.get_data()).get('get_info_req_id')
    await state.finish()
    await database.add_msg(message.from_user.id, message.message_id)
    msg_ids = await handlers.get_msg_ids(message.from_user.id)
    if not msg_ids:
        return

    contractor_id = message.from_user.id
    request_data = await handlers.get_request_data(request_id)
    author_id = request_data.tg_id
    title = request_data.title
    await message.answer('Вопрос отправлен. Ожидайте ответа')
    btn = types.InlineKeyboardButton(text='Ответить', callback_data=f'answer_req_{contractor_id}_{msg_ids[-1]}')
    await bot.send_message(author_id,
                           text=f'Появился новый вопрос по заявке <b>"{title}"</b>:\n{message.text}',
                           parse_mode=types.ParseMode.HTML,
                           reply_markup=types.InlineKeyboardMarkup().add(btn))


@dp.callback_query_handler(lambda c: c.data.startswith('answer_req'))
async def call_answer_req(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    contractor_id = data[2]
    msg_id = data[3]
    # print(contractor_id, msg_id)
    await call.message.answer('Введите ответ:')
    await GetInfoState.wait_reply_info.set()
    await state.update_data(contractor_id=contractor_id, msg_id=msg_id)
    await call.answer()


@dp.message_handler(state=GetInfoState.wait_reply_info)
async def message_answer_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    contractor_id = data.get('contractor_id')
    msg_id = data.get('msg_id')
    await bot.send_message(contractor_id, message.text, reply_to_message_id=msg_id)
    await message.answer('Ответ отправлен')
    await database.delete_msg(msg_id)


# Механизм обновления заявок
@dp.callback_query_handler(lambda c: c.data.startswith('reload'))
async def call_set_price(call: types.CallbackQuery):
    await call.answer()
    request_id = call.data.split('_')[1]
    request_data = await handlers.get_request_data(request_id)
    msg_to_send = await reload_request_description(call.from_user.id, request_data)
    request_menu_contractor = req_menu(request_data.id)
    try:
        await call.message.edit_text(text=msg_to_send,
                                     parse_mode=types.ParseMode.HTML,
                                     reply_markup=request_menu_contractor)
    except MessageNotModified as e:
        cnt_logger.error(e)
    finally:
        await call.answer()


async def reload_request_description(user_id, request_data):
    min_price_data = await handlers.get_min_price(request_data.id)
    price_desc = ''
    price = "цена не установлена"

    if min_price_data:
        price = f"<code>{min_price_data.price}</code> ₽"
        if min_price_data.tg_id == user_id:
            price_desc = '\n<b>Ваша стоимость лидирует 🔥</b>'
        else:
            curr_price = await handlers.get_user_price_data(user_id)
            if curr_price and curr_price.request_id == request_data.id:
                price_desc = f'\n<b>Вы предложили:</b> <code>{curr_price.price}</code> ₽'
    msg_to_send = f'<b>{request_data.title}</b>\n\n' \
                  f'{request_data.description}\n\n' \
                  f'Предложенная стоимость: {price}' \
                  f'{price_desc}'

    return msg_to_send


# Установка цены на request
@dp.message_handler(state=PriceState.wait_price)
async def price_changer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    request_id = data.get('request_id')
    if not message.text.isdigit():
        await message.answer('Некорректный формат. Введите заново:')
        return
    await database.add_price(request_id, message.from_user.id, message.text)
    await message.answer('Цена отправлена')
    await state.finish()


REQ_TYPE = ['АХО', 'Реклама']


# Обработка кнопки "Список заказов"
@dp.message_handler(text='Обновить список заявок')
async def request_list_contractor(message: types.Message):
    request_list = await handlers.get_all_requests(is_archived=0)
    list_msg = await handlers.get_msg_ids(message.from_user.id)
    if list_msg:
        for msg in list_msg:
            try:
                await bot.delete_message(message.chat.id, msg)
                await database.delete_all_msg(message.from_user.id)
            except MessageToDeleteNotFound as e:
                cnt_logger.error(f"Error to delete message: {e}")
    if not request_list:
        await message.answer('Список заявок пуст')
        return
    user_data = await handlers.get_user_data(message.from_user.id)
    flag = False
    for req_data in request_list:
        author_data = await handlers.get_user_data(req_data.tg_id)
        if not any([r in user_data.regions.split(', ') for r in author_data.regions.split(', ')]) \
                or user_data.agent_type != req_data.type:
            flag |= False
            continue

        cnt_logger.debug(req_data)
        msg_media, msg_text = await req_send(message.from_user.id, req_data)
        for msg in msg_media:
            await database.add_msg(message.from_user.id, msg.message_id)
        await database.add_msg(message.from_user.id, msg_text.message_id)
        flag |= True
    if not flag:
        await message.answer('Нет активных заявок')


async def on_startup(dp: Dispatcher):
    cnt_logger.info('Bot has been started.')
    dp.middleware.setup(LoggingMiddleware())


async def on_shutdown(dp):
    cnt_logger.info('Bot has been stopped.')
    cnt_logging.archive_logs()


def req_menu(request_id):
    r = types.InlineKeyboardMarkup(row_width=1)
    r.add(
        types.InlineKeyboardButton('Предложить свою цену', callback_data=f'set_price_{request_id}'),
        types.InlineKeyboardButton('Обновить', callback_data=f'reload_{request_id}'),
        types.InlineKeyboardButton('Задать вопрос', callback_data=f'getInfo_{request_id}')
    )
    return r


async def error(message: types.Message, error_by):
    await message.answer('Непредвиденная ошибка. Напишите об это разработчикам.')
    cnt_logger.error(F'ОШИБКА ПОЛУЧЕНИЯ ДАННЫХ ПО ЗАПРОСУ "{error_by}"')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown, on_startup=on_startup, timeout=120)
