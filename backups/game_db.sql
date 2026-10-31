--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: battle; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.battle (
    id bigint NOT NULL,
    battle_name character varying NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    location character varying NOT NULL,
    result character varying NOT NULL,
    importance_level character varying,
    CONSTRAINT battle_importance_level_check CHECK (((importance_level)::text = ANY (ARRAY[('стратегическая'::character varying)::text, ('фронтовая'::character varying)::text, ('тактическая'::character varying)::text])))
);


ALTER TABLE public.battle OWNER TO postgres;

--
-- Name: battle_enemy_unit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.battle_enemy_unit (
    battle_id bigint NOT NULL,
    enemy_unit_id bigint NOT NULL
);


ALTER TABLE public.battle_enemy_unit OWNER TO postgres;

--
-- Name: COLUMN battle_enemy_unit.battle_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.battle_enemy_unit.battle_id IS 'Связь между боями и участвовавшими немецкими частями';


--
-- Name: battle_military_unit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.battle_military_unit (
    battle_id bigint NOT NULL,
    unit_id bigint NOT NULL
);


ALTER TABLE public.battle_military_unit OWNER TO postgres;

--
-- Name: TABLE battle_military_unit; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.battle_military_unit IS 'Связь между сражениями и участвовавшими советскими частями';


--
-- Name: enemy_unit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.enemy_unit (
    id bigint NOT NULL,
    unit_name character varying NOT NULL,
    unit_type character varying NOT NULL,
    commander character varying NOT NULL,
    location character varying NOT NULL,
    formation_date date NOT NULL,
    destruction_date date,
    CONSTRAINT enemy_unit_unit_type_check CHECK (((unit_type)::text = ANY (ARRAY[('танковая'::character varying)::text, ('пехотная'::character varying)::text, ('авиационная'::character varying)::text, ('СС'::character varying)::text, ('артиллерийская'::character varying)::text, ('резервная'::character varying)::text])))
);


ALTER TABLE public.enemy_unit OWNER TO postgres;

--
-- Name: TABLE enemy_unit; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.enemy_unit IS 'Подразделения вермахта и СС с историческими данными';


--
-- Name: COLUMN enemy_unit.unit_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.enemy_unit.unit_type IS 'Тип подразделения: танковая, пехотная, авиационная, СС и др.';


--
-- Name: COLUMN enemy_unit.commander; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.enemy_unit.commander IS 'Командир части на момент наибольшей активности';


--
-- Name: equipment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipment (
    id bigint NOT NULL,
    unit_id bigint,
    equipment_type character varying NOT NULL,
    item_name character varying NOT NULL,
    quantity integer NOT NULL,
    last_replenishment date NOT NULL
);


ALTER TABLE public.equipment OWNER TO postgres;

--
-- Name: equipment_assignment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipment_assignment (
    id bigint NOT NULL,
    soldier_id bigint,
    equipment_id bigint,
    issue_date date NOT NULL,
    quantity integer NOT NULL
);


ALTER TABLE public.equipment_assignment OWNER TO postgres;

--
-- Name: equipment_audit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipment_audit (
    id integer NOT NULL,
    item_name character varying NOT NULL,
    added_at date DEFAULT CURRENT_DATE
);


ALTER TABLE public.equipment_audit OWNER TO postgres;

--
-- Name: equipment_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipment_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.equipment_audit_id_seq OWNER TO postgres;

--
-- Name: equipment_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipment_audit_id_seq OWNED BY public.equipment_audit.id;


--
-- Name: medal; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medal (
    id bigint NOT NULL,
    medal_name character varying NOT NULL,
    establishment_date date NOT NULL,
    award_criteria text
);


ALTER TABLE public.medal OWNER TO postgres;

--
-- Name: military_service; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.military_service (
    id bigint NOT NULL,
    soldier_id bigint,
    unit_id bigint,
    start_date date NOT NULL,
    end_date date
);


ALTER TABLE public.military_service OWNER TO postgres;

--
-- Name: military_unit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.military_unit (
    id bigint NOT NULL,
    unit_name character varying NOT NULL,
    unit_type character varying NOT NULL,
    location character varying NOT NULL,
    formation_date date NOT NULL,
    combat_efficiency numeric
);


ALTER TABLE public.military_unit OWNER TO postgres;

