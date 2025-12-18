BEGIN TRANSACTION;
CREATE TABLE comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        comment_text TEXT NOT NULL,
        is_technical_note BOOLEAN DEFAULT 0,
        parts_ordered TEXT,
        created_at DATE DEFAULT (date('now')),
        FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
CREATE TABLE requests (
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
    );
INSERT INTO "requests" VALUES(1,'REQ-2025-0001','2023-06-06','Кондиционер','TCL TAC-12CHSA/TPG-W белый','Не охлаждает воздух','Петров Никита Артёмович','89219567841','В процессе ремонта',3,'2023-06-06',NULL);
INSERT INTO "requests" VALUES(2,'REQ-2025-0002','2023-05-05','Кондиционер','Electrolux EACS/I-09HAT/N3_21Y белый','Выключается сам по себе','Ковалева Софья Владимировна','89219567842','В процессе ремонта',7,'2023-05-05',NULL);
INSERT INTO "requests" VALUES(3,'REQ-2025-0003','2022-07-07','Увлажнитель воздуха','Xiaomi Smart Humidifier 2','Пар имеет неприятный запах','Кузнецов Сергей Матвеевич','89219567843','Готово к выдаче',7,'2022-08-07','2023-01-01');
INSERT INTO "requests" VALUES(4,'REQ-2025-0004','2023-08-02','Увлажнитель воздуха','Polaris PUH 2300 WIFI IQ Home','Увлажнитель воздуха продолжает работать при предельном снижении уровня воды','Ковалева Софья Владимировна','89219567842','Новая заявка',NULL,NULL,NULL);
INSERT INTO "requests" VALUES(5,'REQ-2025-0005','2023-08-02','Сушилка для рук','Ballu BAHD-1250','Не работает','Кузнецов Сергей Матвеевич','89219567843','В процессе ремонта',9,'2025-12-16',NULL);
CREATE TABLE status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        changed_by INTEGER NOT NULL,
        changed_at DATE DEFAULT (date('now')),
        FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by) REFERENCES users(id)
    );
INSERT INTO "status_history" VALUES(1,1,'Новая заявка','В процессе ремонта',1,'2025-12-16');
INSERT INTO "status_history" VALUES(2,2,'Новая заявка','В процессе ремонта',1,'2025-12-16');
INSERT INTO "status_history" VALUES(3,3,'Новая заявка','Готово к выдаче',1,'2025-12-16');
INSERT INTO "status_history" VALUES(4,5,'Новая заявка','В процессе ремонта',1,'2025-12-16');
CREATE TABLE "users" (
	"id"	INTEGER,
	"username"	TEXT NOT NULL UNIQUE,
	"password_hash"	TEXT NOT NULL,
	"role"	TEXT NOT NULL CHECK("role" IN ('Администратор', 'Менеджер', 'Специалист', 'Оператор', 'Заказчик', 'Менеджер по качеству')),
	"full_name"	TEXT NOT NULL,
	"phone"	TEXT,
	"created_at"	DATE DEFAULT (date('now')),
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "users" VALUES(1,'admin','240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9','Администратор','Главный Администратор','+79990000000','2025-12-15');
INSERT INTO "users" VALUES(2,'manager','866485796cfa8d7c0cf7111640205b83076433547577511d81f8030ae99ecea5','Менеджер','Широков Василий Матвеевич','+79991111111','2025-12-15');
INSERT INTO "users" VALUES(3,'tech','3ac40463b419a7de590185c7121f0bfbe411d6168699e8014f521b050b1d6653','Специалист','Кудрявцева Ева Ивановна','+79992222222','2025-12-15');
INSERT INTO "users" VALUES(4,'operator','ec6e1c25258002eb1c67d15c7f45da7945fa4c58778fd7d88faa5e53e3b4698d','Оператор','Гусева Виктория Данииловна','+79993333333','2025-12-15');
INSERT INTO "users" VALUES(5,'customer','b041c0aeb35bb0fa4aa668ca5a920b590196fdaf9a00eb852c9b7f4d123cc6d6','Заказчик','Овчинников Фёдор Никитич','+79994444444','2025-12-15');
INSERT INTO "users" VALUES(6,'login5','0eeac8171768d0cdef3a20fee6db4362d019c91e10662a6b55186336e1a42778','Оператор','Баранов Артём Юрьевич','89994563847','2025-12-15');
INSERT INTO "users" VALUES(7,'login3','3acb59306ef6e660cf832d1d34c4fba3d88d616f0bb5c2a9e0f82d18ef6fc167','Специалист','Гончарова Ульяна Ярославовна','89210673849','2025-12-15');
INSERT INTO "users" VALUES(9,'login10','b35892cb8b089e03e4420b94df688122a2b76d4ad0f8b94ad20808bb029e48a5','Специалист','Беспалова Екатерина Даниэльевна','89219567844','2025-12-16');
INSERT INTO "users" VALUES(10,'login7','4a6b7fa040bcfc734a113fee84d3789c0a626d70d029afad0d1c3e7b6c562e14','Заказчик','Петров Никита Артёмович','89219567841','2025-12-16');
INSERT INTO "users" VALUES(11,'login8','c8fea5b0b76dc690feaf5544749f99b40e78e2a37c0e867a086696509416302a','Заказчик','Ковалева Софья Владимировна','89219567842','2025-12-16');
INSERT INTO "users" VALUES(12,'login9','2d4589473fb3f4581d7452cd25182159d68d2a50056a0cce35a529b010e32f2b','Заказчик','Кузнецов Сергей Матвеевич','89219567843','2025-12-16');
INSERT INTO "users" VALUES(14,'kach','8aba6f3c8a865d38f97cf989eb4c567e3eb41ab29f3cf9aebce82aba24141b55','Менеджер по качеству','Йоу','+71111111111','2025-12-17');
CREATE INDEX idx_requests_status ON requests(status);
CREATE INDEX idx_requests_assigned ON requests(assigned_to);
CREATE INDEX idx_requests_number ON requests(request_number);
CREATE INDEX idx_comments_request ON comments(request_id);
CREATE INDEX idx_requests_date ON requests(created_at);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('requests',5);
INSERT INTO "sqlite_sequence" VALUES('status_history',4);
INSERT INTO "sqlite_sequence" VALUES('users',14);
COMMIT;
