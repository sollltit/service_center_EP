import sqlite3
from datetime import datetime, date
from contextlib import contextmanager

# Регистрируем адаптеры для работы с датами
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_converter("DATE", lambda s: date.fromisoformat(s.decode()))

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect('service_center.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def create_request(request_data):
    """
    Создание новой заявки согласно п.2.1 ТЗ
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # генерация номера заявки: REQ-ГГГГ-ПППП
            year = datetime.now().year
            cursor.execute('SELECT COUNT(*) FROM requests WHERE strftime("%Y", created_at) = ?', (str(year),))
            count = cursor.fetchone()[0] + 1
            request_number = f'REQ-{year}-{count:04d}'
            
            cursor.execute('''
            INSERT INTO requests 
            (request_number, equipment_type, equipment_model, problem_description, 
             user_name, user_phone, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_number,
                request_data['equipment_type'],
                request_data['equipment_model'],
                request_data['problem_description'],
                request_data['user_name'],
                request_data['user_phone'],
                'Новая заявка'
            ))
            
            request_id = cursor.lastrowid
            conn.commit()
            return request_id
    except Exception as e:
        print(f"Ошибка при создании заявки: {e}")
        return None

def get_all_requests():
    """
    Получение всех заявок для отображения списка
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT r.*, u.full_name as assigned_name 
        FROM requests r
        LEFT JOIN users u ON r.assigned_to = u.id
        ORDER BY r.created_at DESC, r.id DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def update_request_status(request_id, new_status, user_id):
    """
    Обновление статуса заявки согласно п.2.2 ТЗ
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM requests WHERE id = ?', (request_id,))
            old_status = cursor.fetchone()[0]
            cursor.execute('''
            UPDATE requests 
            SET status = ?, 
                completed_at = CASE WHEN ? = 'completed' THEN date('now') ELSE completed_at END
            WHERE id = ?
            ''', (new_status, new_status, request_id))
            cursor.execute('''
            INSERT INTO status_history (request_id, old_status, new_status, changed_by)
            VALUES (?, ?, ?, ?)
            ''', (request_id, old_status, new_status, user_id))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при обновлении статуса: {e}")
        return False

def assign_technician(request_id, technician_id):
    """
    Назначение специалиста на заявку
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if technician_id: 
                cursor.execute('''
                UPDATE requests 
                SET assigned_to = ?, assigned_at = date('now')
                WHERE id = ?
                ''', (technician_id, request_id))
            else: 
                cursor.execute('''
                UPDATE requests 
                SET assigned_to = NULL, assigned_at = NULL
                WHERE id = ?
                ''', (request_id,))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при назначении специалиста: {e}")
        return False

def get_statistics():
    """
    Расчет статистики согласно п.2.5 ТЗ
    ТОЛЬКО ДАТА - расчет в днях
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM requests')
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        cursor.execute('''
        SELECT AVG(
            julianday(completed_at) - julianday(created_at)
        )
        FROM requests 
        WHERE status = 'completed' 
          AND completed_at IS NOT NULL 
          AND created_at IS NOT NULL
        ''')
        avg_days_result = cursor.fetchone()[0]
        avg_days = round(avg_days_result, 2) if avg_days_result else 0
        cursor.execute('''
        SELECT equipment_type, COUNT(*) as count
        FROM requests
        GROUP BY equipment_type
        ORDER BY count DESC
        ''')
        equipment_stats = [dict(row) for row in cursor.fetchall()]
        return {
            'total_requests': total,
            'completed_requests': completed,
            'avg_completion_days': avg_days,
            'equipment_stats': equipment_stats
        }


def get_technicians():
    """
    Получение списка всех специалистов
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, full_name, phone 
        FROM users 
        WHERE role = 'Специалист'  
        ORDER BY full_name
        ''')
        return [dict(row) for row in cursor.fetchall()]


def search_requests(search_term):
    """
    Поиск заявок по номеру или ФИО заказчика согласно п.2.3 ТЗ
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT r.*, u.full_name as assigned_name 
        FROM requests r
        LEFT JOIN users u ON r.assigned_to = u.id
        WHERE r.request_number LIKE ? OR r.user_name LIKE ?
        ORDER BY r.created_at DESC
        ''', (f'%{search_term}%', f'%{search_term}%'))
        return [dict(row) for row in cursor.fetchall()]


def add_comment(request_id, user_id, comment_text, is_technical=False, parts_ordered=None):
    """
    Добавление комментария к заявке согласно п.2.4 ТЗ
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO comments (request_id, user_id, comment_text, is_technical_note, parts_ordered)
            VALUES (?, ?, ?, ?, ?)
            ''', (request_id, user_id, comment_text, is_technical, parts_ordered))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при добавлении комментария: {e}")
        return False

def get_comments(request_id):
    """
    Получение всех комментариев к заявке
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT c.*, u.full_name, u.role
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.request_id = ?
        ORDER BY c.created_at ASC
        ''', (request_id,))
        return [dict(row) for row in cursor.fetchall()]
    

def create_user_db(user_data):
    """
    Создание нового пользователя в базе данных
    
    Args:
        user_data: dict с данными пользователя
        
    Returns:
        bool: True если пользователь создан, False при ошибке
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Хешируем пароль
            password_hash = hash_password(user_data['password'])
            
            cursor.execute('''
            INSERT INTO users (username, password_hash, role, full_name, phone)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                user_data['username'],
                password_hash,
                user_data['role'],
                user_data['full_name'],
                user_data.get('phone', '')
            ))
            
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        print(f"Пользователь с логином '{user_data['username']}' уже существует")
        return False
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        return False