--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schema_migrations (
    id integer NOT NULL,
    version character varying(255) NOT NULL,
    applied_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.schema_migrations OWNER TO postgres;

--
-- Name: schema_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.schema_migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.schema_migrations_id_seq OWNER TO postgres;

--
-- Name: schema_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.schema_migrations_id_seq OWNED BY public.schema_migrations.id;


--
-- Name: soldier; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.soldier (
    id bigint NOT NULL,
    full_name character varying NOT NULL,
    birth_year integer NOT NULL,
    gender character varying,
    rank character varying NOT NULL,
    branch character varying NOT NULL,
    enlistment_city character varying NOT NULL,
    status character varying,
    enlistment_date date NOT NULL,
    CONSTRAINT soldier_gender_check CHECK (((gender)::text = ANY (ARRAY[('мужской'::character varying)::text, ('женский'::character varying)::text]))),
    CONSTRAINT soldier_status_check CHECK (((status)::text = ANY (ARRAY[('жив'::character varying)::text, ('убит'::character varying)::text, ('пропал без вести'::character varying)::text, ('ранен'::character varying)::text])))
);


ALTER TABLE public.soldier OWNER TO postgres;

--
-- Name: soldier_medal; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.soldier_medal (
    soldier_id bigint NOT NULL,
    medal_id bigint NOT NULL,
    award_date date NOT NULL
);


ALTER TABLE public.soldier_medal OWNER TO postgres;

--
-- Name: equipment_audit id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_audit ALTER COLUMN id SET DEFAULT nextval('public.equipment_audit_id_seq'::regclass);


--
-- Name: schema_migrations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schema_migrations ALTER COLUMN id SET DEFAULT nextval('public.schema_migrations_id_seq'::regclass);


--
-- Data for Name: battle; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.battle VALUES (1, 'Оборона Брестской крепости', '1941-06-22', '1941-06-29', 'Брест', 'сдерживание противника', 'стратегическая');
INSERT INTO public.battle VALUES (2, 'Битва за Москву', '1941-09-30', '1942-04-20', 'Москва', 'победа СССР', 'стратегическая');
INSERT INTO public.battle VALUES (3, 'Сталинградская битва', '1942-07-17', '1943-02-02', 'Сталинград', 'окружение армии Паулюса', 'стратегическая');
INSERT INTO public.battle VALUES (4, 'Курская битва', '1943-07-05', '1943-08-23', 'Курск', 'разгром немецких танковых сил', 'стратегическая');
INSERT INTO public.battle VALUES (5, 'Операция "Багратион"', '1944-06-23', '1944-08-29', 'Белоруссия', 'освобождение Белоруссии', 'стратегическая');
INSERT INTO public.battle VALUES (6, 'Блокада Ленинграда', '1941-09-08', '1944-01-27', 'Ленинград', 'прорыв блокады', 'фронтовая');
INSERT INTO public.battle VALUES (7, 'Оборона Севастополя', '1941-10-30', '1942-07-04', 'Севастополь', 'временная потеря города', 'тактическая');
INSERT INTO public.battle VALUES (8, 'Битва за Берлин', '1945-04-16', '1945-05-08', 'Берлин', 'взятие столицы Рейха', 'стратегическая');
INSERT INTO public.battle VALUES (9, 'Висло-Одерская операция', '1945-01-12', '1945-02-03', 'Польша', 'освобождение Польши', 'фронтовая');
INSERT INTO public.battle VALUES (10, 'Будапештская операция', '1944-10-29', '1945-02-13', 'Венгрия', 'капитуляция гарнизона', 'тактическая');
INSERT INTO public.battle VALUES (11, 'Ржевская битва', '1942-01-08', '1943-03-31', 'Ржев', 'тактическая победа вермахта', 'фронтовая');
INSERT INTO public.battle VALUES (12, 'Оборона Заполярья', '1941-06-29', '1944-10-01', 'Мурманск', 'срыв плана "Серебряная лисица"', 'тактическая');
INSERT INTO public.battle VALUES (13, 'Харьковская операция', '1942-05-12', '1942-05-28', 'Харьков', 'окружение советских войск', 'фронтовая');
INSERT INTO public.battle VALUES (14, 'Смоленское сражение', '1941-07-10', '1941-09-10', 'Смоленск', 'задержка наступления на Москву', 'стратегическая');
INSERT INTO public.battle VALUES (15, 'Битва за Днепр', '1943-08-26', '1943-12-23', 'Днепр', 'освобождение Киева', 'стратегическая');
INSERT INTO public.battle VALUES (16, 'Оборона Брестской крепости', '1941-06-22', '1941-06-29', 'Брест', 'героическая оборона', 'стратегическая');
INSERT INTO public.battle VALUES (17, 'Таллинский переход', '1941-08-27', '1941-08-30', 'Балтийское море', 'эвакуация флота', 'тактическая');
INSERT INTO public.battle VALUES (18, 'Демянская операция', '1942-02-20', '1942-05-20', 'Новгородская обл.', 'окружение демянской группировки', 'фронтовая');
INSERT INTO public.battle VALUES (19, 'Прорыв блокады Ленинграда', '1943-01-12', '1943-01-30', 'Ленинград', 'операция "Искра"', 'стратегическая');
INSERT INTO public.battle VALUES (20, 'Корсунь-Шевченковская операция', '1944-01-24', '1944-02-17', 'Украина', 'разгром группировки вермахта', 'фронтовая');
INSERT INTO public.battle VALUES (21, 'Битва за Воронеж', '1942-06-28', '1943-01-25', 'Воронеж', 'освобождение города', 'фронтовая');
INSERT INTO public.battle VALUES (22, 'Керченско-Эльтигенская операция', '1943-10-31', '1943-12-11', 'Керчь', 'плацдарм для Крыма', 'тактическая');
INSERT INTO public.battle VALUES (23, 'Балатонская операция', '1945-03-06', '1945-03-15', 'Венгрия', 'отражение контрудара', 'стратегическая');
INSERT INTO public.battle VALUES (24, 'Восточно-Прусская операция', '1945-01-13', '1945-04-25', 'Кёнигсберг', 'ликвидация группировки', 'стратегическая');
INSERT INTO public.battle VALUES (25, 'Маньчжурская операция', '1945-08-09', '1945-09-02', 'Маньчжурия', 'разгром Квантунской армии', 'стратегическая');
INSERT INTO public.battle VALUES (26, 'Битва за Кавказ', '1942-07-25', '1943-10-09', 'Кавказ', 'освобождение нефтяных районов', 'стратегическая');
INSERT INTO public.battle VALUES (27, 'Оборона Тулы', '1941-10-24', '1941-12-05', 'Тула', 'срыв плана окружения Москвы', 'фронтовая');
INSERT INTO public.battle VALUES (28, 'Берлинская операция', '1945-04-16', '1945-05-08', 'Берлин', 'капитуляция Германии', 'стратегическая');
INSERT INTO public.battle VALUES (29, 'Пражская операция', '1945-05-06', '1945-05-11', 'Прага', 'освобождение Чехословакии', 'фронтовая');
INSERT INTO public.battle VALUES (30, 'Битва при Дебрецене', '1944-10-06', '1944-10-29', 'Венгрия', 'прорыв к Будапешту', 'тактическая');


--
-- Data for Name: battle_enemy_unit; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.battle_enemy_unit VALUES (3, 1);
INSERT INTO public.battle_enemy_unit VALUES (4, 2);
INSERT INTO public.battle_enemy_unit VALUES (14, 5);
INSERT INTO public.battle_enemy_unit VALUES (8, 3);
INSERT INTO public.battle_enemy_unit VALUES (11, 9);
INSERT INTO public.battle_enemy_unit VALUES (20, 10);
INSERT INTO public.battle_enemy_unit VALUES (12, 11);
INSERT INTO public.battle_enemy_unit VALUES (18, 13);
INSERT INTO public.battle_enemy_unit VALUES (14, 14);
INSERT INTO public.battle_enemy_unit VALUES (16, 16);
INSERT INTO public.battle_enemy_unit VALUES (3, 17);
INSERT INTO public.battle_enemy_unit VALUES (4, 18);
INSERT INTO public.battle_enemy_unit VALUES (3, 19);
INSERT INTO public.battle_enemy_unit VALUES (6, 20);
INSERT INTO public.battle_enemy_unit VALUES (7, 21);
INSERT INTO public.battle_enemy_unit VALUES (4, 22);
INSERT INTO public.battle_enemy_unit VALUES (3, 23);
INSERT INTO public.battle_enemy_unit VALUES (2, 24);
INSERT INTO public.battle_enemy_unit VALUES (26, 25);
INSERT INTO public.battle_enemy_unit VALUES (14, 26);
INSERT INTO public.battle_enemy_unit VALUES (18, 27);
INSERT INTO public.battle_enemy_unit VALUES (7, 28);
INSERT INTO public.battle_enemy_unit VALUES (26, 29);
INSERT INTO public.battle_enemy_unit VALUES (4, 30);
INSERT INTO public.battle_enemy_unit VALUES (25, 31);
INSERT INTO public.battle_enemy_unit VALUES (5, 32);
INSERT INTO public.battle_enemy_unit VALUES (18, 33);
INSERT INTO public.battle_enemy_unit VALUES (24, 34);
INSERT INTO public.battle_enemy_unit VALUES (4, 35);
INSERT INTO public.battle_enemy_unit VALUES (5, 36);
INSERT INTO public.battle_enemy_unit VALUES (30, 37);
INSERT INTO public.battle_enemy_unit VALUES (12, 38);
INSERT INTO public.battle_enemy_unit VALUES (20, 39);
INSERT INTO public.battle_enemy_unit VALUES (7, 40);
INSERT INTO public.battle_enemy_unit VALUES (3, 51);
INSERT INTO public.battle_enemy_unit VALUES (4, 47);
INSERT INTO public.battle_enemy_unit VALUES (18, 53);
INSERT INTO public.battle_enemy_unit VALUES (24, 54);
INSERT INTO public.battle_enemy_unit VALUES (4, 55);
INSERT INTO public.battle_enemy_unit VALUES (7, 56);
INSERT INTO public.battle_enemy_unit VALUES (20, 57);
INSERT INTO public.battle_enemy_unit VALUES (3, 58);
INSERT INTO public.battle_enemy_unit VALUES (26, 59);
INSERT INTO public.battle_enemy_unit VALUES (4, 60);
INSERT INTO public.battle_enemy_unit VALUES (6, 50);
INSERT INTO public.battle_enemy_unit VALUES (2, 42);
INSERT INTO public.battle_enemy_unit VALUES (3, 43);
INSERT INTO public.battle_enemy_unit VALUES (11, 44);
INSERT INTO public.battle_enemy_unit VALUES (6, 45);
INSERT INTO public.battle_enemy_unit VALUES (5, 46);
INSERT INTO public.battle_enemy_unit VALUES (8, 48);
INSERT INTO public.battle_enemy_unit VALUES (5, 49);
INSERT INTO public.battle_enemy_unit VALUES (26, 41);


--
-- Data for Name: battle_military_unit; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.battle_military_unit VALUES (1, 15);
INSERT INTO public.battle_military_unit VALUES (2, 1);
INSERT INTO public.battle_military_unit VALUES (2, 6);
INSERT INTO public.battle_military_unit VALUES (3, 2);
INSERT INTO public.battle_military_unit VALUES (3, 13);
INSERT INTO public.battle_military_unit VALUES (3, 18);
INSERT INTO public.battle_military_unit VALUES (3, 26);
INSERT INTO public.battle_military_unit VALUES (4, 5);
INSERT INTO public.battle_military_unit VALUES (4, 20);
INSERT INTO public.battle_military_unit VALUES (4, 23);
INSERT INTO public.battle_military_unit VALUES (4, 24);
INSERT INTO public.battle_military_unit VALUES (4, 29);
INSERT INTO public.battle_military_unit VALUES (5, 3);
INSERT INTO public.battle_military_unit VALUES (5, 8);
INSERT INTO public.battle_military_unit VALUES (5, 9);
INSERT INTO public.battle_military_unit VALUES (6, 14);
INSERT INTO public.battle_military_unit VALUES (6, 19);
INSERT INTO public.battle_military_unit VALUES (6, 30);
INSERT INTO public.battle_military_unit VALUES (7, 12);
INSERT INTO public.battle_military_unit VALUES (8, 4);
INSERT INTO public.battle_military_unit VALUES (8, 8);
INSERT INTO public.battle_military_unit VALUES (9, 3);
INSERT INTO public.battle_military_unit VALUES (9, 4);
INSERT INTO public.battle_military_unit VALUES (10, 28);
INSERT INTO public.battle_military_unit VALUES (11, 1);
INSERT INTO public.battle_military_unit VALUES (11, 11);
INSERT INTO public.battle_military_unit VALUES (11, 15);
INSERT INTO public.battle_military_unit VALUES (12, 14);
INSERT INTO public.battle_military_unit VALUES (13, 17);
INSERT INTO public.battle_military_unit VALUES (13, 27);
INSERT INTO public.battle_military_unit VALUES (14, 1);
INSERT INTO public.battle_military_unit VALUES (14, 19);
INSERT INTO public.battle_military_unit VALUES (15, 2);
INSERT INTO public.battle_military_unit VALUES (15, 21);
INSERT INTO public.battle_military_unit VALUES (16, 15);
INSERT INTO public.battle_military_unit VALUES (17, 15);
INSERT INTO public.battle_military_unit VALUES (18, 7);
INSERT INTO public.battle_military_unit VALUES (18, 14);
INSERT INTO public.battle_military_unit VALUES (18, 27);
INSERT INTO public.battle_military_unit VALUES (19, 7);
INSERT INTO public.battle_military_unit VALUES (20, 3);
INSERT INTO public.battle_military_unit VALUES (20, 17);
INSERT INTO public.battle_military_unit VALUES (21, 2);
INSERT INTO public.battle_military_unit VALUES (22, 16);
INSERT INTO public.battle_military_unit VALUES (23, 8);
INSERT INTO public.battle_military_unit VALUES (23, 28);
INSERT INTO public.battle_military_unit VALUES (24, 9);
INSERT INTO public.battle_military_unit VALUES (24, 10);
INSERT INTO public.battle_military_unit VALUES (25, 25);
INSERT INTO public.battle_military_unit VALUES (26, 28);
INSERT INTO public.battle_military_unit VALUES (27, 22);
INSERT INTO public.battle_military_unit VALUES (28, 8);
INSERT INTO public.battle_military_unit VALUES (29, 3);
INSERT INTO public.battle_military_unit VALUES (29, 27);
INSERT INTO public.battle_military_unit VALUES (30, 28);


--
-- Data for Name: enemy_unit; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.enemy_unit VALUES (1, '6-я армия', 'пехотная', 'Фридрих Паулюс', 'Сталинград', '1939-10-10', '1943-02-02');
INSERT INTO public.enemy_unit VALUES (2, 'Танковая группа "Кемпф"', 'танковая', 'Вернер Кемпф', 'Курск', '1943-03-01', '1943-08-20');
INSERT INTO public.enemy_unit VALUES (3, '1-я танковая дивизия СС "Лейбштандарт Адольф Гитлер"', 'СС', 'Теодор Виш', 'Харьков', '1933-11-09', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (4, 'Люфтваффе: эскадра JG52', 'авиационная', 'Герман Граф', 'Кубань', '1941-06-22', NULL);
INSERT INTO public.enemy_unit VALUES (5, '56-й танковый корпус', 'танковая', 'Фердинанд Шааль', 'Ржев', '1941-02-01', '1944-06-22');
INSERT INTO public.enemy_unit VALUES (6, 'Группа армий "Центр"', 'пехотная', 'Гюнтер фон Клюге', 'Смоленск', '1941-06-22', '1945-04-28');
INSERT INTO public.enemy_unit VALUES (7, '502-й тяжёлый танковый батальон', 'танковая', 'Отто Кариус', 'Нарва', '1942-05-01', '1945-05-01');
INSERT INTO public.enemy_unit VALUES (8, 'Дивизия "Великая Германия"', 'пехотная', 'Вальтер Хёрнлайн', 'Курск', '1942-04-12', '1945-04-25');
INSERT INTO public.enemy_unit VALUES (9, '9-я армия', 'пехотная', 'Вальтер Модель', 'Ржев', '1940-05-15', '1945-04-20');
INSERT INTO public.enemy_unit VALUES (10, '5-я танковая дивизия СС "Викинг"', 'СС', 'Герберт Отто Гилле', 'Украина', '1940-12-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (11, 'Эскадра JG54 "Зелёное сердце"', 'авиационная', 'Ханс Траутлофт', 'Ленинград', '1939-02-01', NULL);
INSERT INTO public.enemy_unit VALUES (12, '78-я штурмовая дивизия', 'пехотная', 'Ганс Траут', 'Орёл', '1942-08-01', '1944-07-03');
INSERT INTO public.enemy_unit VALUES (13, '502-й артиллерийский полк', 'артиллерийская', 'Фриц Штрахвиц', 'Демянск', '1941-06-22', '1944-02-28');
INSERT INTO public.enemy_unit VALUES (14, '3-я горнострелковая дивизия', 'пехотная', 'Юлиус Рингель', 'Кавказ', '1938-04-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (15, 'Боевая группа "Пайпер"', 'танковая', 'Йоахим Пайпер', 'Арденны', '1944-12-10', '1945-01-22');
INSERT INTO public.enemy_unit VALUES (16, 'Бранденбург-800', 'СС', 'Теодор фон Хиппель', 'Восточный фронт', '1939-10-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (17, 'Дивизия "Мёртвая голова"', 'СС', 'Теодор Эйке', 'Харьков', '1939-11-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (18, '505-й тяжёлый танковый батальон', 'танковая', 'Эрнст Баркман', 'Курск', '1943-01-01', '1945-04-01');
INSERT INTO public.enemy_unit VALUES (19, '4-я танковая армия', 'танковая', 'Герман Гот', 'Сталинград', '1941-02-01', '1943-02-02');
INSERT INTO public.enemy_unit VALUES (20, '16-я армия', 'пехотная', 'Эрнст Буш', 'Ленинград', '1939-10-01', '1944-06-22');
INSERT INTO public.enemy_unit VALUES (21, '11-я армия', 'пехотная', 'Эрих фон Манштейн', 'Крым', '1940-10-01', '1944-05-12');
INSERT INTO public.enemy_unit VALUES (22, '503-й тяжёлый танковый батальон', 'танковая', 'Клеменс Хетцель', 'Курск', '1942-05-01', '1945-04-16');
INSERT INTO public.enemy_unit VALUES (23, 'Дивизия СС "Дас Райх"', 'СС', 'Вальтер Крюгер', 'Харьков', '1939-10-10', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (24, 'Эскадра JG3 "Удет"', 'авиационная', 'Вальтер Даль', 'Сталинград', '1939-05-01', '1943-02-02');
INSERT INTO public.enemy_unit VALUES (25, '257-я пехотная дивизия', 'пехотная', 'Карл Шаландер', 'Кавказ', '1939-08-01', '1944-11-20');
INSERT INTO public.enemy_unit VALUES (26, 'Группа армий "Юг"', 'пехотная', 'Герд фон Рундштедт', 'Украина', '1941-06-22', '1944-09-01');
INSERT INTO public.enemy_unit VALUES (27, '17-я танковая дивизия', 'танковая', 'Ганс-Юрген фон Арним', 'Смоленск', '1940-11-01', '1944-08-01');
INSERT INTO public.enemy_unit VALUES (28, '22-я пехотная дивизия', 'пехотная', 'Фридрих-Вильгельм Мюллер', 'Крым', '1935-10-01', '1944-05-12');
INSERT INTO public.enemy_unit VALUES (29, '1-я горнострелковая дивизия', 'пехотная', 'Хуберт Ланц', 'Кавказ', '1938-04-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (30, '505-й инженерный батальон', 'СС', 'Вальтер Шимана', 'Курск', '1942-03-01', '1943-08-20');
INSERT INTO public.enemy_unit VALUES (31, 'Боевая группа "Фельдхернхалле"', 'танковая', 'Ульрих Клеман', 'Будапешт', '1944-09-01', '1945-02-11');
INSERT INTO public.enemy_unit VALUES (32, 'Эскадра KG55 "Гриф"', 'авиационная', 'Эрих Хоффман', 'Орёл', '1939-09-01', '1944-07-03');
INSERT INTO public.enemy_unit VALUES (33, '707-я пехотная дивизия', 'пехотная', 'Густав Хёне', 'Белоруссия', '1941-05-01', '1944-06-28');
INSERT INTO public.enemy_unit VALUES (34, 'Дивизия "Гроссдойчланд"', 'танковая', 'Хасо фон Мантойфель', 'Восточная Пруссия', '1942-04-12', '1945-04-25');
INSERT INTO public.enemy_unit VALUES (35, 'Эскадра SG2 "Иммельман"', 'авиационная', 'Ханс-Ульрих Рудель', 'Курск', '1943-01-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (36, '201-я охранная дивизия', 'пехотная', 'Альфред Якоби', 'Белоруссия', '1941-06-22', '1944-07-01');
INSERT INTO public.enemy_unit VALUES (37, 'Боевая группа "Шульц"', 'СС', 'Отто Шульц', 'Курляндия', '1944-10-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (38, '5-я горнострелковая дивизия', 'пехотная', 'Юлиус Рингель', 'Карелия', '1940-11-01', '1944-09-19');
INSERT INTO public.enemy_unit VALUES (39, '8-я танковая дивизия', 'танковая', 'Вернер Фрибе', 'Украина', '1939-10-01', '1944-03-20');
INSERT INTO public.enemy_unit VALUES (40, 'Эскадра KG53 "Легион Кондор"', 'авиационная', 'Герберт Илефельд', 'Крым', '1939-09-01', '1944-05-12');
INSERT INTO public.enemy_unit VALUES (41, '97-я егерская дивизия', 'пехотная', 'Эрих Рёпке', 'Кавказ', '1940-11-01', '1944-09-01');
INSERT INTO public.enemy_unit VALUES (42, '3-я танковая дивизия', 'танковая', 'Фридрих Кюн', 'Москва', '1935-10-01', '1943-03-20');
INSERT INTO public.enemy_unit VALUES (43, 'Эскадра KG76', 'авиационная', 'Вольфганг Швайкхард', 'Сталинград', '1939-09-01', '1943-02-02');
INSERT INTO public.enemy_unit VALUES (44, '299-я пехотная дивизия', 'пехотная', 'Йозеф Харпе', 'Ржев', '1940-02-01', '1944-06-28');
INSERT INTO public.enemy_unit VALUES (45, 'Дивизия СС "Нордланд"', 'СС', 'Фриц фон Шольц', 'Ленинград', '1943-03-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (46, '501-й тяжёлый танковый батальон', 'танковая', 'Эрих Лёве', 'Варшава', '1942-05-01', '1945-01-17');
INSERT INTO public.enemy_unit VALUES (47, '12-я танковая дивизия', 'танковая', 'Йозеф Харпе', 'Курск', '1940-10-01', '1944-08-20');
INSERT INTO public.enemy_unit VALUES (48, 'Эскадра JG51 "Мёльдерс"', 'авиационная', 'Вернер Мёльдерс', 'Смоленск', '1939-11-01', '1944-07-03');
INSERT INTO public.enemy_unit VALUES (49, '205-я пехотная дивизия', 'пехотная', 'Эрнст Хааке', 'Белоруссия', '1939-08-01', '1944-06-22');
INSERT INTO public.enemy_unit VALUES (50, 'Группа армий "Север"', 'пехотная', 'Вильгельм фон Лееб', 'Ленинград', '1941-06-22', '1944-01-01');
INSERT INTO public.enemy_unit VALUES (51, '10-я танковая дивизия', 'танковая', 'Фердинанд Шааль', 'Сталинград', '1939-04-01', '1943-02-02');
INSERT INTO public.enemy_unit VALUES (52, 'Эскадра KG4 "Генерал Вефер"', 'авиационная', 'Ганс-Йоахим Райнеке', 'Орёл', '1939-05-01', '1944-07-01');
INSERT INTO public.enemy_unit VALUES (53, '252-я пехотная дивизия', 'пехотная', 'Пауль Дрекман', 'Ржев', '1939-08-01', '1944-06-28');
INSERT INTO public.enemy_unit VALUES (54, 'Боевая группа "Штайнер"', 'танковая', 'Феликс Штайнер', 'Курляндия', '1944-10-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (55, 'Эскадра KG27 "Бёльке"', 'авиационная', 'Генрих фон Риттер', 'Курск', '1939-09-01', '1944-04-01');
INSERT INTO public.enemy_unit VALUES (56, '131-я пехотная дивизия', 'пехотная', 'Фридрих-Вильгельм Хёнике', 'Крым', '1940-10-01', '1944-05-12');
INSERT INTO public.enemy_unit VALUES (57, 'Дивизия СС "Флориан Гайер"', 'СС', 'Йоахим Райпе', 'Украина', '1943-06-01', '1945-04-20');
INSERT INTO public.enemy_unit VALUES (58, '23-я танковая дивизия', 'танковая', 'Ханс фон Бойнебург-Ленгсфельд', 'Сталинград', '1941-09-01', '1943-02-02');
INSERT INTO public.enemy_unit VALUES (59, 'Эскадра JG77 "Герц Ас"', 'авиационная', 'Йоханнес Штейнхофф', 'Кубань', '1939-05-01', '1945-05-08');
INSERT INTO public.enemy_unit VALUES (60, '337-я пехотная дивизия', 'пехотная', 'Карл Бек-Беренс', 'Курск', '1941-12-01', '1944-08-20');


--
-- Data for Name: equipment; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.equipment VALUES (1, 1, 'оружие', 'Винтовка Мосина', 1200, '1942-03-01');
INSERT INTO public.equipment VALUES (2, 1, 'боеприпасы', 'Патроны 7.62 мм', 50000, '1942-03-05');
INSERT INTO public.equipment VALUES (3, 2, 'медицина', 'Аптечки полевые', 350, '1943-01-10');
INSERT INTO public.equipment VALUES (4, 2, 'артиллерия', '76-мм дивизионная пушка ЗИС-3', 24, '1942-11-10');
INSERT INTO public.equipment VALUES (5, 3, 'танки', 'Т-34', 58, '1943-07-05');
INSERT INTO public.equipment VALUES (6, 4, 'миномёты', 'БМ-13 "Катюша"', 12, '1944-01-15');
INSERT INTO public.equipment VALUES (7, 5, 'самолёты', 'Ил-2', 45, '1943-05-01');
INSERT INTO public.equipment VALUES (8, 6, 'реактивные снаряды', 'М-31', 1500, '1942-12-01');
INSERT INTO public.equipment VALUES (9, 7, 'инженерное', 'Сапёрная лопатка', 850, '1943-08-14');
INSERT INTO public.equipment VALUES (10, 8, 'танки', 'ИС-2', 42, '1944-10-01');
INSERT INTO public.equipment VALUES (11, 9, 'авиабомбы', 'ФАБ-100', 3200, '1943-09-05');
INSERT INTO public.equipment VALUES (12, 10, 'противотанковые', 'ПТРД', 68, '1944-02-28');
INSERT INTO public.equipment VALUES (13, 1, 'связь', 'Радиостанция РБМ', 15, '1942-05-10');
INSERT INTO public.equipment VALUES (14, 2, 'медицина', 'Плазменные флаконы', 480, '1943-12-01');
INSERT INTO public.equipment VALUES (15, 2, 'боеприпасы', 'Патроны 7.62 мм', 50000, '1942-03-05');
INSERT INTO public.equipment VALUES (16, 13, 'боеприпасы', 'Патроны 7.62 мм', 30000, '1942-03-05');
INSERT INTO public.equipment VALUES (17, 18, 'боеприпасы', 'Патроны 7.62 мм', 40000, '1942-03-05');
INSERT INTO public.equipment VALUES (18, 21, 'боеприпасы', 'Патроны 7.62 мм', 50000, '1942-03-05');
INSERT INTO public.equipment VALUES (19, 26, 'боеприпасы', 'Патроны 7.62 мм', 70000, '1942-03-05');
INSERT INTO public.equipment VALUES (20, 6, 'боеприпасы', 'Патроны 7.62 мм', 20000, '1942-12-01');
INSERT INTO public.equipment VALUES (21, 13, 'медицина', 'Аптечки полевые', 250, '1942-03-05');
INSERT INTO public.equipment VALUES (22, 12, 'миномёты', '82-мм', 930, '1942-03-05');
INSERT INTO public.equipment VALUES (23, 12, 'миномёты', '50-мм', 1326, '1942-06-06');
INSERT INTO public.equipment VALUES (24, 12, 'медицина', 'Аптечки полевые', 250, '1942-03-05');


--
-- Data for Name: equipment_assignment; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.equipment_assignment VALUES (1, 1, 1, '1942-03-02', 1);
INSERT INTO public.equipment_assignment VALUES (2, 1, 2, '1942-03-02', 120);
INSERT INTO public.equipment_assignment VALUES (3, 2, 3, '1943-01-12', 5);
INSERT INTO public.equipment_assignment VALUES (4, 4, 5, '1943-07-10', 1);
INSERT INTO public.equipment_assignment VALUES (5, 7, 4, '1942-11-15', 1);
INSERT INTO public.equipment_assignment VALUES (6, 8, 6, '1944-01-20', 120);
INSERT INTO public.equipment_assignment VALUES (7, 6, 7, '1943-05-05', 1);
INSERT INTO public.equipment_assignment VALUES (8, 9, 9, '1943-08-15', 1);
INSERT INTO public.equipment_assignment VALUES (9, 10, 10, '1944-10-02', 1);
INSERT INTO public.equipment_assignment VALUES (10, 11, 11, '1943-09-06', 24);
INSERT INTO public.equipment_assignment VALUES (11, 12, 12, '1944-03-01', 1);
INSERT INTO public.equipment_assignment VALUES (12, 13, 13, '1942-05-12', 1);
INSERT INTO public.equipment_assignment VALUES (13, 15, 14, '1943-12-05', 3);


--
-- Data for Name: equipment_audit; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: medal; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.medal VALUES (1, 'Герой Советского Союза', '1934-04-16', 'За личные или коллективные заслуги перед государством');
INSERT INTO public.medal VALUES (2, 'Орден Красной Звезды', '1930-04-06', 'За большие заслуги в обороне СССР');
INSERT INTO public.medal VALUES (3, 'Медаль "За отвагу"', '1938-10-17', 'За личное мужество в бою');
INSERT INTO public.medal VALUES (4, 'Орден Отечественной войны', '1942-05-20', 'За храбрость в бою');
INSERT INTO public.medal VALUES (5, 'Медаль "За оборону Москвы"', '1944-05-01', 'Участникам обороны Москвы');
INSERT INTO public.medal VALUES (6, 'Медаль "За оборону Сталинграда"', '1942-12-22', 'Защитникам Сталинграда');
INSERT INTO public.medal VALUES (7, 'Орден Славы', '1943-11-08', 'За личный подвиг');
INSERT INTO public.medal VALUES (8, 'Медаль "Партизану Отечественной войны"', '1943-02-02', 'Партизанам и подпольщикам');
INSERT INTO public.medal VALUES (9, 'Орден Ушакова', '1944-03-03', 'За морские операции');
INSERT INTO public.medal VALUES (10, 'Медаль "За взятие Берлина"', '1945-06-09', 'Участникам штурма Берлина');


--
-- Data for Name: military_service; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.military_service VALUES (1, 1, 1, '1941-08-05', NULL);
INSERT INTO public.military_service VALUES (2, 2, 2, '1942-02-01', '1943-01-15');
INSERT INTO public.military_service VALUES (3, 3, 2, '1941-10-15', '1942-11-20');
INSERT INTO public.military_service VALUES (4, 4, 3, '1941-09-15', '1944-04-20');
INSERT INTO public.military_service VALUES (5, 5, 1, '1943-09-01', '1945-05-09');
INSERT INTO public.military_service VALUES (6, 6, 5, '1941-06-25', NULL);
INSERT INTO public.military_service VALUES (7, 7, 2, '1942-09-05', '1943-02-02');
INSERT INTO public.military_service VALUES (8, 8, 4, '1943-02-01', '1945-04-30');
INSERT INTO public.military_service VALUES (9, 9, 7, '1942-04-01', '1945-05-01');
INSERT INTO public.military_service VALUES (10, 10, 8, '1943-07-05', NULL);
INSERT INTO public.military_service VALUES (11, 11, 9, '1944-09-01', '1945-03-15');
INSERT INTO public.military_service VALUES (12, 12, 10, '1943-11-10', '1944-06-22');
INSERT INTO public.military_service VALUES (13, 13, 3, '1941-10-05', '1944-12-01');
INSERT INTO public.military_service VALUES (14, 14, 4, '1944-05-01', '1944-05-09');
INSERT INTO public.military_service VALUES (15, 15, 5, '1942-06-20', '1945-04-30');
INSERT INTO public.military_service VALUES (16, 16, 11, '1942-08-05', '1943-03-15');
INSERT INTO public.military_service VALUES (17, 17, 12, '1943-09-20', '1944-05-09');
INSERT INTO public.military_service VALUES (18, 18, 13, '1944-03-01', '1944-12-01');
INSERT INTO public.military_service VALUES (19, 19, 14, '1941-12-10', '1942-04-20');
INSERT INTO public.military_service VALUES (20, 20, 15, '1942-11-15', '1945-05-10');
INSERT INTO public.military_service VALUES (21, 21, 16, '1943-02-15', '1944-11-30');
INSERT INTO public.military_service VALUES (22, 22, 17, '1942-10-01', '1943-02-02');
INSERT INTO public.military_service VALUES (23, 23, 18, '1942-01-01', '1944-08-20');
INSERT INTO public.military_service VALUES (24, 24, 19, '1943-08-01', '1944-06-06');
INSERT INTO public.military_service VALUES (25, 25, 20, '1944-02-01', '1945-05-09');
INSERT INTO public.military_service VALUES (26, 26, 21, '1941-09-25', '1943-11-12');
INSERT INTO public.military_service VALUES (27, 27, 22, '1943-04-20', '1945-05-09');
INSERT INTO public.military_service VALUES (28, 28, 23, '1944-08-10', '1945-02-28');
INSERT INTO public.military_service VALUES (29, 29, 24, '1942-11-15', '1943-07-22');
INSERT INTO public.military_service VALUES (30, 30, 25, '1941-07-05', '1944-12-01');
INSERT INTO public.military_service VALUES (31, 31, 26, '1941-08-20', '1943-02-02');
INSERT INTO public.military_service VALUES (32, 32, 27, '1943-02-01', '1944-01-15');
INSERT INTO public.military_service VALUES (33, 33, 28, '1942-05-15', '1945-05-09');
INSERT INTO public.military_service VALUES (34, 34, 29, '1942-07-15', '1944-06-06');
INSERT INTO public.military_service VALUES (35, 35, 30, '1943-02-10', '1945-04-30');
INSERT INTO public.military_service VALUES (36, 36, 26, '1941-10-20', '1943-11-20');
INSERT INTO public.military_service VALUES (37, 37, 27, '1942-05-25', '1943-07-18');
INSERT INTO public.military_service VALUES (38, 38, 28, '1943-03-05', '1945-02-01');
INSERT INTO public.military_service VALUES (39, 39, 29, '1944-06-15', '1945-03-22');
INSERT INTO public.military_service VALUES (40, 40, 30, '1942-09-10', '1944-12-10');


--
-- Data for Name: military_unit; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.military_unit VALUES (1, '316-я стрелковая дивизия', 'пехота', 'Москва', '1941-07-15', 85.5);
INSERT INTO public.military_unit VALUES (2, '62-я армия', 'общевойсковая', 'Сталинград', '1942-05-01', 92.3);
INSERT INTO public.military_unit VALUES (3, '1-я гвардейская танковая армия', 'танковые войска', 'Курск', '1943-01-20', 95.0);
INSERT INTO public.military_unit VALUES (4, '150-я стрелковая дивизия', 'пехота', 'Берлин', '1943-03-12', 97.8);
INSERT INTO public.military_unit VALUES (5, '16-я воздушная армия', 'авиация', 'Курск', '1942-08-01', 88.9);
INSERT INTO public.military_unit VALUES (6, '7-я гвардейская миномётная дивизия', 'реактивная артиллерия', 'Москва', '1941-10-05', 90.5);
INSERT INTO public.military_unit VALUES (7, '2-я ударная армия', 'общевойсковая', 'Ленинград', '1941-09-01', 75.2);
INSERT INTO public.military_unit VALUES (8, '8-я гвардейская армия', 'танковые войска', 'Берлин', '1943-04-12', 98.5);
INSERT INTO public.military_unit VALUES (9, '3-я воздушная армия', 'авиация', 'Орёл', '1942-07-20', 85.0);
INSERT INTO public.military_unit VALUES (10, '106-я стрелковая дивизия', 'пехота', 'Кёнигсберг', '1944-01-10', 89.3);
INSERT INTO public.military_unit VALUES (11, '14-я отдельная штрафная рота', 'пехота', 'Ржев', '1942-08-01', 65.8);
INSERT INTO public.military_unit VALUES (12, '1-я морская бригада', 'морская пехота', 'Севастополь', '1941-10-10', 82.4);
INSERT INTO public.military_unit VALUES (13, 'Отдельная медико-санитарная рота', 'медицинская', 'Сталинград', '1942-09-01', 91.7);
INSERT INTO public.military_unit VALUES (14, '88-й отдельный лыжный батальон', 'лыжные войска', 'Ленинград', '1941-12-01', 73.9);
INSERT INTO public.military_unit VALUES (15, '101-й полк НКВД', 'спецназ', 'Москва', '1941-06-25', 96.2);
INSERT INTO public.military_unit VALUES (16, '369-й отдельный батальон морской пехоты', 'морская пехота', 'Керчь', '1943-04-15', 88.9);
INSERT INTO public.military_unit VALUES (17, '1-й чехословацкий отдельный батальон', 'пехота', 'Харьков', '1942-01-30', 78.5);
INSERT INTO public.military_unit VALUES (18, '585-й женский авиаполк', 'авиация', 'Сталинград', '1942-05-20', 94.1);
INSERT INTO public.military_unit VALUES (19, '28-я дивизия народного ополчения', 'пехота', 'Ленинград', '1941-07-10', 69.8);
INSERT INTO public.military_unit VALUES (20, 'Отдельный отряд собак-истребителей танков', 'спецназ', 'Курск', '1943-06-01', 82.4);
INSERT INTO public.military_unit VALUES (21, '37-й гвардейский миномётный полк', 'реактивная артиллерия', 'Сталинград', '1942-09-01', 96.5);
INSERT INTO public.military_unit VALUES (22, 'Отдельный батальон связи №45', 'связисты', 'Москва', '1941-10-15', 85.2);
INSERT INTO public.military_unit VALUES (23, '225-й отдельный инженерный батальон', 'инженерные войска', 'Курск', '1943-05-10', 89.7);
INSERT INTO public.military_unit VALUES (24, '18-я дивизия СС "Хорст Вессель"', 'противник', 'Берлин', '1939-04-20', 88.1);
INSERT INTO public.military_unit VALUES (25, '101-й учебный полк', 'резерв', 'Новосибирск', '1942-02-01', 68.3);
INSERT INTO public.military_unit VALUES (26, '64-я стрелковая дивизия', 'пехота', 'Сталинград', '1942-07-01', 92.4);
INSERT INTO public.military_unit VALUES (27, '1-й отдельный чехословацкий батальон', 'пехота', 'Харьков', '1942-02-15', 85.0);
INSERT INTO public.military_unit VALUES (28, '46-й гвардейский ночной бомбардировочный полк', 'авиация', 'Краснодар', '1942-05-10', 96.7);
INSERT INTO public.military_unit VALUES (29, '101-й инженерно-сапёрный батальон', 'инженерные войска', 'Курск', '1943-04-20', 89.5);
INSERT INTO public.military_unit VALUES (30, 'Отдельный отряд собак-миноискателей', 'спецназ', 'Ленинград', '1943-08-01', 81.3);


--
-- Data for Name: schema_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.schema_migrations VALUES (1, '001_equipment_audit.sql', '2026-10-13 07:17:08.016423+00');


--
-- Data for Name: soldier; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.soldier VALUES (1, 'Иванов Алексей Петрович', 1923, 'мужской', 'рядовой', 'пехота', 'Москва', 'жив', '1941-08-01');
INSERT INTO public.soldier VALUES (2, 'Смирнова Анна Васильевна', 1925, 'женский', 'медсестра', 'медицинская служба', 'Ленинград', 'ранен', '1942-01-15');
INSERT INTO public.soldier VALUES (3, 'Петров Дмитрий Иванович', 1918, 'мужской', 'сержант', 'артиллерия', 'Сталинград', 'убит', '1941-10-10');
INSERT INTO public.soldier VALUES (4, 'Козлов Николай Семёнович', 1920, 'мужской', 'лейтенант', 'танковые войска', 'Харьков', 'убит', '1941-09-10');
INSERT INTO public.soldier VALUES (5, 'Фёдорова Мария Ивановна', 1922, 'женский', 'санитар', 'медицинская служба', 'Киев', 'пропал без вести', '1943-08-20');
INSERT INTO public.soldier VALUES (6, 'Жуков Андрей Григорьевич', 1915, 'мужской', 'капитан', 'авиация', 'Минск', 'жив', '1941-06-22');
INSERT INTO public.soldier VALUES (7, 'Павлов Яков Фёдорович', 1917, 'мужской', 'сержант', 'пехота', 'Волгоград', 'жив', '1942-09-01');
INSERT INTO public.soldier VALUES (8, 'Зайцева Людмила Михайловна', 1924, 'женский', 'снайпер', 'пехота', 'Ленинград', 'ранен', '1943-01-15');
INSERT INTO public.soldier VALUES (9, 'Громов Михаил Сергеевич', 1919, 'мужской', 'старшина', 'инженерные войска', 'Свердловск', 'жив', '1942-03-12');
INSERT INTO public.soldier VALUES (10, 'Орлова Вера Павловна', 1921, 'женский', 'радист', 'связисты', 'Одесса', 'ранен', '1943-07-01');
INSERT INTO public.soldier VALUES (11, 'Новиков Александр Иванович', 1924, 'мужской', 'ефрейтор', 'кавалерия', 'Ростов-на-Дону', 'убит', '1944-08-20');
INSERT INTO public.soldier VALUES (12, 'Васнецова Татьяна Дмитриевна', 1923, 'женский', 'разведчик', 'разведка', 'Смоленск', 'пропал без вести', '1943-11-02');
INSERT INTO public.soldier VALUES (13, 'Кузнецов Пётр Васильевич', 1916, 'мужской', 'майор', 'НКВД', 'Мурманск', 'жив', '1941-10-01');
INSERT INTO public.soldier VALUES (14, 'Белов Алексей Николаевич', 1925, 'мужской', 'рядовой', 'морская пехота', 'Севастополь', 'убит', '1944-05-09');
INSERT INTO public.soldier VALUES (15, 'Соколова Ольга Ивановна', 1920, 'женский', 'хирург', 'медицинская служба', 'Киев', 'жив', '1942-06-15');
INSERT INTO public.soldier VALUES (16, 'Морозов Иван Кузьмич', 1914, 'мужской', 'полковник', 'артиллерия', 'Тула', 'жив', '1941-07-01');
INSERT INTO public.soldier VALUES (17, 'Волкова Елена Сергеевна', 1926, 'женский', 'зенитчик', 'ПВО', 'Горький', 'ранен', '1943-09-15');
INSERT INTO public.soldier VALUES (18, 'Ткаченко Григорий Петрович', 1927, 'мужской', 'рядовой', 'пехота', 'Киев', 'убит', '1944-02-20');
INSERT INTO public.soldier VALUES (19, 'Беляев Павел Дмитриевич', 1912, 'мужской', 'подполковник', 'кавалерия', 'Самара', 'жив', '1941-08-30');
INSERT INTO public.soldier VALUES (20, 'Семёнова Валентина Михайловна', 1920, 'женский', 'связист', 'связисты', 'Омск', 'пропал без вести', '1942-11-11');
INSERT INTO public.soldier VALUES (21, 'Ковалёв Сергей Николаевич', 1925, 'мужской', 'лейтенант', 'танковые войска', 'Челябинск', 'жив', '1943-02-01');
INSERT INTO public.soldier VALUES (22, 'Мельникова Галина Ивановна', 1924, 'женский', 'снайпер', 'пехота', 'Сталинград', 'ранен', '1942-09-15');
INSERT INTO public.soldier VALUES (23, 'Фёдоров Игорь Васильевич', 1913, 'мужской', 'полковник', 'авиация', 'Казань', 'убит', '1941-12-05');
INSERT INTO public.soldier VALUES (24, 'Горбачёв Алексей Дмитриевич', 1926, 'мужской', 'рядовой', 'пехота', 'Воронеж', 'пропал без вести', '1943-07-22');
INSERT INTO public.soldier VALUES (25, 'Сидорова Екатерина Петровна', 1921, 'женский', 'радист', 'связисты', 'Минск', 'жив', '1944-01-10');
INSERT INTO public.soldier VALUES (26, 'Смирнов Василий Иванович', 1911, 'мужской', 'генерал-майор', 'артиллерия', 'Киев', 'убит', '1941-09-20');
INSERT INTO public.soldier VALUES (27, 'Крылова Надежда Фёдоровна', 1925, 'женский', 'санитар', 'медицинская служба', 'Одесса', 'жив', '1943-04-12');
INSERT INTO public.soldier VALUES (28, 'Орлов Денис Сергеевич', 1927, 'мужской', 'рядовой', 'пехота', 'Брянск', 'пропал без вести', '1944-08-03');
INSERT INTO public.soldier VALUES (29, 'Жукова Елена Викторовна', 1923, 'женский', 'радист', 'связисты', 'Смоленск', 'ранен', '1942-11-07');
INSERT INTO public.soldier VALUES (30, 'Гришин Алексей Петрович', 1918, 'мужской', 'капитан', 'инженерные войска', 'Харьков', 'жив', '1941-07-01');
INSERT INTO public.soldier VALUES (31, 'Ткаченко Иван Григорьевич', 1920, 'мужской', 'старший сержант', 'танковые войска', 'Харьков', 'жив', '1941-08-15');
INSERT INTO public.soldier VALUES (32, 'Воронцова Лидия Павловна', 1924, 'женский', 'снайпер', 'пехота', 'Ленинград', 'убит', '1943-01-20');
INSERT INTO public.soldier VALUES (33, 'Жуковский Виктор Михайлович', 1915, 'мужской', 'полковник', 'артиллерия', 'Киев', 'пропал без вести', '1941-09-01');
INSERT INTO public.soldier VALUES (34, 'Морозова Анна Сергеевна', 1922, 'женский', 'радист', 'связисты', 'Одесса', 'ранен', '1942-07-10');
INSERT INTO public.soldier VALUES (35, 'Кузнецов Артём Игоревич', 1926, 'мужской', 'рядовой', 'пехота', 'Сталинград', 'жив', '1943-02-01');
INSERT INTO public.soldier VALUES (36, 'Соколовская Надежда Викторовна', 1923, 'женский', 'хирург', 'медицинская служба', 'Москва', 'жив', '1941-10-15');
INSERT INTO public.soldier VALUES (37, 'Белов Дмитрий Николаевич', 1917, 'мужской', 'капитан', 'инженерные войска', 'Новосибирск', 'убит', '1942-05-20');
INSERT INTO public.soldier VALUES (38, 'Громова Екатерина Ивановна', 1925, 'женский', 'зенитчик', 'ПВО', 'Горький', 'жив', '1943-03-01');
INSERT INTO public.soldier VALUES (39, 'Фролов Павел Сергеевич', 1928, 'мужской', 'рядовой', 'морская пехота', 'Севастополь', 'пропал без вести', '1944-06-10');
INSERT INTO public.soldier VALUES (40, 'Ковалёва Ольга Дмитриевна', 1921, 'женский', 'разведчик', 'разведка', 'Смоленск', 'ранен', '1942-09-05');


--
-- Data for Name: soldier_medal; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.soldier_medal VALUES (7, 1, '1943-02-05');
INSERT INTO public.soldier_medal VALUES (8, 3, '1943-05-20');
INSERT INTO public.soldier_medal VALUES (6, 2, '1942-11-07');
INSERT INTO public.soldier_medal VALUES (9, 4, '1943-09-01');
INSERT INTO public.soldier_medal VALUES (10, 7, '1944-02-15');
INSERT INTO public.soldier_medal VALUES (11, 2, '1944-09-05');
INSERT INTO public.soldier_medal VALUES (12, 8, '1944-07-20');
INSERT INTO public.soldier_medal VALUES (13, 1, '1945-01-10');
INSERT INTO public.soldier_medal VALUES (14, 6, '1943-02-02');
INSERT INTO public.soldier_medal VALUES (15, 5, '1944-05-05');
INSERT INTO public.soldier_medal VALUES (1, 3, '1942-08-14');
INSERT INTO public.soldier_medal VALUES (2, 4, '1943-03-22');
INSERT INTO public.soldier_medal VALUES (3, 10, '1945-06-12');


--
-- Name: equipment_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.equipment_audit_id_seq', 1, false);


--
-- Name: schema_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.schema_migrations_id_seq', 1, true);


--
-- Name: battle_enemy_unit battle_enemy_unit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battle_enemy_unit
    ADD CONSTRAINT battle_enemy_unit_pkey PRIMARY KEY (battle_id, enemy_unit_id);


--
-- Name: battle_military_unit battle_military_unit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battle_military_unit
    ADD CONSTRAINT battle_military_unit_pkey PRIMARY KEY (battle_id, unit_id);


--
-- Name: battle battle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battle
    ADD CONSTRAINT battle_pkey PRIMARY KEY (id);


--
-- Name: enemy_unit enemy_unit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enemy_unit
    ADD CONSTRAINT enemy_unit_pkey PRIMARY KEY (id);


--
-- Name: equipment_assignment equipment_assignment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_assignment
    ADD CONSTRAINT equipment_assignment_pkey PRIMARY KEY (id);


--
-- Name: equipment_audit equipment_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_audit
    ADD CONSTRAINT equipment_audit_pkey PRIMARY KEY (id);


--
-- Name: equipment equipment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT equipment_pkey PRIMARY KEY (id);


--
-- Name: medal medal_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medal
    ADD CONSTRAINT medal_pkey PRIMARY KEY (id);


--
-- Name: military_service military_service_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.military_service
    ADD CONSTRAINT military_service_pkey PRIMARY KEY (id);


--
-- Name: military_unit military_unit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.military_unit
    ADD CONSTRAINT military_unit_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_version_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_version_key UNIQUE (version);


--
-- Name: soldier_medal soldier_medal_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.soldier_medal
    ADD CONSTRAINT soldier_medal_pkey PRIMARY KEY (soldier_id, medal_id);


--
-- Name: soldier soldier_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.soldier
    ADD CONSTRAINT soldier_pkey PRIMARY KEY (id);


--
-- Name: idx_battle_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_battle_date ON public.battle USING btree (start_date, end_date);


--
-- Name: idx_destruction_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_destruction_date ON public.enemy_unit USING btree (destruction_date);


--
-- Name: idx_enemy_commanders; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_enemy_commanders ON public.enemy_unit USING hash (commander);


--
-- Name: idx_enemy_location; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_enemy_location ON public.enemy_unit USING btree (location);


--
-- Name: idx_enemy_unit_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_enemy_unit_type ON public.enemy_unit USING btree (unit_type);


--
-- Name: idx_soldier_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_soldier_name ON public.soldier USING btree (full_name);


--
-- Name: battle_enemy_unit battle_enemy_unit_battle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battle_enemy_unit
    ADD CONSTRAINT battle_enemy_unit_battle_id_fkey FOREIGN KEY (battle_id) REFERENCES public.battle(id);


--
-- Name: battle_enemy_unit battle_enemy_unit_enemy_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battle_enemy_unit
    ADD CONSTRAINT battle_enemy_unit_enemy_unit_id_fkey FOREIGN KEY (enemy_unit_id) REFERENCES public.enemy_unit(id);


--
-- Name: battle_military_unit battle_military_unit_battle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battle_military_unit
    ADD CONSTRAINT battle_military_unit_battle_id_fkey FOREIGN KEY (battle_id) REFERENCES public.battle(id) ON DELETE CASCADE;


--
-- Name: battle_military_unit battle_military_unit_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.battle_military_unit
    ADD CONSTRAINT battle_military_unit_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.military_unit(id) ON DELETE CASCADE;


--
-- Name: equipment_assignment equipment_assignment_equipment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_assignment
    ADD CONSTRAINT equipment_assignment_equipment_id_fkey FOREIGN KEY (equipment_id) REFERENCES public.equipment(id);


--
-- Name: equipment_assignment equipment_assignment_soldier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_assignment
    ADD CONSTRAINT equipment_assignment_soldier_id_fkey FOREIGN KEY (soldier_id) REFERENCES public.soldier(id);


--
-- Name: equipment equipment_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT equipment_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.military_unit(id);


--
-- Name: military_service military_service_soldier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.military_service
    ADD CONSTRAINT military_service_soldier_id_fkey FOREIGN KEY (soldier_id) REFERENCES public.soldier(id);


--
-- Name: military_service military_service_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.military_service
    ADD CONSTRAINT military_service_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.military_unit(id);


--
-- Name: soldier_medal soldier_medal_medal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.soldier_medal
    ADD CONSTRAINT soldier_medal_medal_id_fkey FOREIGN KEY (medal_id) REFERENCES public.medal(id);


--
-- Name: soldier_medal soldier_medal_soldier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.soldier_medal
    ADD CONSTRAINT soldier_medal_soldier_id_fkey FOREIGN KEY (soldier_id) REFERENCES public.soldier(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO sql_runner;


--
-- Name: TABLE battle; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.battle TO sql_runner;


--
-- Name: TABLE battle_enemy_unit; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.battle_enemy_unit TO sql_runner;


--
-- Name: TABLE battle_military_unit; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.battle_military_unit TO sql_runner;


--
-- Name: TABLE enemy_unit; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.enemy_unit TO sql_runner;


--
-- Name: TABLE equipment; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.equipment TO sql_runner;


--
-- Name: TABLE equipment_assignment; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.equipment_assignment TO sql_runner;


--
-- Name: TABLE equipment_audit; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.equipment_audit TO sql_runner;


--
-- Name: SEQUENCE equipment_audit_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.equipment_audit_id_seq TO sql_runner;


--
-- Name: TABLE medal; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.medal TO sql_runner;


--
-- Name: TABLE military_service; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.military_service TO sql_runner;


--
-- Name: TABLE military_unit; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.military_unit TO sql_runner;


--
-- Name: TABLE schema_migrations; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.schema_migrations TO sql_runner;


--
-- Name: SEQUENCE schema_migrations_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.schema_migrations_id_seq TO sql_runner;


--
-- Name: TABLE soldier; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.soldier TO sql_runner;


--
-- Name: TABLE soldier_medal; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.soldier_medal TO sql_runner;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES  TO sql_runner;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES  TO sql_runner;


--
-- PostgreSQL database dump complete
--

