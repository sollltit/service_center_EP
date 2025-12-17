import streamlit as st
import auth
import database
from datetime import datetime
import time
auth.init_session_state()


def show_add_comment_modal(request_id, current_user):
    with st.expander("💬 Добавить комментарий", expanded=True):
        comment = st.text_area("Текст комментария*", placeholder="Введите ваш комментарий...")
        parts_ordered = st.text_input("Заказанные комплектующие (если есть)", 
                                     placeholder="Например: Компрессор ABC-123, 2 шт.")
        is_technical = st.checkbox("Это техническая заметка")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Сохранить комментарий", use_container_width=True, type="primary"):
                if comment.strip():
                    if database.add_comment(request_id, current_user['id'], 
                                          comment.strip(), is_technical, 
                                          parts_ordered if parts_ordered.strip() else None):
                        st.success("✅ Комментарий успешно добавлен")
                        st.rerun()
                else:
                    st.error("❌ Введите текст комментария")
        with col2:
            if st.button("❌ Отмена", use_container_width=True):
                st.rerun()

def show_create_request_form(current_user):
    st.title("➕ Создание новой заявки")
    
    with st.form("create_request_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            equipment_type = st.text_input(
                "Тип оборудования *",
                placeholder="Например: Сплит-система, Кондиционер..."
            )
            

            if current_user['role'] == 'Заказчик':
                user_name = st.text_input(
                    "ФИО заказчика *",
                    value=current_user['full_name'],
                    disabled=True  # Нельзя изменить
                )
                st.caption("📝 Ваше ФИО заполнено автоматически")
            else:
                user_name = st.text_input("ФИО заказчика *")
        
        with col2:
            equipment_model = st.text_input("Модель устройства *")

            if current_user['role'] == 'Заказчик' and current_user.get('phone'):
                user_phone = st.text_input(
                    "Номер телефона *",
                    value=current_user.get('phone', ''),
                    disabled=True  
                )
                st.caption("📞 Ваш телефон заполнен автоматически")
            else:
                user_phone = st.text_input("Номер телефона *")
        
        problem_description = st.text_area(
            "Описание проблемы *",
            height=120
        )
        
        if current_user['role'] != 'Заказчик':
            st.divider()
            st.write("**Дополнительные настройки (опционально):**")
            
            col3, col4 = st.columns(2)
            with col3:
                if current_user['role'] in ['Администратор', 'Менеджер']:
                    initial_status = st.selectbox(
                        "Начальный статус",
                        ['Новая заявка', 'В процессе ремонта'],
                        help="Выберите начальный статус заявки"
                    )
                else:
                    initial_status = 'Новая заявка'
            
            with col4:
                # Назначение специалиста сразу
                if current_user['role'] in ['Администратор', 'Менеджер']:
                    technicians = database.get_technicians()
                    if technicians:
                        tech_options = ["❌ Не назначать сразу"] + [t['full_name'] for t in technicians]
                        initial_tech = st.selectbox(
                            "Назначить специалиста",
                            tech_options,
                            help="Можно назначить специалиста сразу при создании"
                        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("✅ Создать заявку", type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Отмена")
        
        if cancel:
            st.session_state.show_create_form = False
            st.rerun()
        
        if submit:
            # Проверка обязательных полей
            if not all([equipment_type, equipment_model, problem_description, user_name, user_phone]):
                st.error("❌ Заполните все обязательные поля (помечены *)")
                return
            
            # Подготовка данных
            request_data = {
                'equipment_type': equipment_type,
                'equipment_model': equipment_model,
                'problem_description': problem_description,
                'user_name': user_name,
                'user_phone': user_phone,
                'status': 'Новая заявка'
            }
            
            # Для не-заказчиков может быть другой начальный статус
            if current_user['role'] != 'Заказчик' and 'initial_status' in locals():
                request_data['status'] = initial_status
            
            # Создаем заявку
            request_id = database.create_request(request_data)
            
            if request_id:
                # Если нужно сразу назначить специалиста
                if current_user['role'] in ['Администратор', 'Менеджер'] and 'initial_tech' in locals():
                    if initial_tech != "❌ Не назначать сразу":
                        # Находим ID специалиста
                        for tech in technicians:
                            if tech['full_name'] == initial_tech:
                                database.assign_technician(request_id, tech['id'])
                                break
                
                st.success("✅ Заявка успешно создана!")
                
                # Особое сообщение для заказчиков
                if current_user['role'] == 'Заказчик':
                    st.info("📋 Вы можете отслеживать статус заявки на этой странице. С вами свяжется специалист.")
                
                st.session_state.show_create_form = False
                
                # Ждем и обновляем
                import time
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("❌ Ошибка при создании заявки")

def show_request_detail_page(request_id, current_user):
    """
    Страница детального просмотра заявки
    """
    # Получаем данные заявки
    request = database.get_request_by_id(request_id)
    if not request:
        st.error("Заявка не найдена")
        if st.button("← Назад к списку"):
            st.session_state.page = "requests"
            st.session_state.selected_request = None
            st.rerun()
        return
    
    st.title(f"📋 Заявка #{request['request_number']}")
    
    # Кнопка возврата
    if st.button("← Назад к списку"):
        st.session_state.page = "requests"
        st.session_state.selected_request = None
        st.rerun()
    
    # Основная информация о заявке
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Информация о заявке")
        st.write(f"**Номер:** {request['request_number']}")
        st.write(f"**Дата создания:** {request['created_at']}")
        st.write(f"**Статус:** {get_status_name(request['status'])}")
        st.write(f"**Тип оборудования:** {request['equipment_type']}")
        st.write(f"**Модель:** {request['equipment_model']}")
        
        # Кнопка изменения статуса для авторизованных пользователей
        if current_user['role'] in ['Администратор', 'Менеджер', 'Специалист']:
            st.divider()
            new_status = st.selectbox(
                "Изменить статус",
                ["Новая заявка", "В процессе ремонта", "Готово к выдаче", "Выполнено"],
                index=list(["Новая заявка", "В процессе ремонта", "Готово к выдаче", "Выполнено"]).index(request['status']),
                format_func=get_status_name,
                key=f"status_select_{request_id}"
            )
            
            if new_status != request['status']:
                if st.button("🔄 Обновить статус", type="secondary"):
                    if database.update_request_status(request_id, new_status, current_user['id']):
                        st.success("✅ Статус обновлен")
                        st.rerun()
    
    with col2:
        st.subheader("Информация о заказчике")
        st.write(f"**ФИО:** {request['user_name']}")
        st.write(f"**Телефон:** {request['user_phone']}")
        
        if request['assigned_name']:
            st.write(f"**Ответственный:** {request['assigned_name']}")
        
        if request['assigned_at']:
            st.write(f"**Назначена:** {request['assigned_at']}")
        
        if request['completed_at']:
            st.write(f"**Завершена:** {request['completed_at']}")
    
    # Описание проблемы
    st.divider()
    st.subheader("📝 Описание проблемы")
    st.write(request['problem_description'])
    
    # Комментарии
    st.divider()
    st.subheader("💬 Комментарии")
    
    # Показать существующие комментарии
    comments = database.get_comments(request_id)
    if comments:
        for comment in comments:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{comment['full_name']}** ({comment['role']})")
                    st.write(f"*{comment['created_at']}*")
                    
                    if comment['is_technical_note']:
                        st.info("🔧 **Техническая заметка**")
                    
                    if comment['parts_ordered']:
                        st.warning(f"🛠️ **Заказанные комплектующие:** {comment['parts_ordered']}")
                    
                    st.write(comment['comment_text'])
                st.divider()
    else:
        st.info("Пока нет комментариев")
    
    # Форма добавления нового комментария
    if current_user['role'] in ['Администратор', 'Менеджер', 'Специалист']:
        st.subheader("Добавить комментарий")
        show_add_comment_modal(request_id, current_user)

def show_requests_page(current_user):
    """
    Страница управления заявками
    Разные возможности для разных ролей
    """
    st.title("📋 Управление заявками")

    create_allowed_roles = ['Заказчик', 'Оператор', 'Менеджер', 'Администратор']
    
    if current_user['role'] in create_allowed_roles:
        if st.button("➕ Создать новую заявку", type="primary", key="create_request_btn"):
            st.session_state.show_create_form = True
    if st.session_state.get('show_create_form', False):
        show_create_request_form(current_user)
        return
    
    requests = []
    
    if current_user['role'] == 'Заказчик':
        requests = database.get_requests_by_customer(
            current_user['full_name'], 
            current_user.get('phone', '') 
        )

        if not requests and current_user.get('phone'):
            all_requests = database.get_all_requests()
            requests = [r for r in all_requests if r['user_name'] == current_user['full_name']]
    
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Фильтр по статусу",
                ["Все", "Новая заявка", "В процессе ремонта", "Готово к выдаче", "Выполнено"],
                key="status_filter_all"
            )
        with col2:
            search_term = st.text_input("Поиск по номеру или ФИО", key="search_all")
        with col3:
            if st.button("🔍 Поиск", use_container_width=True, key="search_btn_all"):
                st.session_state.search_term = search_term
            if st.button("🔄 Сбросить", use_container_width=True, key="reset_btn_all"):
                st.session_state.search_term = ""
        
        # Получаем заявки
        if st.session_state.get('search_term'):
            requests = database.search_requests(st.session_state.search_term)
        else:
            requests = database.get_all_requests()
        
        # Применяем фильтр по статусу
        if status_filter != "Все":
            requests = [r for r in requests if r['status'] == status_filter]

    if current_user['role'] == 'Заказчик':
        if not requests:
            st.info("📭 У вас еще нет заявок. Создайте первую!")
        else:
            st.success(f"✅ Найдено ваших заявок: {len(requests)}")
    else:
        # Для остальных ролей
        if not requests:
            st.info("📭 Заявок не найдено")
        else:
            st.write(f"**Найдено заявок:** {len(requests)}")
    
    # Отображаем таблицу заявок с разными правами
    display_requests_table_by_role(requests, current_user)


def display_requests_table_by_role(requests, current_user):
    """
    Отображение таблицы с заявками с учетом роли пользователя
    """
    if not requests:
        return
    
    for req in requests:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                status_icons = {
                    'Новая заявка': '🔴',
                    'В процессе ремонта': '🟡',
                    'Готово к выдаче': '🟠',
                    'Выполнено': '🟢'
                }
                icon = status_icons.get(req['status'], '⚪')
                
                st.write(f"**{req['request_number']}** {icon}")
                st.write(f"📱 {req['user_name']} | {req['user_phone']}")
                st.write(f"🔧 {req['equipment_type']} {req['equipment_model']}")
            
            with col2:
                st.write(f"**Статус:** {req['status']}")
                if req['assigned_name']:
                    st.write(f"👨‍🔧 {req['assigned_name']}")
                if req['created_at']:
                    st.write(f"📅 {req['created_at']}")

            with col3:
                # Кнопка "Подробнее" - для всех ролей
                if st.button("👁️ Подробнее", key=f"view_{req['id']}", use_container_width=True):
                    st.session_state.selected_request = req['id']
                    st.rerun()
                
                # Кнопка "Редактировать" - для менеджеров, админов и менеджеров по качеству
                if current_user['role'] != 'Заказчик':  
                    edit_roles = ['Администратор', 'Менеджер', 'Менеджер по качеству', 'Специалист', 'Оператор']
                    if current_user['role'] in edit_roles:
                        if st.button("✏️ Редактировать", key=f"edit_{req['id']}", use_container_width=True):
                            st.session_state.editing_request = req['id']
                            st.rerun()
            
            st.divider()


def display_requests_table(requests, current_user):
    """
    Отображение таблицы с заявками
    """
    if not requests:
        st.info("📭 Заявок не найдено")
        return
    
    for req in requests:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                status_icons = {
                    'Новая заявка': '🔴',
                    'В процессе ремонта': '🟡',
                    'Готово к выдаче': '🟠',
                    'Выполнено': '🟢'
                }
                icon = status_icons.get(req['status'], '⚪')
                
                st.write(f"**{req['request_number']}** {icon}")
                st.write(f"📱 {req['user_name']} | {req['user_phone']}")
                st.write(f"🔧 {req['equipment_type']} {req['equipment_model']}")
            
            with col2:
                st.write(f"**Статус:** {req['status']}")
                if req['assigned_name']:
                    st.write(f"👨‍🔧 {req['assigned_name']}")
                if req['created_at']:
                    st.write(f"📅 {req['created_at']}")
            
            with col3:
                # Кнопка "Подробнее"
                if st.button("👁️ Подробнее", key=f"view_{req['id']}", use_container_width=True):
                    st.session_state.selected_request = req['id']
                    st.rerun()
                
                # Кнопка "Редактировать" (открывает новую страницу)
                edit_roles = ['Администратор', 'Менеджер', 'Специалист']
                if current_user['role'] in edit_roles:
                    if st.button("✏️ Редактировать", key=f"edit_{req['id']}", use_container_width=True):
                        st.session_state.editing_request = req['id']
                        st.rerun()
            
            st.divider()

def show_edit_request_modal(request, current_user):
    """
    Безопасный вариант редактирования заявки
    """
    with st.expander(f"✏️ Редактирование заявки {request['request_number']}", expanded=True):
        # 1. Статус заявки (простой вариант)
        status_options = ['Новая заявка', 'В процессе ремонта', 'Готово к выдаче', 'Выполнено']
        
        # Определяем текущий индекс
        try:
            current_index = status_options.index(request['status'])
        except ValueError:
            current_index = 0  # По умолчанию
        
        # Selectbox для статуса
        new_status = st.selectbox(
            "Статус заявки",
            status_options,
            index=current_index,
            key=f"status_simple_{request['id']}"
        )
        
        # 2. Назначение специалиста
        selected_tech_id = None
        
        if current_user['role'] in ['Администратор', 'Менеджер']:
            # Получаем специалистов
            technicians_raw = database.get_technicians()
            
            # Преобразуем в правильный формат если нужно
            technicians = []
            if technicians_raw:
                for tech in technicians_raw:
                    if isinstance(tech, dict):
                        technicians.append(tech)
                    else:
                        # Если пришел не словарь, создаем его
                        technicians.append({
                            'id': tech[0] if hasattr(tech, '__getitem__') and len(tech) > 0 else None,
                            'full_name': tech[1] if hasattr(tech, '__getitem__') and len(tech) > 1 else '',
                            'phone': tech[2] if hasattr(tech, '__getitem__') and len(tech) > 2 else ''
                        })
            
            if technicians:
                # Создаем список для selectbox
                tech_options = ["❌ Не назначен"]
                tech_ids = [None]  # Соответствующие ID
                
                for tech in technicians:
                    if 'full_name' in tech:
                        tech_options.append(tech['full_name'])
                        tech_ids.append(tech.get('id'))
                
                # Текущий выбор
                current_tech_id = request.get('assigned_to')
                current_index = 0  # "Не назначен" по умолчанию
                
                # Ищем текущего специалиста в списке
                if current_tech_id and tech_ids:
                    for i, tech_id in enumerate(tech_ids):
                        if tech_id == current_tech_id:
                            current_index = i
                            break
                
                # Selectbox
                selected_tech_name = st.selectbox(
                    "Ответственный специалист",
                    tech_options,
                    index=current_index,
                    key=f"tech_simple_{request['id']}"
                )
                
                # Находим ID выбранного специалиста
                selected_index = tech_options.index(selected_tech_name)
                selected_tech_id = tech_ids[selected_index] if selected_index < len(tech_ids) else None
            else:
                st.info("📭 Нет доступных специалистов")
                selected_tech_id = request.get('assigned_to')  # Оставляем текущего
        
        # 3. Кнопки
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Сохранить", type="primary", key=f"save_simple_{request['id']}"):
                # Сохраняем статус
                if new_status != request['status']:
                    database.update_request_status(request['id'], new_status, current_user['id'])
                    st.success(f"✅ Статус: {new_status}")
                
                # Сохраняем специалиста
                if current_user['role'] in ['Администратор', 'Менеджер']:
                    current_tech_id = request.get('assigned_to')
                    
                    if selected_tech_id != current_tech_id:
                        database.assign_technician(request['id'], selected_tech_id)
                        
                        if selected_tech_id:
                            # Находим имя
                            tech_name = "специалист"
                            for tech in technicians:
                                if tech.get('id') == selected_tech_id:
                                    tech_name = tech.get('full_name', 'специалист')
                                    break
                            st.success(f"✅ Назначен: {tech_name}")
                        else:
                            st.success("✅ Специалист снят")
                
                # Ждем и обновляем
                import time
                time.sleep(1.5)
                st.session_state.editing_request = None
                st.rerun()
        
        with col2:
            if st.button("❌ Отмена", key=f"cancel_simple_{request['id']}"):
                st.session_state.editing_request = None
                st.rerun()


def show_edit_request_page(request_id, current_user):
    """
    Отдельная страница для редактирования заявки
    """
    # Получаем данные заявки
    request = database.get_request_by_id(request_id)
    
    if not request:
        st.error("❌ Заявка не найдена")
        if st.button("← Назад к списку"):
            del st.session_state.editing_request
            st.rerun()
        return
    
    st.title(f"✏️ Редактирование заявки #{request['request_number']}")
    
    # Кнопка возврата
    if st.button("← Назад к списку заявок"):
        del st.session_state.editing_request
        st.rerun()
    
    # Основная информация о заявке (только для просмотра)
    st.subheader("📄 Информация о заявке")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Номер заявки:** {request['request_number']}")
        st.write(f"**Дата создания:** {request['created_at']}")
        st.write(f"**Тип оборудования:** {request['equipment_type']}")
        st.write(f"**Модель:** {request['equipment_model']}")
    
    with col2:
        st.write(f"**ФИО заказчика:** {request['user_name']}")
        st.write(f"**Телефон:** {request['user_phone']}")
        st.write(f"**Описание проблемы:**")
        st.info(request['problem_description'])
    
    st.divider()
    
    # ФОРМА РЕДАКТИРОВАНИЯ
    st.subheader("⚙️ Изменение параметров заявки")
    
    with st.form(key=f"edit_request_form_{request_id}", clear_on_submit=False):
        # 1. Статус заявки
        st.write("**Статус заявки:**")
        status_options = ['Новая заявка', 'В процессе ремонта', 'Готово к выдаче', 'Выполнено']
        
        # Текущий статус
        current_status = request['status']
        current_index = status_options.index(current_status) if current_status in status_options else 0
        
        new_status = st.selectbox(
            "Выберите новый статус",
            status_options,
            index=current_index,
            key=f"status_{request_id}"
        )
        
        # 2. Назначение специалиста (только для админов и менеджеров)
        new_assigned_to = None
        
        if current_user['role'] in ['Администратор', 'Менеджер']:
            st.write("**Назначение специалиста:**")
            
            technicians = database.get_technicians()
            
            if technicians:
                # Создаем список опций
                tech_options = ["❌ Не назначен"]
                tech_ids = [None]
                
                for tech in technicians:
                    if isinstance(tech, dict):
                        name = tech.get('full_name', 'Неизвестно')
                        tech_id = tech.get('id')
                    else:
                        # Если кортеж
                        name = str(tech[1]) if len(tech) > 1 else 'Неизвестно'
                        tech_id = tech[0] if len(tech) > 0 else None
                    
                    tech_options.append(name)
                    tech_ids.append(tech_id)
                
                # Текущий назначенный специалист
                current_assigned_id = request.get('assigned_to')
                current_index = 0  # "Не назначен" по умолчанию
                
                # Ищем текущего в списке
                if current_assigned_id is not None:
                    for i, tech_id in enumerate(tech_ids):
                        if tech_id == current_assigned_id:
                            current_index = i
                            break
                
                # Selectbox для выбора специалиста
                selected_tech_name = st.selectbox(
                    "Выберите ответственного специалиста",
                    tech_options,
                    index=current_index,
                    key=f"tech_{request_id}"
                )
                
                # Находим ID выбранного специалиста
                selected_index = tech_options.index(selected_tech_name)
                new_assigned_to = tech_ids[selected_index] if selected_index < len(tech_ids) else None
            else:
                st.info("📭 Нет доступных специалистов")
                new_assigned_to = request.get('assigned_to')
        else:
            # Для не-админов/менеджеров оставляем текущего
            new_assigned_to = request.get('assigned_to')
        
        # 3. Кнопки формы
        col1, col2, col3 = st.columns(3)
        
        with col1:
            save_button = st.form_submit_button(
                "💾 Сохранить изменения", 
                type="primary",
                use_container_width=True
            )
        
        with col2:
            reset_button = st.form_submit_button(
                "🔄 Сбросить к исходным",
                use_container_width=True
            )
        
        with col3:
            cancel_button = st.form_submit_button(
                "❌ Отмена",
                use_container_width=True
            )
        
        # 4. Обработка действий формы
        if save_button:
            # Проверяем изменения
            changes_made = False
            messages = []
            
            # Статус
            if new_status != request['status']:
                if database.update_request_status(request_id, new_status, current_user['id']):
                    changes_made = True
                    messages.append(f"✅ Статус изменен на: **{new_status}**")
            
            # Специалист (только для админов/менеджеров)
            if current_user['role'] in ['Администратор', 'Менеджер']:
                current_tech_id = request.get('assigned_to')
                
                if new_assigned_to != current_tech_id:
                    if database.assign_technician(request_id, new_assigned_to):
                        changes_made = True
                        if new_assigned_to:
                            # Находим имя специалиста
                            tech_name = "специалист"
                            for tech in technicians:
                                tech_id = tech.get('id') if isinstance(tech, dict) else (tech[0] if len(tech) > 0 else None)
                                if tech_id == new_assigned_to:
                                    tech_name = tech.get('full_name', 'специалист') if isinstance(tech, dict) else (tech[1] if len(tech) > 1 else 'специалист')
                                    break
                            messages.append(f"✅ Назначен специалист: **{tech_name}**")
                        else:
                            messages.append("✅ **Специалист снят с заявки**")
            
            # Показываем результат
            if messages:
                for msg in messages:
                    st.success(msg)
                
                # Обновляем данные заявки
                request = database.get_request_by_id(request_id)
                time.sleep(1)
                st.rerun()
            else:
                st.info("ℹ️ Изменений не внесено")
        
        if reset_button:
            st.rerun()
        
        if cancel_button:
            del st.session_state.editing_request
            st.rerun()
    

    st.divider()
    st.subheader("📊 Текущее состояние заявки")
    
    col1, col2 = st.columns(2)
    
    with col1:
        status_icons = {
            'Новая заявка': '🔴',
            'В процессе ремонта': '🟡',
            'Готово к выдаче': '🟠',
            'Выполнено': '🟢'
        }
        icon = status_icons.get(request['status'], '⚪')
        st.write(f"**Текущий статус:** {icon} {request['status']}")
    
    with col2:

        if request.get('assigned_name'):
            st.write(f"**Ответственный:** 👨‍🔧 {request['assigned_name']}")
        else:
            st.write("**Ответственный:** ❌ Не назначен")
        
        if request.get('assigned_at'):
            st.write(f"**Назначена:** {request['assigned_at']}")
        
        if request.get('completed_at'):
            st.write(f"**Завершена:** {request['completed_at']}")

    st.divider()
    st.subheader("📋 История изменений статуса")

    try:
        history = get_status_history(request_id)
        if history:
            for record in history:
                st.write(f"**{record['changed_at']}** - {record['old_status']} → {record['new_status']}")
        else:
            st.info("История изменений отсутствует")
    except:
        st.info("История изменений отсутствует")


def show_my_tasks_page(current_user):
    """
    Страница для специалистов с их заявками согласно п.2.4 ТЗ
    """
    st.title("👨‍🔧 Мои задачи")
    
    if current_user['role'] != 'Специалист':
        st.warning("Эта страница доступна только специалистам")
        return
    
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT r.* FROM requests r
        WHERE r.assigned_to = ? AND r.status != 'Выполнено'
        ORDER BY 
            CASE r.status 
                WHEN 'В процессе ремонта' THEN 1
                WHEN 'Готово к выдаче' THEN 2
                WHEN 'Новая заявка' THEN 3
                ELSE 4
            END,
            r.created_at DESC
        ''', (current_user['id'],))
        my_requests = [dict(row) for row in cursor.fetchall()]
    
    if not my_requests:
        st.info("У вас нет активных заявок")
        return
    
    for req in my_requests:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{req['request_number']}** - {req['equipment_type']} {req['equipment_model']}")
                st.write(f"📱 {req['user_name']} | {req['user_phone']}")
                st.write(f"📝 {req['problem_description'][:100]}...")
            
            with col2:
                # Изменение статуса
                new_status = st.selectbox(
                    "Статус",
                    ["Новая заявка", "В процессе ремонта", "Готово к выдаче", "Выполнено"],
                    index=list(["Новая заявка", "В процессе ремонта", "Готово к выдаче", "Выполнено"]).index(req['status']),
                    key=f"status_{req['id']}",
                    format_func=get_status_name
                )
                
                if new_status != req['status']:
                    if st.button("🔄 Обновить", key=f"update_{req['id']}", use_container_width=True):
                        if database.update_request_status(req['id'], new_status, current_user['id']):
                            st.success("✓ Обновлено")
                            st.rerun()
                
                if st.button("💬 Комментарий", key=f"comment_{req['id']}", use_container_width=True):
                    show_add_comment_modal(req['id'], current_user)
            
            st.divider()

def show_statistics_page(current_user):
    """
    Страница статистики согласно п.2.5 ТЗ
    """
    if current_user['role'] not in ['Администратор', 'Менеджер']:
        st.warning("Эта страница доступна только администраторам и менеджерам")
        return
    
    st.title("📊 Статистика работы")
    
    stats = database.get_statistics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего заявок", stats['total_requests'])
    with col2:
        st.metric("Выполнено", stats['completed_requests'])
    with col3:
        active = stats['total_requests'] - stats['completed_requests']
        st.metric("Активных", active)
    
    st.divider()
    
    if stats['equipment_stats']:
        for item in stats['equipment_stats']:
            st.write(f"**{item['equipment_type']}**: {item['count']} заявок")
    else:
        st.info("Нет данных для отображения")

def show_users_page(current_user):
    """
    Страница управления пользователями (только для администратора)
    Упрощенная версия с надежными кнопками
    """
    if current_user['role'] != 'Администратор':
        st.warning("⛔ Эта страница доступна только администраторам")
        if st.button("← Назад", key="back_from_users"):
            st.session_state.page = "requests"
            st.rerun()
        return
    
    st.title("👥 Пользователи")
    
    tab1, tab2 = st.tabs(["📋 Список пользователей", "➕ Добавить пользователя"])
    
    with tab1:
        if 'editing_user_id' in st.session_state:
            user_to_edit = next((u for u in database.get_all_users() if u['id'] == st.session_state.editing_user_id), None)
            if user_to_edit:
                show_edit_user_modal(user_to_edit, current_user)
                return  
        if 'deleting_user_id' in st.session_state:
            user_to_delete = next((u for u in database.get_all_users() if u['id'] == st.session_state.deleting_user_id), None)
            if user_to_delete:
                show_delete_user_modal(user_to_delete, current_user)
                return 
        show_users_list_simple(current_user)
    
    with tab2:
        show_add_user_form(current_user)

def show_users_list_simple(current_user):
    """
    Упрощенный список пользователей с работающими кнопками
    """
    users = database.get_all_users()
    
    if not users:
        st.info("👤 Пользователи не найдены")
        return
    
    # Поиск
    search = st.text_input("🔍 Поиск по имени или логину", 
                          placeholder="Введите для поиска...",
                          key="simple_user_search")
    
    if search:
        users = [u for u in users if search.lower() in u['full_name'].lower() or 
                                       search.lower() in u['username'].lower()]
    
    # Фильтр по роли
    role_filter = st.selectbox("Фильтр по роли", 
                              ["Все", "Администратор", "Менеджер", "Специалист", "Оператор", "Заказчик"],
                              key="simple_role_filter")
    
    if role_filter != "Все":
        users = [u for u in users if u['role'] == role_filter]
    
    # Статистика
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Найдено пользователей", len(users))
    with col2:
        admins = sum(1 for u in users if u['role'] == 'Администратор')
    
    # Отображение пользователей
    for user in users:
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                # Иконка роли
                role_icons = {
                    'Администратор': '👑',
                    'Менеджер': '👔',
                    'Специалист': '👨‍🔧',
                    'Оператор': '📞',
                    'Заказчик': '👤'
                }
                icon = role_icons.get(user['role'], '👤')
                
                st.write(f"**{icon} {user['full_name']}**")
                st.write(f"👤 **Логин:** `{user['username']}`")
                st.write(f"📋 **Роль:** {user['role']}")
                st.write(f"📞 **Телефон:** {user['phone'] or 'не указан'}")
                st.write(f"📅 **Регистрация:** {user['created_at']}")
                
                if user['id'] == current_user['id']:
                    st.info("📍 Это вы")
            
            with col2:
                # Кнопка редактирования
                if user['id'] == current_user['id']:
                    st.button("✏️", disabled=True, key=f"edit_dis_{user['id']}", 
                             help="Нельзя редактировать себя")
                else:
                    # УБИРАЕМ session_state для кнопки
                    if st.button("✏️", key=f"edit_{user['id']}", help="Редактировать"):
                        st.session_state.editing_user_id = user['id']
                        st.rerun()
            
            with col3:
                # Кнопка удаления
                if user['id'] == current_user['id'] or user['role'] == 'Администратор':
                    st.button("🗑️", disabled=True, key=f"del_dis_{user['id']}", 
                             help="Нельзя удалить" + (" себя" if user['id'] == current_user['id'] else " администратора"))
                else:
                    # УБИРАЕМ session_state для кнопки
                    if st.button("🗑️", key=f"delete_{user['id']}", help="Удалить"):
                        st.session_state.deleting_user_id = user['id']
                        st.rerun()
            
            st.divider()

def show_add_user_form(current_user):
    """
    Форма добавления нового пользователя
    """
    st.subheader("➕ Добавить нового пользователя")
    
    # Форма добавления пользователя
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "Логин *",
                placeholder="Уникальное имя для входа",
                help="Логин должен быть уникальным",
                key="add_username"
            )
            
            password = st.text_input(
                "Пароль *",
                type="password",
                placeholder="Пароль для входа",
                help="Минимум 1 символ",
                key="add_password"
            )
            
            confirm_password = st.text_input(
                "Подтверждение пароля *",
                type="password",
                placeholder="Повторите пароль",
                key="add_confirm_password"
            )
        
        with col2:
            full_name = st.text_input(
                "Полное имя *",
                placeholder="Иванов Иван Иванович",
                key="add_full_name"
            )
            
            role = st.selectbox(
                "Роль *",
                ["Администратор", "Менеджер", "Специалист", "Оператор", "Заказчик", "Менеджер по качеству"],
                help="Выберите роль пользователя в системе",
                key="add_role"
            )
            
            phone = st.text_input(
                "Телефон",
                placeholder="+79990000000",
                help="Номер телефона для связи",
                key="add_phone"
            )

        submit_button = st.form_submit_button("✅ Добавить пользователя", type="primary")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Очистить форму", use_container_width=True, key="clear_form_btn"):
            if 'add_username' in st.session_state:
                del st.session_state.add_username
            if 'add_password' in st.session_state:
                del st.session_state.add_password
            if 'add_confirm_password' in st.session_state:
                del st.session_state.add_confirm_password
            if 'add_full_name' in st.session_state:
                del st.session_state.add_full_name
            if 'add_phone' in st.session_state:
                del st.session_state.add_phone
            st.rerun()
    
    with col2:
        if st.button("❌ Отмена", use_container_width=True, key="cancel_form_btn"):
            # Очищаем все и возвращаемся к списку
            clear_form_fields()
            st.session_state.page = "users"
            st.rerun()
    
    # Обработка отправки формы
    if submit_button:
        # Проверяем, что поля не пустые
        if not username or not password or not confirm_password or not full_name:
            st.error("❌ Заполните все обязательные поля (помеченные *)")
            return
        
        # Валидация
        errors = []
        
        if len(password) < 1:
            errors.append("Пароль должен быть не менее 6 символов")
        if password != confirm_password:
            errors.append("Пароли не совпадают")
        
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Создаем пользователя
            user_data = {
                'username': username,
                'password': password,
                'role': role,
                'full_name': full_name,
                'phone': phone
            }
            
            if database.create_user_db(user_data):
                st.success(f"✅ Пользователь {full_name} успешно добавлен!")
                
                # Очищаем поля формы
                clear_form_fields()
                
                # Ждем 2 секунды и обновляем
                import time
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Не удалось добавить пользователя. Возможно, логин уже занят.")

def clear_form_fields():
    """Функция для очистки полей формы"""
    keys_to_clear = [
        'add_username', 'add_password', 'add_confirm_password',
        'add_full_name', 'add_role', 'add_phone'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
        

def show_edit_user_modal(user, current_user):
    """
    Модальное окно редактирования пользователя
    """
    st.subheader(f"✏️ Редактирование пользователя: {user['full_name']}")
    
    # Поля формы
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Текущий логин:** `{user['username']}`")
        
        new_full_name = st.text_input(
            "Полное имя *",
            value=user['full_name'],
            key=f"edit_name_{user['id']}"
        )
        
        new_role = st.selectbox(
            "Роль *",
            ["Администратор", "Менеджер", "Специалист", "Оператор", "Заказчик"],
            index=["Администратор", "Менеджер", "Специалист", "Оператор", "Заказчик"].index(user['role']),
            key=f"edit_role_{user['id']}"
        )
    
    with col2:
        new_phone = st.text_input(
            "Телефон",
            value=user['phone'] if user['phone'] else "",
            placeholder="+79990000000",
            key=f"edit_phone_{user['id']}"
        )
        
        st.write("**Смена пароля (оставьте пустым, чтобы не менять):**")
        new_password = st.text_input(
            "Новый пароль",
            type="password",
            placeholder="Введите новый пароль",
            key=f"edit_pass_{user['id']}"
        )
        
        confirm_new_password = st.text_input(
            "Подтверждение пароля",
            type="password",
            placeholder="Повторите новый пароль",
            key=f"edit_confirm_{user['id']}"
        )
    
    # Кнопки
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Сохранить", type="primary", use_container_width=True, 
                    key=f"save_edit_{user['id']}"):
            # Валидация
            errors = []
            
            if not new_full_name:
                errors.append("Полное имя обязательно")
            
            if new_password:
                if len(new_password) < 6:
                    errors.append("Пароль должен быть не менее 6 символов")
                if new_password != confirm_new_password:
                    errors.append("Пароли не совпадают")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Подготавливаем данные для обновления
                update_data = {
                    'role': new_role,
                    'full_name': new_full_name,
                    'phone': new_phone
                }
                
                if new_password:
                    update_data['password'] = new_password
                
                if database.update_user_db(user['id'], update_data):
                    st.success("✅ Данные пользователя обновлены!")
                    
                    # Очищаем состояние и перезагружаем через 2 секунды
                    import time
                    time.sleep(2)
                    
                    if 'editing_user_id' in st.session_state:
                        del st.session_state.editing_user_id
                    st.rerun()
                else:
                    st.error("❌ Не удалось обновить данные пользователя")
    
    with col2:
        if st.button("🔄 Сбросить", use_container_width=True, key=f"reset_edit_{user['id']}"):
            st.rerun()
    
    with col3:
        if st.button("❌ Отмена", use_container_width=True, key=f"cancel_edit_{user['id']}"):
            if 'editing_user_id' in st.session_state:
                del st.session_state.editing_user_id
            st.rerun()
    
    if st.button("✖️ Закрыть", key=f"close_edit_{user['id']}"):
        if 'editing_user_id' in st.session_state:
            del st.session_state.editing_user_id
        st.rerun()

def show_delete_user_modal(user, current_user):
    """
    Модальное окно подтверждения удаления пользователя
    """
    st.warning("⚠️ **ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ**")
    
    st.write(f"**Вы собираетесь удалить пользователя:**")
    st.write(f"👤 **ФИО:** {user['full_name']}")
    st.write(f"🔑 **Логин:** {user['username']}")
    st.write(f"👑 **Роль:** {user['role']}")
    st.write(f"📞 **Телефон:** {user['phone'] or 'не указан'}")
    st.write(f"📅 **Дата регистрации:** {user['created_at']}")
    
    st.error("❌ **ВНИМАНИЕ:** Это действие нельзя отменить! Все данные пользователя будут удалены.")
    
    confirm_text = st.text_input(
        "Для подтверждения введите 'УДАЛИТЬ' (заглавными буквами):",
        placeholder="Введите УДАЛИТЬ",
        key=f"confirm_delete_{user['id']}"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Да, удалить", type="primary", use_container_width=True, 
                    key=f"confirm_delete_btn_{user['id']}"):
            if confirm_text == "УДАЛИТЬ":
                if database.delete_user_db(user['id']):
                    st.success(f"✅ Пользователь {user['full_name']} успешно удален!")
                    
                    if 'deleting_user_id' in st.session_state:
                        del st.session_state.deleting_user_id
                    
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Не удалось удалить пользователя")
            else:
                st.error("❌ Неправильное подтверждение. Введите 'УДАЛИТЬ' заглавными буквами.")
    
    with col2:
        if st.button("❌ Отмена", use_container_width=True, key=f"cancel_delete_btn_{user['id']}"):
            if 'deleting_user_id' in st.session_state:
                del st.session_state.deleting_user_id
            st.rerun()
    
    if st.button("✖️ Закрыть", key=f"close_delete_{user['id']}"):
        if 'deleting_user_id' in st.session_state:
            del st.session_state.deleting_user_id
        st.rerun()

def get_status_name(status_code):
    """
    Преобразование кода статуса в читаемое название
    """
    status_names = {
        'Новая заявка': 'Открыта',
        'В процессе ремонта': 'В работе',
        'Готово к выдаче': 'Готовые к выдаче',
        'Выполнено': 'Завершена'
    }
    return status_names.get(status_code, status_code)


def show_quality_control_page(current_user):
    """
    Страница для менеджера по качеству
    """
    if current_user['role'] != 'Менеджер по качеству':
        st.warning("⛔ Эта страница доступна только менеджерам по качеству")
        if st.button("← Назад"):
            st.session_state.page = "requests"
            st.rerun()
        return
    
    st.title("🔧 Управление качеством ремонта")
    
    # Вкладки для разных функций
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Проблемные заявки", 
        "👥 Привлечение специалистов", 
        "📅 Продление сроков",
        "📊 Аналитика качества"
    ])
    
    with tab1:
        show_problem_requests(current_user)
    
    with tab2:
        show_assign_specialists(current_user)
    
    with tab3:
        show_extend_deadlines(current_user)
    
    with tab4:
        show_quality_analytics(current_user)

def show_problem_requests(current_user):
    """
    Просмотр проблемных заявок
    """
    st.subheader("📋 Проблемные заявки, требующие вмешательства")
    
    col1, col2 = st.columns(2)
    
    with col1:
        problem_type = st.selectbox(
            "Тип проблемы",
            ["Все", "Просроченные", "Сложные случаи", "Конфликтные", "Технически сложные"],
            key="problem_filter"
        )
    
    with col2:
        days_overdue = st.slider(
            "Просрочка (дней)", 
            min_value=1, 
            max_value=30, 
            value=3,
            key="overdue_days"
        )
    
    all_requests = database.get_all_requests()
    
    problem_requests = []
    
    for req in all_requests:
        if req['status'] in ['Новая заявка', 'В процессе ремонта']:
            created_date = datetime.strptime(req['created_at'], '%Y-%m-%d') if isinstance(req['created_at'], str) else req['created_at']
            days_in_work = (datetime.now() - created_date).days
            
            if days_in_work > days_overdue:
                req['problem_type'] = 'Просроченная'
                req['days_overdue'] = days_in_work - days_overdue
                problem_requests.append(req)
    
        elif req['status'] == 'Готово к выдаче':
            if req.get('assigned_at'):
                assigned_date = datetime.strptime(req['assigned_at'], '%Y-%m-%d') if isinstance(req['assigned_at'], str) else req['assigned_at']
                days_waiting = (datetime.now() - assigned_date).days
                if days_waiting > 5:
                    req['problem_type'] = 'Длительное ожидание'
                    req['days_waiting'] = days_waiting
                    problem_requests.append(req)
    

    if problem_type != "Все":
        problem_requests = [r for r in problem_requests if r.get('problem_type', '') == problem_type]
    

    if problem_requests:
        st.warning(f"⚠️ Найдено проблемных заявок: {len(problem_requests)}")
        
        for req in problem_requests:
            with st.expander(f"🔴 {req['request_number']} - {req.get('problem_type', 'Проблема')}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Заказчик:** {req['user_name']}")
                    st.write(f"**Телефон:** {req['user_phone']}")
                    st.write(f"**Оборудование:** {req['equipment_type']} {req['equipment_model']}")
                    st.write(f"**Статус:** {req['status']}")
                
                with col2:
                    st.write(f"**Создана:** {req['created_at']}")
                    if req.get('assigned_name'):
                        st.write(f"**Ответственный:** {req['assigned_name']}")
                    if req.get('assigned_at'):
                        st.write(f"**Назначена:** {req['assigned_at']}")
                    
                    if req.get('days_overdue'):
                        st.error(f"**Просрочка:** {req['days_overdue']} дней")
                    if req.get('days_waiting'):
                        st.warning(f"**Ожидание:** {req['days_waiting']} дней")
                
                col_actions = st.columns(3)
                
                with col_actions[0]:
                    if st.button("👁️ Подробнее", key=f"view_prob_{req['id']}"):
                        st.session_state.selected_request = req['id']
                        st.rerun()
                
                with col_actions[1]:
                    if st.button("👥 Привлечь специалиста", key=f"assign_prob_{req['id']}"):
                        st.session_state.assign_to_request = req['id']
                        st.rerun()
                
                with col_actions[2]:
                    if st.button("📅 Продлить срок", key=f"extend_prob_{req['id']}"):
                        st.session_state.extend_request = req['id']
                        st.rerun()

                with st.form(key=f"quality_comment_{req['id']}"):
                    comment = st.text_area(
                        "Рекомендации/комментарии",
                        placeholder="Введите рекомендации для специалиста или комментарии по заявке...",
                        key=f"comment_{req['id']}"
                    )
                    
                    if st.form_submit_button("💾 Добавить комментарий"):
                        if comment:
                            database.add_comment(
                                req['id'], 
                                current_user['id'], 
                                f"👨‍💼 Менеджер по качеству: {comment}",
                                is_technical=True
                            )
                            st.success("✅ Комментарий добавлен")
                            st.rerun()
    else:
        st.success("✅ Проблемных заявок не обнаружено")

def show_assign_specialists(current_user):
    """
    Привлечение дополнительных специалистов
    """
    st.subheader("👥 Привлечение специалистов к сложным заявкам")
    

    all_requests = database.get_all_requests()
    
    need_help_requests = []
    
    for req in all_requests:
        if req['status'] == 'В процессе ремонта':
            if req.get('assigned_at'):
                assigned_date = datetime.strptime(req['assigned_at'], '%Y-%m-%d') if isinstance(req['assigned_at'], str) else req['assigned_at']
                days_in_progress = (datetime.now() - assigned_date).days
                if days_in_progress > 3:
                    req['days_in_progress'] = days_in_progress
                    need_help_requests.append(req)
        
        comments = database.get_comments(req['id'])
        technical_notes = [c for c in comments if c.get('is_technical_note') and 'сложн' in c.get('comment_text', '').lower()]
        if technical_notes:
            req['technical_issues'] = True
            need_help_requests.append(req)
    
    if need_help_requests:
        st.write(f"**Заявки, требующие дополнительных специалистов:** {len(need_help_requests)}")
        
        for req in need_help_requests:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{req['request_number']}** - {req['equipment_type']}")
                    st.write(f"Заказчик: {req['user_name']} | Статус: {req['status']}")
                    
                    if req.get('days_in_progress'):
                        st.warning(f"В работе: {req['days_in_progress']} дней")
                    if req.get('technical_issues'):
                        st.error("Есть технические сложности")
                    
                    if req.get('assigned_name'):
                        st.write(f"Текущий специалист: {req['assigned_name']}")
                
                with col2:
                    with st.form(key=f"add_specialist_{req['id']}"):
                        technicians = database.get_technicians()
                        
                        if technicians:
                            available_techs = [
                                t for t in technicians 
                                if t.get('id') != req.get('assigned_to')
                            ]
                            
                            if available_techs:
                                tech_names = [t['full_name'] for t in available_techs]
                                selected_tech = st.selectbox(
                                    "Выберите специалиста",
                                    tech_names,
                                    key=f"select_tech_{req['id']}"
                                )
                                
                                reason = st.text_area(
                                    "Причина привлечения",
                                    placeholder="Опишите причину привлечения дополнительного специалиста...",
                                    key=f"reason_{req['id']}",
                                    height=60
                                )
                                
                                if st.form_submit_button("👥 Привлечь специалиста"):
                                  
                                    for tech in available_techs:
                                        if tech['full_name'] == selected_tech:
                                         
                                            database.add_comment(
                                                req['id'],
                                                current_user['id'],
                                                f"👨‍💼 Менеджер по качеству привлек дополнительного специалиста: {selected_tech}. Причина: {reason}",
                                                is_technical=True
                                            )
                                            
                        
                                            st.success(f"✅ Специалист {selected_tech} привлечен к заявке")
                                            st.rerun()
                                            break
                            else:
                                st.info("Нет доступных специалистов")
                        else:
                            st.info("Нет специалистов в системе")
                
                st.divider()
    else:
        st.success("✅ В настоящее время не требуется привлечение дополнительных специалистов")

def show_extend_deadlines(current_user):
    """
    Продление сроков выполнения заявок
    """
    st.subheader("📅 Продление сроков выполнения заявок")
    
    # Получаем заявки, которые могут требовать продления
    all_requests = database.get_all_requests()
    
    extend_candidates = []
    
    for req in all_requests:
        # Заявки в работе, которым может потребоваться продление
        if req['status'] in ['В процессе ремонта', 'Готово к выдаче']:
            extend_candidates.append(req)
    
    if extend_candidates:
        st.info("ℹ️ Выберите заявку для продления срока выполнения")
        
        # Список заявок для выбора
        request_options = {
            f"{r['request_number']} - {r['user_name']} - {r['status']}": r['id'] 
            for r in extend_candidates
        }
        
        selected_request_label = st.selectbox(
            "Выберите заявку",
            list(request_options.keys()),
            key="select_extend_request"
        )
        
        if selected_request_label:
            request_id = request_options[selected_request_label]
            request = next(r for r in extend_candidates if r['id'] == request_id)
            
            st.divider()
            st.write(f"**Выбрана заявка:** {request['request_number']}")
            st.write(f"**Заказчик:** {request['user_name']} ({request['user_phone']})")
            st.write(f"**Оборудование:** {request['equipment_type']} {request['equipment_model']}")
            st.write(f"**Текущий статус:** {request['status']}")
            st.write(f"**Дата создания:** {request['created_at']}")
            
            if request.get('assigned_at'):
                st.write(f"**Дата назначения:** {request['assigned_at']}")
            
            # Форма продления срока
            with st.form(key=f"extend_form_{request_id}"):
                st.write("**Продление срока выполнения:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    extension_days = st.number_input(
                        "Количество дней продления",
                        min_value=1,
                        max_value=30,
                        value=3,
                        key=f"days_{request_id}"
                    )
                
                with col2:
                    extension_reason = st.selectbox(
                        "Причина продления",
                        [
                            "Ожидание комплектующих",
                            "Техническая сложность ремонта",
                            "Необходимость дополнительной диагностики",
                            "Другие обстоятельства"
                        ],
                        key=f"reason_ext_{request_id}"
                    )
                
                customer_agreement = st.checkbox(
                    "Согласовано с заказчиком",
                    key=f"agreement_{request_id}"
                )
                
                customer_comments = st.text_area(
                    "Комментарии заказчика (если есть)",
                    placeholder="Запишите комментарии или пожелания заказчика...",
                    key=f"cust_comments_{request_id}",
                    height=80
                )
                
                additional_notes = st.text_area(
                    "Дополнительные заметки",
                    placeholder="Внутренние заметки для специалистов...",
                    key=f"notes_{request_id}",
                    height=80
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    submit_extend = st.form_submit_button("✅ Продлить срок", type="primary")
                with col2:
                    cancel_extend = st.form_submit_button("❌ Отмена")
                
                if submit_extend:
                    if not customer_agreement:
                        st.error("❌ Для продления срока необходимо согласование с заказчиком!")
                    else:
                        # Добавляем комментарий о продлении
                        comment_text = f"""
👨‍💼 Менеджер по качеству продлил срок выполнения на {extension_days} дней.
📋 Причина: {extension_reason}
✅ Согласовано с заказчиком: Да
💬 Комментарии заказчика: {customer_comments if customer_comments else "не указаны"}
📝 Заметки: {additional_notes if additional_notes else "нет"}
                        """.strip()
                        
                        database.add_comment(
                            request_id,
                            current_user['id'],
                            comment_text,
                            is_technical=True
                        )
                        
                        st.success(f"""
✅ Срок выполнения заявки продлен на {extension_days} дней!

**Заказчик уведомлен о продлении срока.**
Специалисты будут работать над заявкой с учетом нового срока.
                        """)

                        
                        st.rerun()
    else:
        st.success("✅ Нет заявок, требующих продления сроков")

def show_quality_analytics(current_user):
    """
    Аналитика качества ремонта
    """
    st.subheader("📊 Аналитика качества обслуживания")
    
    # Получаем все заявки для анализа
    all_requests = database.get_all_requests()
    
    if not all_requests:
        st.info("📭 Нет данных для анализа")
        return
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = len(all_requests)
        st.metric("Всего заявок", total)
    
    with col2:
        completed = sum(1 for r in all_requests if r['status'] == 'Выполнено')
        st.metric("Выполнено", completed)
    
    with col3:
        in_progress = sum(1 for r in all_requests if r['status'] in ['В процессе ремонта', 'Готово к выдаче'])
        st.metric("В работе", in_progress)
    
    with col4:
        overdue = sum(1 for r in all_requests if r['status'] in ['Новая заявка', 'В процессе ремонта'] 
                     and (datetime.now() - datetime.strptime(r['created_at'], '%Y-%m-%d')).days > 3)
        st.metric("Просрочено", overdue)
    
    st.divider()
    
    # Анализ по типам оборудования
    st.write("**📈 Распределение проблем по типам оборудования:**")
    
    equipment_stats = {}
    for req in all_requests:
        eq_type = req['equipment_type']
        if eq_type not in equipment_stats:
            equipment_stats[eq_type] = {'total': 0, 'problems': 0}
        equipment_stats[eq_type]['total'] += 1
        
        # Определяем "проблемные" заявки
        if req['status'] in ['Новая заявка', 'В процессе ремонта']:
            days_old = (datetime.now() - datetime.strptime(req['created_at'], '%Y-%m-%d')).days
            if days_old > 3:
                equipment_stats[eq_type]['problems'] += 1
    
    # Выводим статистику
    for eq_type, stats in equipment_stats.items():
        problem_percent = (stats['problems'] / stats['total'] * 100) if stats['total'] > 0 else 0
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.write(f"**{eq_type}:**")
            st.write(f"Всего: {stats['total']}, Проблемы: {stats['problems']}")
        
        with col2:
            st.progress(problem_percent / 100)
            st.caption(f"{problem_percent:.1f}% проблемных заявок")
    
    st.divider()
    
    # Рекомендации по улучшению качества
    st.subheader("💡 Рекомендации по улучшению качества")
    
    recommendations = []
    
    # Анализ и формирование рекомендаций
    if overdue > total * 0.1:  # Если более 10% заявок просрочено
        recommendations.append("📅 **Увеличить количество специалистов** для обработки заявок")
    
    # Проверяем среднее время выполнения
    completed_requests = [r for r in all_requests if r['status'] == 'Выполнено']
    if completed_requests:
        avg_completion_days = sum(
            (datetime.strptime(r.get('completed_at', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d') - 
             datetime.strptime(r['created_at'], '%Y-%m-%d')).days 
            for r in completed_requests
        ) / len(completed_requests)
        
        if avg_completion_days > 5:
            recommendations.append("⏱️ **Оптимизировать процессы ремонта** для сокращения времени выполнения")
    
    # Рекомендации по обучению
    problematic_types = [eq_type for eq_type, stats in equipment_stats.items() 
                        if stats['problems'] / stats['total'] > 0.2]  # Более 20% проблем
    
    if problematic_types:
        recommendations.append(f"🎓 **Провести обучение специалистов** по работе с: {', '.join(problematic_types)}")
    
    # Выводим рекомендации
    if recommendations:
        st.write("**Рекомендуемые действия:**")
        for rec in recommendations:
            st.success(rec)
    else:
        st.success("✅ Качество обслуживания на хорошем уровне!")


def show_customer_requests_page(current_user):
    """
    Специальная страница для заказчиков
    """
    st.title("📋 Мои заявки")
    
    # Статистика для заказчика
    col1, col2, col3 = st.columns(3)
    
    # Получаем все заявки заказчика
    customer_requests = database.get_requests_by_customer(
        current_user['full_name'], 
        current_user.get('phone', '')
    )
    
    with col1:
        total = len(customer_requests)
        st.metric("Всего заявок", total)
    
    with col2:
        completed = sum(1 for r in customer_requests if r['status'] == 'Выполнено')
        st.metric("Выполнено", completed)
    
    with col3:
        in_progress = sum(1 for r in customer_requests if r['status'] in ['В процессе ремонта', 'Готово к выдаче'])
        st.metric("В работе", in_progress)
    
    # Кнопка создания заявки
    if st.button("➕ Создать новую заявку", type="primary", key="customer_create"):
        st.session_state.show_create_form = True
        st.rerun()
    
    # Фильтры для заказчика
    if customer_requests:
        st.divider()
        
        # Простые фильтры
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox(
                "Фильтр по статусу",
                ["Все", "Новая заявка", "В процессе ремонта", "Готово к выдаче", "Выполнено"],
                key="customer_filter"
            )
        
        # Применяем фильтр
        filtered_requests = customer_requests
        if status_filter != "Все":
            filtered_requests = [r for r in customer_requests if r['status'] == status_filter]
        
        # Отображение заявок
        st.write(f"**Найдено заявок:** {len(filtered_requests)}")
        
        for req in filtered_requests:
            with st.container():
                # Карточка заявки
                with st.expander(f"📋 {req['request_number']} - {req['equipment_type']}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Статус:** {req['status']}")
                        st.write(f"**Оборудование:** {req['equipment_type']} {req['equipment_model']}")
                        st.write(f"**Дата создания:** {req['created_at']}")
                    
                    with col2:
                        if req['assigned_name']:
                            st.write(f"**Ответственный:** {req['assigned_name']}")
                        if req['assigned_at']:
                            st.write(f"**Назначена:** {req['assigned_at']}")
                        if req['completed_at']:
                            st.write(f"**Завершена:** {req['completed_at']}")
                    
                    st.write(f"**Описание проблемы:**")
                    st.info(req['problem_description'])
                    
                    # Кнопка подробнее
                    if st.button("👁️ Подробнее", key=f"cust_view_{req['id']}"):
                        st.session_state.selected_request = req['id']
                        st.rerun()
        
        if not filtered_requests:
            st.info("📭 Заявок по выбранному фильтру не найдено")
    else:
        st.info("""
        📭 У вас еще нет заявок!
        
        **Создайте первую заявку:**
        1. Нажмите кнопку "➕ Создать новую заявку"
        2. Заполните информацию об оборудовании
        3. Опишите проблему
        4. Отправьте заявку
        
        После создания с вами свяжется специалист!
        """)


def main():
    """
    Главная функция приложения
    """
    if not auth.check_auth():
        auth.show_login_form()
        return
    
    current_user = auth.get_current_user()
    
    with st.sidebar:
        st.write(f"👤 **{current_user['full_name']}**")
        st.write(f"📋 Роль: {current_user['role']}")
        st.divider()
        menu_items = []

        menu_items.append(("📋 Мои заявки" if current_user['role'] == 'Заказчик' else "📋 Все заявки", "requests"))

        if current_user['role'] == 'Специалист':
            menu_items.append(("👨‍🔧 Мои задачи", "my_tasks"))

        if current_user['role'] == 'Менеджер по качеству':
            menu_items.append(("🔧 Управление качеством", "quality_control"))

        if current_user['role'] in ['Администратор', 'Менеджер']:
            menu_items.append(("📊 Статистика", "statistics"))

        if current_user['role'] == 'Администратор':
            menu_items.append(("👥 Управление пользователями", "users"))
        

        for text, page in menu_items:
            if st.button(text, use_container_width=True, key=f"nav_{page}"):
                st.session_state.page = page
 
                for key in ['selected_request', 'editing_request', 'show_create_form', 'search_term']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        if current_user['role'] == 'Заказчик':
            st.divider()
            st.write("**Быстрые действия:**")
            if st.button("🚀 Создать новую заявку", type="primary", use_container_width=True, key="quick_create"):
                st.session_state.show_create_form = True
                st.session_state.page = "requests"
                st.rerun()
        
        st.divider()
        
        if st.button("🚪 Выйти", use_container_width=True, key="logout_btn"):
            auth.logout_user()
            st.rerun()
    

    if 'page' not in st.session_state:
        st.session_state.page = "requests"
    
    if 'editing_request' in st.session_state and st.session_state.editing_request:
        show_edit_request_page(st.session_state.editing_request, current_user)
        return

    if 'selected_request' in st.session_state and st.session_state.selected_request:
        show_request_detail_page(st.session_state.selected_request, current_user)
        return
    

    if st.session_state.page == "requests":
        if current_user['role'] == 'Заказчик':
            show_customer_requests_page(current_user)
        else:
            show_requests_page(current_user)
    elif st.session_state.page == "my_tasks":
        show_my_tasks_page(current_user)
    elif st.session_state.page == "statistics":
        show_statistics_page(current_user)
    elif st.session_state.page == "users":
        show_users_page(current_user)
    elif st.session_state.page == "quality_control":  
        show_quality_control_page(current_user)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Учет заявок на ремонт",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    main()