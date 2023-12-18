import telebot
import os
import io
import sqlite3
import shutil
import subprocess

from PIL import Image
from sqlite3 import Error

TOKEN = '#PREENCHER COM TOKEN DO TELEGRAM'

SAVE_DIR = 'dataset/'

def create_connection(db_file):
    """ Cria uma conexão com o banco de dados SQLite """
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        return conn
    except Error as e:
        print(e)
        return conn
    
def get_all_users():
    """ Obtém uma lista de todos os usuários cadastrados """
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users")
    users = cur.fetchall()
    return users

def show_user_list_for_deletion(message, users):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    for user_id, user_name in users:
        markup.add(telebot.types.KeyboardButton(f'{user_name} - {user_id}'))

    markup.add(telebot.types.KeyboardButton('Cancelar'))

    bot.reply_to(message, 'Selecione um usuário para excluir:', reply_markup=markup)
    
def process_user_deletion(message):
    user_input = message.text.strip()

    if user_input.lower() == 'cancelar':
        bot.reply_to(message, 'Operação cancelada.')
    else:
        selected_user = user_input.split(' - ')

        if len(selected_user) == 2 and selected_user[1].isdigit():
            user_id = int(selected_user[1])
            try:
                print("Deleting User ID:", user_id)
                delete_user_directory(user_id)
                delete_user(conn, user_id)
                bot.reply_to(message, f'O usuário {selected_user[1]} foi excluído com sucesso.')
                script_path = "./train.py"
                subprocess.run(["python3", script_path])
            except Exception as e:
                bot.reply_to(message, f'Erro ao excluir usuário: {e}')
        else:
            bot.reply_to(message, 'Seleção inválida. Por favor, use os botões fornecidos.')

    
