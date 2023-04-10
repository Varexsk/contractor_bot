from typing import NamedTuple

from db import database


class ActiveMessage(NamedTuple):
    id: int
    tg_id: int
    msg_id: int


class Users(NamedTuple):
    id: int
    tg_id: int
    phone: str
    fullname: str
    regions: str
    agent_type: int


class Images(NamedTuple):
    id: int
    request_id: int
    file_id: str


class Prices(NamedTuple):
    id: int
    request_id: int
    tg_id: int
    price: int


class Requests(NamedTuple):
    id: int
    title: str
    tg_id: str
    description: str
    isArchived: bool
    type: int


async def get_msg_ids(tg_id):
    data = await database.get_id_msg_by_tg_id(tg_id)
    if not data:
        return []
    return [d[0] for d in data]


async def get_admin_list():
    data = await database.get_admin_list()
    if not data:
        return []
    return [d[0] for d in data]


async def get_contractors_tg(region):
    data = await database.get_all_tg_id_contractor(region)
    if not data:
        return []
    return [d[0] for d in data]


async def get_user_data(tg_id):
    data = await database.get_user_by_tg_id(tg_id)
    if not data:
        return None
    return Users(*data)


async def get_request_id(title, tg_id):
    data = await database.get_id_request(title, tg_id)
    if not data:
        return None
    return data[0]


async def get_all_requests(is_archived, tg_id=None):
    if tg_id:
        data = await database.get_all_request_by_tg_id(tg_id, is_archived)
    else:
        data = await database.get_all_request(is_archived)
    if not data:
        return []
    return [Requests(*d) for d in data]


async def get_request_data(req_id):
    data = await database.get_request_by_id(req_id)
    if not data:
        return None
    return Requests(*data)


async def get_request_by_type(req_type):
    data = await database.get_request_by_type(req_type)
    if not data:
        return []
    return [Requests(*d) for d in data]


async def get_images(req_id):
    data = await database.get_image(req_id)
    if not data:
        return []
    return [Images(*d) for d in data]


async def get_price(req_id):
    data = await database.get_price(req_id)
    if not data:
        return []
    return [Prices(*d) for d in data]


async def get_price_data(req_id):
    data = await database.get_all_from_price_by_request(req_id)
    if not data:
        return []
    return [Prices(*d) for d in data]


async def get_user_price_data(tg_id):
    data = await database.get_user_price_data(tg_id)
    if not data:
        return None
    return Prices(*data)


async def get_min_price(req_id):
    data = await database.get_min_price_data(req_id)
    if not data or None in data:
        return None
    return Prices(*data)


async def get_min_price_data_list(req_id):
    data = await database.get_min_price_data_list(req_id)
    if not data or None in data:
        return []
    return [Prices(*d) for d in data]