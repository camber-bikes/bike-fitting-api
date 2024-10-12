ALTER TABLE scan ADD CONSTRAINT uq_scan_uuid UNIQUE(uuid);
ALTER TABLE person ADD CONSTRAINT uq_person_uuid UNIQUE(uuid);
ALTER TABLE photo ADD CONSTRAINT uq_photo_scan_id UNIQUE(scan_id);
ALTER TABLE video ADD CONSTRAINT uq_video_scan_id UNIQUE(scan_id);
