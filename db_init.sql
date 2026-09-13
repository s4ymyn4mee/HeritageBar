
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE IF NOT EXISTS users
(
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    profile_create_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(255),
    verification_token_expires TIMESTAMP WITHOUT TIME ZONE
);

DROP TABLE IF EXISTS reserved_tables CASCADE;

CREATE TABLE IF NOT EXISTS reserved_tables
(
    reservation_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    table_id SMALLINT NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    "time" TIME(5) WITHOUT TIME ZONE NOT NULL,
    people_count SMALLINT NOT NULL,
    reservation_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id)
        REFERENCES users (user_id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);

DROP TABLE IF EXISTS session CASCADE;

CREATE TABLE IF NOT EXISTS session
(
    sid VARCHAR NOT NULL,
    sess JSON NOT NULL,
    expire TIMESTAMP(6) WITHOUT TIME ZONE NOT NULL,
    CONSTRAINT session_pkey PRIMARY KEY (sid)
);

DROP INDEX IF EXISTS "IDX_session_expire";

CREATE INDEX IF NOT EXISTS "IDX_session_expire"
    ON session USING btree (expire ASC NULLS LAST);

INSERT INTO users (username, email, password, is_verified)
VALUES 
  ('testuser', 'test@example.com', '$2b$10$VDGHZr0kI6u87Ijmq94i5O4O4/K7wraBd8YvJqPjfqp1QWXWQrJUm', true),
  ('testuser', 'laffpie@mail.ru', '$2b$10$6DmaLAISgQk/Qn7xPH6Kkus7R1LopLKv87IcUsfI660TnkkOT6xGm', true)
ON CONFLICT (email) DO NOTHING;