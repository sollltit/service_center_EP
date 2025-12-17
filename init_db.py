import sqlite3
import hashlib
from datetime import datetime, date

def init_database():
    """Создает базу данных и таблицы если они не существуют"""

    conn = sqlite3.connect('service_center.db')
    cursor = conn.cursor()
    sqlite3.register_adapter(date, lambda d: d.isoformat())
    sqlite3.register_converter("DATE", lambda s: date.fromisoformat(s.decode()))
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,т
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN (
            'Администратор',     
            'Менеджер',          
            'Менеджер по качеству',          
            'Специалист',        
            'Оператор',          
            'Заказчик'           
        )),
        full_name TEXT NOT NULL,
        phone TEXT,
        created_at DATE DEFAULT (date('now'))
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_number TEXT UNIQUE NOT NULL,
        created_at DATE DEFAULT (date('now')),
        equipment_type TEXT NOT NULL,
        equipment_model TEXT NOT NULL,
        problem_description TEXT NOT NULL,
        user_name TEXT NOT NULL,
        user_phone TEXT NOT NULL,
        status TEXT DEFAULT 'Новая заявка' CHECK(status IN ('Новая заявка', 'В процессе ремонта', 'Готово к выдаче', 'Выполнено')),
        assigned_to INTEGER,
        assigned_at DATE,
        completed_at DATE,
        FOREIGN KEY (assigned_to) REFERENCES users(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        comment_text TEXT NOT NULL,
        is_technical_note BOOLEAN DEFAULT 0,
        parts_ordered TEXT,
        created_at DATE DEFAULT (date('now')),
        FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        changed_by INTEGER NOT NULL,
        changed_at DATE DEFAULT (date('now')),
        FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by) REFERENCES users(id)
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_requests_assigned ON requests(assigned_to)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_requests_number ON requests(request_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_request ON comments(request_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_requests_date ON requests(created_at)')
    admin_password = hash_password('admin123')
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, role, full_name, phone)
    VALUES (?, ?, ?, ?, ?)
    ''', ('admin', admin_password, 'Администратор', 'Главный Администратор', '+79990000000'))
    
    manager_password = hash_password('manager123')
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, role, full_name, phone)
    VALUES (?, ?, ?, ?, ?)
    ''', ('manager', manager_password, 'Менеджер', 'Менеджер Отдела', '+79991111111'))
    tech_password = hash_password('tech123')
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, role, full_name, phone)
    VALUES (?, ?, ?, ?, ?)
    ''', ('tech', tech_password, 'Специалист', 'Инженер Петров', '+79992222222'))
    operator_password = hash_password('operator123')
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, role, full_name, phone)
    VALUES (?, ?, ?, ?, ?)
    ''', ('operator', operator_password, 'Оператор', 'Оператор Call-центра', '+79993333333'))
    
    customer_password = hash_password('customer123')
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, role, full_name, phone)
    VALUES (?, ?, ?, ?, ?)
    ''', ('customer', customer_password, 'Заказчик', 'Иванов Иван', '+79994444444'))
    
    conn.commit()
    conn.close()
    print("База данных успешно инициализирована!")
    print("Данные для входа:")
    print("1. Администратор: admin / admin123")
    print("2. Менеджер: manager / manager123")
    print("3. Специалист: tech / tech123")
    print("4. Оператор: operator / operator123")
    print("5. Заказчик: customer / customer123")

def hash_password(password):
    """Хеширование пароля для безопасного хранения"""
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == '__main__':
    init_database()