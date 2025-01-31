-- Table: users

DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users
(
    username character varying(50) COLLATE pg_catalog."default" NOT NULL,
    email character varying(50) COLLATE pg_catalog."default" NOT NULL,
    password character varying(100) COLLATE pg_catalog."default" NOT NULL,
    profile_create_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id integer NOT NULL DEFAULT nextval('users_user_id_seq'::regclass),
    is_verified boolean DEFAULT false,
    verification_token character varying(255) COLLATE pg_catalog."default",
    verification_token_expires timestamp without time zone,
    CONSTRAINT users_pkey PRIMARY KEY (user_id),
    CONSTRAINT email_unique UNIQUE (email)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS users
    OWNER to postgres;

-- Table: reserved_tables

DROP TABLE IF EXISTS reserved_tables;

CREATE TABLE IF NOT EXISTS reserved_tables
(
    reservation_id bigint NOT NULL DEFAULT nextval('reserved_tables_reservation_id_seq'::regclass),
    user_id integer NOT NULL,
    table_id smallint NOT NULL,
    username character varying(50) COLLATE pg_catalog."default" NOT NULL,
    email character varying(50) COLLATE pg_catalog."default" NOT NULL,
    date date NOT NULL,
    "time" time(5) without time zone NOT NULL,
    people_count smallint NOT NULL,
    reservation_time timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_reservation_id PRIMARY KEY (reservation_id),
    CONSTRAINT fk_user_id FOREIGN KEY (user_id)
        REFERENCES users (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS reserved_tables
    OWNER to postgres;

-- Table: session

DROP TABLE IF EXISTS session;

CREATE TABLE IF NOT EXISTS session
(
    sid character varying COLLATE pg_catalog."default" NOT NULL,
    sess json NOT NULL,
    expire timestamp(6) without time zone NOT NULL,
    CONSTRAINT session_pkey PRIMARY KEY (sid)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS session
    OWNER to postgres;

-- Index: IDX_session_expire

DROP INDEX IF EXISTS "IDX_session_expire";

CREATE INDEX IF NOT EXISTS "IDX_session_expire"
    ON session USING btree
    (expire ASC NULLS LAST)
    TABLESPACE pg_default;