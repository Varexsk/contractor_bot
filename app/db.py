#
# Код для работы с БД
#
import os
import sqlite3
from pathlib import Path


class Database:
    """ Класс работы с базой данных """

    def __init__(self, name):
        self.name = name
        self._conn = self.connection()

    @staticmethod
    def create_db(path):
        connection = sqlite3.connect(path)
        cursor = connection.cursor()

        cursor.execute("""CREATE TABLE users
                       (id INTEGER PRIMARY KEY,
                       tg_id INTEGER NOT NULL,
                       phone VARCHAR NOT NULL,
                       fullname VARCHAR NOT NULL,
                       region VARCHAR NOT NULL,
                       agent_type INTEGER NOT NULL)
                       """)

        cursor.execute("""CREATE TABLE requests
                       (id INTEGER PRIMARY KEY,
                       title_name VARCHAR NOT NULL,
                       tg_id INTEGER NOT NULL,
                       text_request TEXT,
                       archive INTEGER,
                       type INTEGER NOT NULL)
                       """)

        cursor.execute("""CREATE TABLE images
                       (id INTEGER PRIMARY KEY,
                       request_id INTEGER NOT NULL,
                       file_id VARCHAR NOT NULL)
                       """)

        cursor.execute("""CREATE TABLE prices
                       (id INTEGER PRIMARY KEY,
                       request_id INTEGER NOT NULL,
                       tg_id INTEGER NOT NULL,
                       price INTEGER NOT NULL)
                       """)

        cursor.execute("""CREATE TABLE active_message
                       (id INTEGER PRIMARY KEY,
                       tg_id INTEGER NOT NULL,
                       msg_id INTEGER NOT NULL)
                       """)

        connection.commit()
        cursor.close()

    def connection(self):
        db_path = f'{get_bot_root_path()}/{self.name}.db'
        if not os.path.exists(db_path):
            self.create_db(db_path)
        return sqlite3.connect(db_path)

    def _execute_query(self, query, select=False, fetch_all=False):
        cursor = self._conn.cursor()
        cursor.execute(query)
        if select:
            records = cursor.fetchall() if fetch_all else cursor.fetchone()
            cursor.close()
            return records
        else:
            self._conn.commit()

    async def add_msg(self, tg_id, msg_id):
        insert_query = f"""
                INSERT INTO active_message (tg_id, msg_id)
                VALUES ({tg_id}, {msg_id})
                """
        self._execute_query(insert_query)

    async def delete_all_msg(self, tg_id):
        delete_query = f"""
        DELETE FROM active_message WHERE tg_id = {tg_id} 
        """
        self._execute_query(delete_query)

    async def delete_msg(self, msg_id):
        delete_query = f"""
                DELETE FROM active_message WHERE msg_id = {msg_id} 
                """
        self._execute_query(delete_query)

    # to handler
    async def get_id_msg_by_tg_id(self, tg_id):
        select_query = f"""
                    SELECT msg_id FROM active_message WHERE tg_id = {tg_id}
                    """
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record

    async def add_user(self, tg_id, phone, fullname, region, agent_type):
        insert_query = f"""
        INSERT INTO users (tg_id, phone, fullname, region, agent_type)
        VALUES ({tg_id}, "{phone}", "{fullname}", "{region}", {agent_type})
        """
        self._execute_query(insert_query)

    # to handler
    async def get_admin_list(self):
        select_query = """
                    SELECT tg_id FROM users WHERE agent_type = 0
                    """
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record

    async def delete_users(self, tg_id):
        delete_query = f"""
        DELETE FROM users WHERE tg_id = {tg_id} 
        """
        self._execute_query(delete_query)

    # to handler
    async def get_all_tg_id_contractor(self, regions):
        select_query = f"SELECT tg_id FROM users WHERE agent_type <> 0 AND ("
        for reg in regions.split(', '):
            select_query += f'region LIKE("%{reg}%") or '
        select_query = select_query[:-4] + ')'
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record

    # to handler
    async def get_user_by_tg_id(self, tg_id):
        select_query = f"""
                        SELECT * FROM users WHERE tg_id = {tg_id}
                        """
        record = self._execute_query(select_query, select=True)
        return record

    async def create_request(self, req_rype, tg_id, title_name, archive):
        insert_query = f"""
        INSERT INTO requests (type, tg_id, title_name, archive)
        VALUES ({req_rype} , {tg_id}, "{title_name}", {archive})
        """
        self._execute_query(insert_query)

    async def archive_request(self, request_id):
        update_query = f"""UPDATE requests SET archive = 1 
                WHERE id = {request_id}"""
        self._execute_query(update_query)

    async def update_request_text(self, text_request, id_request):
        update_query = f"""UPDATE requests SET text_request = "{text_request}" 
        WHERE id = {id_request}"""
        self._execute_query(update_query)

    async def update_request_type(self, req_type, id_request):
        update_query = f"""UPDATE requests SET type = "{req_type}" 
                WHERE id = {id_request}"""
        self._execute_query(update_query)

    async def delete_request(self, id_request):
        delete_query = f"""
                DELETE FROM requests WHERE id = {id_request} 
                """
        self._execute_query(delete_query)

    # to handler
    async def get_id_request(self, title_name, tg_id):
        select_query = f"""
        SELECT id FROM requests WHERE title_name = "{title_name}" and tg_id = {tg_id}
        """
        record = self._execute_query(select_query, select=True)
        return record

    # to handler
    async def get_all_request_by_tg_id(self, tg_id, archive):
        select_query = f"""
                        SELECT * FROM requests WHERE tg_id = {tg_id} and archive = {archive}
                        """
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record

    # to handler
    async def get_all_request(self, archive):
        select_query = f"""
                        SELECT * FROM requests WHERE archive = {archive}
                        """
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record

    async def get_request_by_type(self, req_type):
        querry = f"SELECT * FROM requests WHERE type = {req_type}"
        record = self._execute_query(querry, select=True, fetch_all=True)
        return record

    # to handler
    async def get_request_by_id(self, request_id):
        select_query = f"""
                        SELECT * FROM requests WHERE id = {request_id}
                        """
        record = self._execute_query(select_query, select=True)
        return record

    async def add_image(self, request_id, file_id):
        insert_query = f"""
                        INSERT INTO images (request_id, file_id)
                        VALUES ({request_id}, "{file_id}")
                        """
        self._execute_query(insert_query)

    # to handler
    async def get_image(self, request_id):
        select_query = f"""
                        SELECT * FROM images WHERE request_id = {request_id}
                        """
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record

    async def add_price(self, request_id, tg_id, price):
        insert_query = f"""
                        INSERT INTO prices (request_id, tg_id, price)
                        VALUES ({request_id}, {tg_id}, {price})
                        """
        self._execute_query(insert_query)

    # to handler
    async def get_price(self, request_id):
        select_query = f"""
                        SELECT price FROM prices WHERE request_id = {request_id}
                        """
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record

    # to handler
    async def get_all_from_price_by_request(self, request_id):
        select_query = f"""
                                SELECT * FROM prices WHERE request_id = {request_id}
                                """
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record

    # to handler
    async def get_user_price_data(self, tg_id):
        query = f"""
                SELECT * FROM prices WHERE tg_id = {tg_id}
                """
        record = self._execute_query(query, select=True, fetch_all=False)
        return record

    # to handler
    async def get_min_price_data(self, request_id):
        query = f"""
                SELECT id, request_id, tg_id, min(price) FROM prices WHERE request_id = {request_id}
                """
        record = self._execute_query(query, select=True, fetch_all=False)
        return record

    async def get_min_price_data_list(self, request_id):
        query = f"""SELECT id, request_id, tg_id, min(price) FROM prices WHERE request_id = {request_id}
                    GROUP BY tg_id
                    """
        return self._execute_query(query, select=True, fetch_all=True)

    async def get_user_tg(self, regions, req_type):
        select_query = f"SELECT tg_id FROM users WHERE agent_type == {req_type} AND ("
        for reg in regions.split(', '):
            select_query += f'region LIKE("%{reg}%") or '
        select_query = select_query[:-4] + ')'
        record = self._execute_query(select_query, select=True, fetch_all=True)
        return record


def get_bot_root_path():
    path_list = [str(path.as_posix()) for path in Path(__file__).parents]
    for path in path_list:
        if 'app' in path.split('/')[-1]:
            return path


database = Database('contractor_db')