def update_user_db(user_id, user_data):
    """
    Обновление данных пользователя
    
    Args:
        user_id: ID пользователя
        user_data: dict с обновленными данными
        
    Returns:
        bool: True если обновлено, False при ошибке
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if 'password' in user_data and user_data['password']:
                password_hash = hash_password(user_data['password'])
                cursor.execute('''
                UPDATE users 
                SET role = ?, full_name = ?, phone = ?, password_hash = ?
                WHERE id = ?
                ''', (
                    user_data['role'],
                    user_data['full_name'],
                    user_data.get('phone', ''),
                    password_hash,
                    user_id
                ))
            else:
                cursor.execute('''
                UPDATE users 
                SET role = ?, full_name = ?, phone = ?
                WHERE id = ?
                ''', (
                    user_data['role'],
                    user_data['full_name'],
                    user_data.get('phone', ''),
                    user_id
                ))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при обновлении пользователя: {e}")
        return False

def delete_user_db(user_id):
    """
    Удаление пользователя из базы данных
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если удалено, False при ошибке
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка при удалении пользователя: {e}")
        return False
    

def get_all_users():
    """
    Получение списка всех пользователей
    
    Returns:
        List of dicts: Список пользователей
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, username, role, full_name, phone, created_at 
        FROM users 
        ORDER BY 
            CASE role
                WHEN 'Администратор' THEN 1
                WHEN 'Менеджер' THEN 2
                WHEN 'Специалист' THEN 3
                WHEN 'Оператор' THEN 4
                WHEN 'Заказчик' THEN 5
                ELSE 6
            END,
            full_name
        ''')
        return [dict(row) for row in cursor.fetchall()]

def hash_password(password):
    """
    Хеширование пароля
    """
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def get_request_by_id(request_id):
    """
    Получение заявки по ID
    
    Args:
        request_id: ID заявки
        
    Returns:
        dict: Данные заявки или None если не найдена
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT r.*, u.full_name as assigned_name 
            FROM requests r
            LEFT JOIN users u ON r.assigned_to = u.id
            WHERE r.id = ?
            ''', (request_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except Exception as e:
        print(f"Ошибка при получении заявки по ID: {e}")
        return None
    

def get_status_history(request_id):
    """
    Получение истории изменения статусов заявки
    
    Args:
        request_id: ID заявки
        
    Returns:
        List of dicts: История изменений статусов
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT sh.*, u.full_name as changed_by_name
            FROM status_history sh
            LEFT JOIN users u ON sh.changed_by = u.id
            WHERE sh.request_id = ?
            ORDER BY sh.changed_at DESC
            ''', (request_id,))
            
            rows = cursor.fetchall()
            result = []
            for row in rows:
                if isinstance(row, sqlite3.Row):
                    result.append(dict(row))
                else:
                    result.append({
                        'id': row[0],
                        'request_id': row[1],
                        'old_status': row[2],
                        'new_status': row[3],
                        'changed_by': row[4],
                        'changed_at': row[5],
                        'changed_by_name': row[6] if len(row) > 6 else None
                    })
            return result
    except Exception as e:
        print(f"Ошибка при получении истории статусов: {e}")
        return []
    

def get_requests_by_customer(customer_name, customer_phone=None):
    """
    Получение заявок конкретного заказчика
    
    Args:
        customer_name: ФИО заказчика
        customer_phone: Телефон заказчика (опционально)
        
    Returns:
        List of dicts: Список заявок заказчика
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if customer_phone:
                cursor.execute('''
                SELECT r.*, u.full_name as assigned_name 
                FROM requests r
                LEFT JOIN users u ON r.assigned_to = u.id
                WHERE (r.user_name = ? AND r.user_phone = ?)
                   OR r.user_name = ?
                ORDER BY r.created_at DESC
                ''', (customer_name, customer_phone, customer_name))
            else:
                cursor.execute('''
                SELECT r.*, u.full_name as assigned_name 
                FROM requests r
                LEFT JOIN users u ON r.assigned_to = u.id
                WHERE r.user_name = ?
                ORDER BY r.created_at DESC
                ''', (customer_name,))
            
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            
            print(f"DEBUG DB: Поиск заявок для '{customer_name}' (тел: {customer_phone})")
            print(f"DEBUG DB: Найдено: {len(result)} заявок")
            if result:
                print(f"DEBUG DB: Пример: {result[0]['user_name']} - {result[0]['user_phone']}")
            
            return result
            
    except Exception as e:
        print(f"Ошибка при получении заявок заказчика: {e}")
        return []