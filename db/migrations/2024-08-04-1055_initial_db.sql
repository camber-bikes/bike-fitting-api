CREATE EXTENSION "pgcrypto";

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
NEW.updated_at = now();
RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TABLE IF NOT EXISTS person(
    id BIGSERIAL PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL,
    name TEXT NOT NULL,
    height_cm SMALLINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE TRIGGER update_modified_person_time BEFORE UPDATE ON person FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TABLE IF NOT EXISTS scan(
    id BIGSERIAL PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL,
    person_id BIGINT NOT NULL,
    result JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_person_id
        FOREIGN KEY(person_id)
        REFERENCES person(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
CREATE TRIGGER update_modified_scan_time BEFORE UPDATE ON scan FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TYPE STATUS AS ENUM ('new', 'done');

CREATE TABLE IF NOT EXISTS image(
    id BIGSERIAL PRIMARY KEY,
    uuid UUID NOT NULL,
    scan_id BIGINT NOT NULL,
    status STATUS NOT NULL,
    joints JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_scan_id
        FOREIGN KEY(scan_id)
        REFERENCES scan(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
CREATE TRIGGER update_modified_image_time BEFORE UPDATE ON image FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

CREATE TABLE IF NOT EXISTS video(
    id BIGSERIAL PRIMARY KEY,
    uuid UUID NOT NULL,
    scan_id BIGINT NOT NULL,
    status STATUS NOT NULL,
    joints JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_scan_id
        FOREIGN KEY(scan_id)
        REFERENCES scan(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
CREATE TRIGGER update_modified_video_time BEFORE UPDATE ON video FOR EACH ROW EXECUTE PROCEDURE update_modified_column();
