import psycopg2
import Dict_uploader
from Cards_logger import cards_logger


def create_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chats(
        id SERIAL PRIMARY KEY,
        chat_tg_id BIGINT,
        first_name VARCHAR(40),
        words_num INT,
        correct_attempts_num INT
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS words(
        id SERIAL PRIMARY KEY,
        russian_word VARCHAR(40),
        english_word VARCHAR(40),
        english_usage VARCHAR(200)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS chats_words(
        id SERIAL PRIMARY KEY,
        chat_id INTEGER NOT NULL REFERENCES chats(id),
        word_id INTEGER NOT NULL REFERENCES words(id)
        );
        """)
    cards_logger.info('Созданы таблицы базы данных')
    conn.commit()


def delete_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""DROP TABLE chats_words""")
        cur.execute("""DROP TABLE chats""")
        cur.execute("""DROP TABLE words""")
    cards_logger.info('Таблицы удалены')
    conn.commit()


def clean_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""DELETE FROM chats_words""")
        cur.execute("""DELETE FROM chats""")
        cur.execute("""DELETE FROM words""")
        cur.execute("""ALTER SEQUENCE words_id_seq RESTART WITH 1;""")
        cur.execute("""ALTER SEQUENCE chats_words_id_seq RESTART WITH 1;""")
        cur.execute("""ALTER SEQUENCE chats_id_seq RESTART WITH 1;""")
    cards_logger.info('Таблицы очищены')
    conn.commit()


def update_correct_attempts_db(conn, chat_tg_id):
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE chats SET correct_attempts_num = correct_attempts_num + 1 WHERE chat_tg_id = %s""", (chat_tg_id, )
        )
        cur.execute(
            """SELECT correct_attempts_num FROM chats WHERE chat_tg_id = %s""", (chat_tg_id, )
        )
        cards_logger.info(f'id{chat_tg_id}: на 1 увеличено количество верно угаданных слов.')
        return cur.fetchone()[0]


def words_num_db(conn, chat_tg_id):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT words_num FROM chats WHERE chat_tg_id = %s""", (chat_tg_id, )
        )
        cards_logger.info(f'id{chat_tg_id}: определено количество слов в списке.')
        return cur.fetchone()[0]


def select_rand_word_db(conn, chat_tg_id):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT russian_word, english_word, english_usage reu FROM words w
            LEFT JOIN chats_words cw ON w.id = cw.word_id
            LEFT JOIN chats c ON c.id = cw.chat_id
            WHERE c.chat_tg_id = %s
            ORDER BY random() 
            LIMIT 1""", (chat_tg_id, )
        )
        _values = cur.fetchall()
        rus_word = _values[0][0]
        eng_word = _values[0][1]
        usage = _values[0][2]
        cur.execute(
            """SELECT english_word FROM words w  
            LEFT JOIN chats_words cw ON w.id = cw.word_id
            LEFT JOIN chats c ON c.id = cw.chat_id
            WHERE russian_word <> %s AND c.chat_tg_id = %s
            ORDER BY random() LIMIT 3""", (rus_word, chat_tg_id)
        )
        _values = cur.fetchall()
        wrong_words = [_values[0][0], _values[1][0], _values[2][0]]
        cards_logger.info(f'id{chat_tg_id}: выбрано слово для перевода "{rus_word}",'
                          f'перевод {eng_word} и 3 неправильных варианта {wrong_words}.')
        return rus_word, eng_word, wrong_words, usage


