"""
Database schema and migration definitions for FaceSoter.
"""

SCHEMA_VERSION = 1

MIGRATIONS = {
    1: """
    -- Migration version 1: Initial FaceSoter schema
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS person_reference_faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
        image_path TEXT NOT NULL,
        bbox_json TEXT NOT NULL,
        landmarks_json TEXT,
        embedding_blob BLOB NOT NULL,
        thumbnail_path TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        file_hash TEXT,
        file_size INTEGER NOT NULL,
        width INTEGER,
        height INTEGER,
        modified_time REAL NOT NULL,
        face_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        created_at TEXT NOT NULL,
        processed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS image_faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
        bbox_x1 REAL NOT NULL,
        bbox_y1 REAL NOT NULL,
        bbox_x2 REAL NOT NULL,
        bbox_y2 REAL NOT NULL,
        det_score REAL NOT NULL,
        face_size REAL NOT NULL,
        landmarks_json TEXT,
        assigned_person_id INTEGER REFERENCES people(id) ON DELETE SET NULL,
        assigned_cluster_id TEXT,
        confidence REAL,
        thumbnail_path TEXT
    );

    CREATE TABLE IF NOT EXISTS face_embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        face_id INTEGER UNIQUE NOT NULL REFERENCES image_faces(id) ON DELETE CASCADE,
        dim INTEGER NOT NULL DEFAULT 512,
        norm REAL NOT NULL DEFAULT 1.0,
        embedding_blob BLOB NOT NULL
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        mode TEXT NOT NULL,
        source_dir TEXT NOT NULL,
        export_dir TEXT NOT NULL,
        status TEXT NOT NULL,
        include_subfolders INTEGER NOT NULL DEFAULT 1,
        settings_json TEXT NOT NULL,
        filter_target_ids_json TEXT,
        total_files INTEGER DEFAULT 0,
        processed_files INTEGER DEFAULT 0,
        failed_files INTEGER DEFAULT 0,
        faces_detected INTEGER DEFAULT 0,
        copied_files INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        completed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS job_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
        file_path TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        error_message TEXT,
        updated_at TEXT NOT NULL,
        UNIQUE(job_id, file_path)
    );

    CREATE TABLE IF NOT EXISTS classification_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
        target_category TEXT NOT NULL,
        destination_path TEXT NOT NULL,
        copy_status TEXT DEFAULT 'pending',
        error_message TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS application_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS model_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT NOT NULL,
        version TEXT NOT NULL,
        detector_name TEXT NOT NULL,
        recognizer_name TEXT NOT NULL,
        local_path TEXT NOT NULL,
        sha256 TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        installed_at TEXT NOT NULL
    );

    -- Performance indexes
    CREATE INDEX IF NOT EXISTS idx_images_file_path ON images(file_path);
    CREATE INDEX IF NOT EXISTS idx_images_file_hash ON images(file_hash);
    CREATE INDEX IF NOT EXISTS idx_images_status ON images(status);
    CREATE INDEX IF NOT EXISTS idx_image_faces_image_id ON image_faces(image_id);
    CREATE INDEX IF NOT EXISTS idx_image_faces_assigned_person ON image_faces(assigned_person_id);
    CREATE INDEX IF NOT EXISTS idx_image_faces_assigned_cluster ON image_faces(assigned_cluster_id);
    CREATE INDEX IF NOT EXISTS idx_job_files_job_id_status ON job_files(job_id, status);
    CREATE INDEX IF NOT EXISTS idx_classification_job_id ON classification_results(job_id);
    CREATE INDEX IF NOT EXISTS idx_person_ref_person_id ON person_reference_faces(person_id);
    """
}
