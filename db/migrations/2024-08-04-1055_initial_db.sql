CREATE EXTENSION "pgcrypto";

CREATE TABLE IF NOT EXISTS person(
    id BIGSERIAL PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL,
    height_cm smallint NOT NULL
);

CREATE TABLE IF NOT EXISTS scan(
    id BIGSERIAL PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL,
    person_id BIGINT NOT NULL,
    result JSONB,
    CONSTRAINT fk_person_id
        FOREIGN KEY(person_id)
        REFERENCES person(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TYPE STATUS AS ENUM ('new', 'done');

CREATE TABLE IF NOT EXISTS image(
    id BIGSERIAL PRIMARY KEY,
    uuid UUID NOT NULL,
    scan_id BIGINT NOT NULL,
    status STATUS NOT NULL,
    joints JSONB,
    CONSTRAINT fk_scan_id
        FOREIGN KEY(scan_id)
        REFERENCES scan(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS video(
    id BIGSERIAL PRIMARY KEY,
    uuid UUID NOT NULL,
    scan_id BIGINT NOT NULL,
    status STATUS NOT NULL,
    joints JSONB,
    CONSTRAINT fk_scan_id
        FOREIGN KEY(scan_id)
        REFERENCES scan(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