def add_word_db(conn, rus_word, chat_tg_id, first_name, eng_word=None, usage=None):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT * FROM words w  
            LEFT JOIN chats_words cw ON w.id = cw.word_id
            LEFT JOIN chats c ON c.id = cw.chat_id
            WHERE russian_word = %s AND c.chat_tg_id = %s""", (rus_word, chat_tg_id)
        )
        if cur.fetchone() is not None:
            cards_logger.info(f'id{chat_tg_id}: пытался добавить существующее слово.')
            return
        if eng_word is None:
            eng_word, usage = Dict_uploader.get_translate_and_example(rus_word)
        cur.execute(
            """SELECT id from words WHERE russian_word = %s AND english_word = %s 
            AND english_usage = %s""", (rus_word, eng_word, usage)
        )
        exist_word = cur.fetchone()
        if exist_word is None:
            cur.execute(
                """INSERT INTO words(russian_word, english_word, english_usage) VALUES(%s, %s, %s);""",
                (rus_word, eng_word, usage)
            )
            cards_logger.info(f'Новое слово "{rus_word} - {eng_word} - {usage}" добавлено в таблицу "words"')
            cur.execute(
                """SELECT id from words WHERE russian_word = %s""", (rus_word, )
            )
            word_id = cur.fetchone()[0]
        else:
            word_id = exist_word[0]
        cur.execute(
            """SELECT id from chats WHERE chat_tg_id = %s""", (chat_tg_id, )
        )
        exist_chat = cur.fetchone()
        if exist_chat is None:
            cur.execute(
                """INSERT INTO chats(chat_tg_id, first_name, words_num, correct_attempts_num) 
                VALUES(%s, %s, %s, %s);""",
                (chat_tg_id, first_name, 1, 0)
            )
            cards_logger.info(f'id{chat_tg_id}: добавлен новый чат в таблицу "chats"')
            cur.execute(
                """SELECT id from chats WHERE chat_tg_id = %s""", (chat_tg_id,)
            )
            chat_id = cur.fetchone()[0]
        else:
            chat_id = exist_chat[0]
        cur.execute(
            """SELECT id from chats_words WHERE chat_id = %s AND word_id = %s""", (chat_id, word_id)
        )
        exist_pair = cur.fetchone()
        if exist_pair is None:
            cur.execute(
                """INSERT INTO chats_words(chat_id, word_id) VALUES(%s, %s);""",
                (chat_id, word_id)
            )
            cards_logger.info(f'Новая связь слово-чат {chat_id} - {word_id} добавлена в таблицу "chats-words"')
            cur.execute(
                """SELECT COUNT(*) from chats_words WHERE chat_id = %s""", (chat_id,)
            )
            words_num = cur.fetchone()[0]
            cur.execute(
                    """UPDATE chats SET words_num = %s WHERE id = %s""", (words_num, chat_id)
            )
    conn.commit()


def list_db(conn, chat_tg_id):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT russian_word rw, english_word ew FROM words w
            LEFT JOIN chats_words cw ON w.id = cw.word_id
            LEFT JOIN chats c ON c.id = cw.chat_id
            WHERE c.chat_tg_id = %s
            ORDER BY rw""", (chat_tg_id, )
        )
        return cur.fetchall()


def delete_word_db(conn, chat_tg_id, rus_word):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT w.id FROM words w
            LEFT JOIN chats_words cw ON w.id = cw.word_id
            LEFT JOIN chats c ON c.id = cw.chat_id
            WHERE russian_word = %s AND c.chat_tg_id = %s""", (rus_word, chat_tg_id)
        )
        word_id = cur.fetchone()[0]
        cur.execute(
            """SELECT id FROM chats
            WHERE chat_tg_id = %s""", (chat_tg_id, )
        )
        chat_id = cur.fetchone()[0]
        cur.execute(
            """SELECT COUNT(*) FROM chats_words
            WHERE word_id = %s""", (word_id, )
        )
        pair_num = cur.fetchone()[0]
        cur.execute(
            """DELETE FROM chats_words WHERE chat_id = %s AND word_id = %s""", (chat_id, word_id)
        )
        cards_logger.info(f'Связь слово-чат {chat_id} - {word_id} удалена из таблицы "chats-words"')
        if pair_num == 1:
            cur.execute(
                """DELETE FROM words WHERE id = %s""", (word_id, )
            )
            cards_logger.info(f'Слово "{rus_word}" удалено из таблицы "words"')
        cur.execute(
            """SELECT COUNT(*) from chats_words WHERE chat_id = %s""", (chat_id,)
        )
        words_num = cur.fetchone()[0]
        cur.execute(
            """UPDATE chats SET words_num = %s WHERE id = %s""", (words_num, chat_id)
        )
    conn.commit()


class DBCards:

    def __init__(self, database, user, password, chat_tg_id):
        self.database = database
        self.user = user
        self.password = password
        self.chat_tg_id = chat_tg_id

    def initial_data(self, first_name):
        with psycopg2.connect(database=self.database, user=self.user, password=self.password) as conn:
            base_words = ['отец', 'сын', 'мыло', 'коллектив', 'красивый', 'здоровый', 'высокий', 'грустно', 'больно',
                          'она', 'оно', 'они']
            for word in base_words:
                add_word_db(conn, word, self.chat_tg_id, first_name)

    def add_word(self, rus_word, translate, usage, first_name):
        with psycopg2.connect(database=self.database, user=self.user, password=self.password) as conn:
            add_word_db(conn, rus_word, self.chat_tg_id, first_name, translate, usage)

    def update_correct_attempts_num(self):
        with psycopg2.connect(database=self.database, user=self.user, password=self.password) as conn:
            return update_correct_attempts_db(conn, self.chat_tg_id)

    def words_num(self):
        with psycopg2.connect(database=self.database, user=self.user, password=self.password) as conn:
            return words_num_db(conn, self.chat_tg_id)

    def select_rand_word(self):
        with psycopg2.connect(database=self.database, user=self.user, password=self.password) as conn:
            return select_rand_word_db(conn, self.chat_tg_id)

    def list_words(self):
        with psycopg2.connect(database=self.database, user=self.user, password=self.password) as conn:
            list_words = []
            i = 1
            for word in list_db(conn, self.chat_tg_id):
                list_words.append([i, word[0], word[1]])
                i += 1
            return list_words

    def delete_word(self, rus_word):
        with psycopg2.connect(database=self.database, user=self.user, password=self.password) as conn:
            delete_word_db(conn, self.chat_tg_id, rus_word)
