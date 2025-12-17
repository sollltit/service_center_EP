import sqlite3
import hashlib
import streamlit as st

def hash_password(password):
    """
    Хеширование пароля для безопасного хранения
    
    Args:
        password: Пароль в чистом виде
        
    Returns:
        str: Хеш пароля SHA-256
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(username, password):
    """
    Проверка логина и пароля пользователя
    
    Args:
        username: Имя пользователя
        password: Пароль в чистом виде
        
    Returns:
        dict or None: Данные пользователя или None если неверные данные
    """
    try:
        conn = sqlite3.connect('service_center.db')
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user:
            password_hash = hash_password(password)
            if user['password_hash'] == password_hash:
                user_dict = dict(user)
                return user_dict
        
        return None
    except sqlite3.Error as e:
        print(f"Ошибка базы данных при проверке логина: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка при проверке логина: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def init_session_state():
    """
    Инициализация состояния сессии Streamlit.
    Вызывается в начале main.py перед любыми операциями.
    """
    if 'user' not in st.session_state:
        st.session_state.user = None          
        st.session_state.role = None          
        st.session_state.full_name = None     
        st.session_state.user_id = None       
    
    # Параметры навигации и состояния
    if 'page' not in st.session_state:
        st.session_state.page = "requests"  
    if 'selected_request' not in st.session_state:
        st.session_state.selected_request = None  
    if 'editing_request' not in st.session_state:
        st.session_state.editing_request = None 
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False 
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""  
def login_user(user_data):
    """
    Сохранение данных пользователя в сессии после успешной авторизации.
    
    Args:
        user_data: dict с данными пользователя из БД
                   Должен содержать: id, username, role, full_name
    """
    st.session_state.user = user_data['username']
    st.session_state.role = user_data['role']
    st.session_state.full_name = user_data['full_name']
    st.session_state.user_id = user_data['id']

def logout_user():
    """
    Выход пользователя из системы.
    Очищает все данные сессии связанные с пользователем.
    """
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.full_name = None
    st.session_state.user_id = None
    st.session_state.page = "requests" 

def check_auth():
    """
    Проверка авторизации пользователя.
    
    Returns:
        bool: True если пользователь авторизован, иначе False
    """
    return st.session_state.user is not None

def get_current_user():
    """
    Получение данных текущего пользователя из сессии.
    
    Returns:
        dict: Словарь с данными пользователя или None если не авторизован
    """
    if check_auth():
        return {
            'username': st.session_state.user,
            'role': st.session_state.role,
            'full_name': st.session_state.full_name,
            'id': st.session_state.user_id
        }
    return None

def require_auth():
    """
    Декоратор для защиты страниц, требующих авторизации.
    Если пользователь не авторизован, показывает форму входа.
    
    Note: В текущей реализации Streamlit используется другой подход,
    но функция оставлена для совместимости и возможного расширения.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_auth():
                show_login_form()
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

def show_login_form():
    """
    Показывает форму входа в систему.
    Используется когда пользователь не авторизован.
    """
    st.title("🔐 Вход в систему")
    st.write("Для работы с системой учета заявок необходимо авторизоваться")
    
    # Создаем форму входа
    with st.form("login_form", clear_on_submit=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("### Данные для входа")
        
        with col2:
            username = st.text_input(
                "Логин",
                placeholder="Введите ваш логин",
                help="Введите имя пользователя, выданное администратором"
            )
            
            password = st.text_input(
                "Пароль",
                type="password",
                placeholder="Введите ваш пароль",
                help="Введите пароль, выданный администратором"
            )

        submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
        with submit_col2:
            submit = st.form_submit_button(
                "🚪 Войти в систему",
                type="primary",
                use_container_width=True
            )
    
    if submit:
        if not username or not password:
            st.error("⚠️ Пожалуйста, заполните все поля")
            return
        
        # Проверка учетных данных
        with st.spinner("Проверка учетных данных..."):
            user_data = verify_login(username, password)
        
        if user_data:
            login_user(user_data)
            st.success(f"✅ Добро пожаловать, {user_data['full_name']}!")
            import time
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Неверный логин или пароль")
            with st.expander("Тестовые данные (для демонстрации)"):
                st.info("""
                **Для тестирования используйте:**
                
                1. **Администратор:** admin / admin123
                2. **Менеджер:** manager / manager123  
                3. **Специалист:** tech / tech123
                4. **Оператор:** operator / operator123
                5. **Заказчик:** customer / customer123
                """)

def get_role_display_name(role_code):
    """
    Получение отображаемого имени роли.
    
    Args:
        role_code: Код роли из БД
        
    Returns:
        str: Человеко-читаемое название роли
    """
    return role_code

def create_user(username, password, role, full_name, phone=None):
    """
    Создание нового пользователя (для администраторов).
    
    Args:
        username: Логин пользователя
        password: Пароль в чистом виде
        role: Роль пользователя
        full_name: Полное имя пользователя
        phone: Телефон (опционально)
        
    Returns:
        bool: True если пользователь создан, False при ошибке
    """
    try:
        conn = sqlite3.connect('service_center.db')
        cursor = conn.cursor()
        
        # Хешируем пароль
        password_hash = hash_password(password)
        
        # Проверяем, что роль допустима
        allowed_roles = ['Администратор', 'Менеджер', 'Специалист', 'Оператор', 'Заказчик']
        if role not in allowed_roles:
            raise ValueError(f"Недопустимая роль. Допустимые роли: {', '.join(allowed_roles)}")
        cursor.execute('''
        INSERT INTO users (username, password_hash, role, full_name, phone)
        VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, role, full_name, phone))
        
        conn.commit()
        return True
        
    except sqlite3.IntegrityError:
        print(f"Пользователь с логином '{username}' уже существует")
        return False
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    """
    Тестирование модуля авторизации.
    Запустите этот файл отдельно для проверки функций.
    """
    import sys
    
    print("=" * 50)
    print("Тестирование модуля авторизации")
    print("=" * 50)
    

    test_password = "test123"
    hashed = hash_password(test_password)
    print(f"Пароль: '{test_password}'")
    print(f"Хеш: {hashed}")

    print("\n" + "=" * 50)
    print("Проверка создания пользователя...")

    success = create_user("test_user", "test123", "Оператор", "Тестовый Пользователь", "+79990000000")
    if success:
        print("✅ Тестовый пользователь создан успешно")
        
        print("\nПроверка авторизации...")
        user_data = verify_login("test_user", "test123")
        if user_data:
            print(f"✅ Авторизация успешна")
            print(f"   Имя: {user_data['full_name']}")
            print(f"   Роль: {user_data['role']}")
        else:
            print("❌ Авторизация не удалась")
    else:
        print("❌ Не удалось создать тестового пользователя")
        print("   (возможно, пользователь уже существует)")
    
    print("\n" + "=" * 50)
    print("Тестирование завершено")