def create_table(conn):
    """ Cria a tabela de usuários se ela não existir """
    sql_create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            passwrd TEXT DEFAULT 'admin123',
            first_access BOOLEAN DEFAULT 1,
            photo_count INTEGER DEFAULT 0
        );
    """
    try:
        c = conn.cursor()
        c.execute(sql_create_users_table)
    except Error as e:
        print(e)
        
def create_user_directory(user_id):
    user_directory = os.path.join(SAVE_DIR, str(user_id))
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    return user_directory

def delete_user_directory(user_id):
    user_directory = os.path.join(SAVE_DIR, str(user_id))
    if os.path.exists(user_directory):
        shutil.rmtree(user_directory)

def process_promote_admin(message):
    chat_id = message.chat.id
    user_id_to_promote = message.text.strip()

    if user_id_to_promote.lower() == 'cancelar':
        bot.reply_to(message, 'Operação cancelada.')
    elif user_id_to_promote.isdigit():
        user_id_to_promote = int(user_id_to_promote)
        if is_user_registered(conn, user_id_to_promote):
            users = get_all_users_with_ids(conn)
            user_names = [f'{user_name} - {user_id}' for user_id, user_name in users]

            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

            for user_option in user_names:
                markup.add(telebot.types.KeyboardButton(user_option))

            markup.add(telebot.types.KeyboardButton('Cancelar'))

            bot.reply_to(message, 'Selecione um usuário para tornar administrador:', reply_markup=markup)
            bot.register_next_step_handler(message, process_selected_user_to_promote_admin, user_id_to_promote)
        else:
            bot.reply_to(message, 'ID de usuário inválido. Usuário não registrado.')
    else:
        bot.reply_to(message, 'ID de usuário inválido. Por favor, insira um número válido.')

def process_selected_user_to_promote_admin(message, user_id_to_promote):
    selected_user = message.text.strip().split(' - ')

    if selected_user[1].isdigit():
        selected_user_id = int(selected_user[1])
        try:
            print("Selected User ID (numeric):", selected_user_id)
            print("Selected User ID (full):", selected_user) 
            update_admin_status(conn, selected_user_id, 1)

            user_name_to_promote = get_user_by_id(conn, selected_user_id)
            bot.reply_to(message, f'O usuário {user_name_to_promote} foi promovido a administrador com sucesso.')
        except Exception as e:
            bot.reply_to(message, f'Erro ao promover usuário a administrador: {e}')
    elif selected_user[0].lower() == 'cancelar':
        bot.reply_to(message, 'Operação cancelada.')
    else:
        bot.reply_to(message, 'Seleção inválida. Por favor, use os botões fornecidos.')

def get_all_users_with_ids(conn):
    """ Obtém uma lista de todos os usuários cadastrados com seus IDs """
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users")
    users = cur.fetchall()
    return users

def is_admin(conn, chat_id):
    """ Verifica se o usuário é um administrador """
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id=?", (chat_id,))
    result = cur.fetchone()
    if result:
        return result[0] == 1
    return False
def is_user_registered(conn, chat_id):
    """ Verifica se o usuário já está registrado no banco de dados """
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (chat_id,))
    return cur.fetchone() is not None

def register_user(conn, chat_id, name, is_admin=0):
    """ Registra um novo usuário no banco de dados """
    cur = conn.cursor()
    cur.execute("INSERT INTO users (id, name, is_admin) VALUES (?, ?, ?)", (chat_id, name, is_admin))
    conn.commit()

def get_user_name(conn, chat_id):
    """ Obtém o nome do usuário do banco de dados """
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE id=?", (chat_id,))
    return cur.fetchone()[0]

def delete_user(conn, chat_id):
    """ Remove um usuário do banco de dados """
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (chat_id,))
    conn.commit()
    
def show_user_options_after_first_access(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Excluir meu registro'))

    bot.reply_to(message, 'Opções disponíveis para usuários:', reply_markup=markup)

def show_admin_options_after_first_access(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Excluir registros'), telebot.types.KeyboardButton('Excluir meu registro'), telebot.types.KeyboardButton('Tornar alguém administrador'))

    bot.reply_to(message, 'Opções disponíveis para administradores:', reply_markup=markup)

def get_first_access_status(conn, chat_id):
    """ Obtém o status do primeiro acesso do usuário do banco de dados """
    cur = conn.cursor()
    cur.execute("SELECT first_access FROM users WHERE id=?", (chat_id,))
    result = cur.fetchone()
    if result:
        return result[0]
    return None

def update_first_access_status(conn, chat_id, status):
    """ Atualiza o status do primeiro acesso do usuário no banco de dados """
    cur = conn.cursor()
    cur.execute("UPDATE users SET first_access=? WHERE id=?", (status, chat_id))
    conn.commit()
    
def update_admin_status(conn, user_id, admin_status):
    """ Atualiza o status de administrador do usuário no banco de dados """
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_admin=? WHERE id=?", (admin_status, user_id))
    conn.commit()

    
bot = telebot.TeleBot(TOKEN)
conn = create_connection("user_data.db")
create_table(conn)

def show_registration_options(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('/start'))

    bot.reply_to(message, 'Olá, vamos começar! Escolha a opção disponivel:', reply_markup=markup)

def show_admin_options(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Excluir registros'), telebot.types.KeyboardButton('Excluir meu registro'), telebot.types.KeyboardButton('Tornar alguém administrador') )

    bot.reply_to(message, 'Olá, vamos começar! Essas são as opções disponíveis para administradores: ', reply_markup=markup)

def show_user_options(message):
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Excluir meu registro'))

    bot.reply_to(message, 'Olá, vamos começar! Essas são as opções disponíveis para usuários: ', reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.lower()

    if is_user_registered(conn, chat_id):
        registered_name = get_user_name(conn, chat_id)
        
        if get_first_access_status(conn, chat_id):
            update_first_access_status(conn, chat_id, 0)

            if is_admin(conn, chat_id):
                show_admin_options_after_first_access(message)
                bot.reply_to(message, f'Você está registrado como administrador, {registered_name}.')
            else:
                show_user_options_after_first_access(message)
                bot.reply_to(message, f'Você está registrado como usuário, {registered_name}.')
        else:
            if text == '/delete':
                try:
                    delete_user_directory(chat_id)
                    delete_user(conn, chat_id)
                    bot.reply_to(message, 'Seu registro foi excluído com sucesso.')
                    script_path = "./train.py"
                    subprocess.run(["python3", script_path])
                except Exception as e:
                    bot.reply_to(message, f'Erro ao excluir usuário: {e}')
            else:
                if is_admin(conn, chat_id):
                    if text == 'excluir registros':
                        users = get_all_users()
                        show_user_list_for_deletion(message, users)
                        bot.register_next_step_handler(message, process_user_deletion)
                        pass
                    elif text == 'excluir meu registro':
                        try:
                            delete_user_directory(chat_id)
                            delete_user(conn, chat_id)
                            bot.reply_to(message, 'Seu registro foi excluído com sucesso.')
                            script_path = "./train.py"
                            subprocess.run(["python3", script_path])
                        except Exception as e:
                            bot.reply_to(message, f'Erro ao excluir usuário: {e}')
                    elif text == 'tornar alguém administrador':
                            users = get_all_users_with_ids(conn)
                            user_names = [f'{user_name} - {user_id}' for user_id, user_name in users]

                            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

                            for user_option in user_names:
                                markup.add(telebot.types.KeyboardButton(user_option))

                            markup.add(telebot.types.KeyboardButton('Cancelar'))

                            bot.reply_to(message, 'Selecione um usuário para tornar administrador:', reply_markup=markup)
                            bot.register_next_step_handler(message, process_promote_admin)
                    
                    else:
                        show_admin_options(message)
                else:
                    if text == 'excluir meu registro':
                        try:
                            delete_user_directory(chat_id)
                            delete_user(conn, chat_id)
                            bot.reply_to(message, 'Seu registro foi excluído com sucesso.')
                            script_path = "./train.py"
                            subprocess.run(["python3", script_path])
                        except Exception as e:
                            bot.reply_to(message, f'Erro ao excluir usuário: {e}')
                    else:
                        show_user_options(message)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton('Usuário'), telebot.types.KeyboardButton('Administrador'))

        msg = bot.reply_to(message, 'Você deseja se cadastrar como usuário ou administrador?', reply_markup=markup)
        bot.register_next_step_handler(msg, process_role_choice)

def process_role_choice(message):
    chat_id = message.chat.id
    user_role = message.text.lower()
    
    if user_role == 'usuário' or user_role == 'administrador':
        markup = telebot.types.ForceReply(selective=False)
        msg = bot.reply_to(message, 'Por favor, digite seu nome:')
        bot.register_next_step_handler(msg, process_user_name, user_role)
    else:
        bot.reply_to(message, 'Escolha inválida. Por favor, use os botões fornecidos.')

def process_user_name(message, user_role):
    chat_id = message.chat.id
    user_name = message.text.strip()

    if user_role == 'usuário':
        register_user(conn, chat_id, user_name)
        create_user_directory(chat_id)
        bot.reply_to(message, f'Olá {user_name}, você foi registrado como usuário. Agora você pode me enviar suas fotos.')
    elif user_role == 'administrador':
        markup = telebot.types.ForceReply(selective=False)
        msg = bot.reply_to(message, 'Digite a senha de administrador:')
        bot.register_next_step_handler(msg, lambda m: process_admin_password(m, user_name))

def process_admin_password(message, admin_name):
    chat_id = message.chat.id
    admin_password = message.text.strip()

    if admin_password == 'adm123':
        register_user(conn, chat_id, admin_name, is_admin=1)
        create_user_directory(chat_id)
        bot.reply_to(message, f'Olá {admin_name}, Você foi registrado como Administrador. Agora você pode me enviar suas fotos.')
    else:
        bot.reply_to(message, 'Senha de administrador incorreta. Registro cancelado.')

@bot.message_handler(content_types=['photo'])
def save_photo(message):
    chat_id = message.chat.id
    user_name = get_user_name(conn, chat_id)
    user_directory = create_user_directory(chat_id)
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    
    cur = conn.cursor()
    cur.execute("SELECT photo_count FROM users WHERE id=?", (chat_id,))
    current_count = cur.fetchone()[0]

    if current_count < 5:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        compressed_file_path = os.path.join(user_directory, f"{file_info.file_id}_compressed_bw.jpg")

        with Image.open(io.BytesIO(downloaded_file)) as img:
            img = img.convert('L')

            img.save(compressed_file_path, quality=15)

        current_count += 1
        cur.execute("UPDATE users SET photo_count=? WHERE id=?", (current_count, chat_id))
        conn.commit()

        if current_count == 5:
            bot.reply_to(message, f"Você enviou com sucesso as 5 imagens, iremos cadastrar você!")
            script_path = "./train.py"
            subprocess.run(["python3", script_path, user_directory])
        else:
            remaining_count = 5 - current_count
            bot.reply_to(message, f"Imagem recebida. Você ainda precisa enviar mais {remaining_count} imagens.")
    else:
        bot.reply_to(message, f"Você já enviou o número máximo de imagens.")

bot.polling()
