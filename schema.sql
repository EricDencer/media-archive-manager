PRAGMA foreign_keys = ON;

-- ============================================================
-- Releases
-- ============================================================
--
-- A release represents the physical product that was purchased
-- or acquired.
--
-- Examples:
--   - Labyrinth DVD
--   - Universal Classic Monsters Blu-ray box set
--   - Supernatural Complete Series
--   - Mill Creek Sci-Fi compilation
--
-- A release may contain one or many physical discs.
-- A release is intentionally separate from movie/show identity.
-- ============================================================

CREATE TABLE IF NOT EXISTS releases (
    id INTEGER PRIMARY KEY,

    name TEXT NOT NULL,

    publisher TEXT,
    format TEXT NOT NULL,

    edition TEXT,
    catalog_number TEXT,
    release_year INTEGER,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- Discs
-- ============================================================
--
-- A disc represents one physical disc belonging to a release.
--
-- Examples:
--   - Disc 1
--   - Season 1 Disc 2
--   - Sci Fi 1a
--
-- backup_path points to the archived physical-media backup,
-- such as the directory containing VIDEO_TS.
-- ============================================================

CREATE TABLE IF NOT EXISTS discs (
    id INTEGER PRIMARY KEY,

    release_id INTEGER,

    name TEXT NOT NULL,
    disc_number INTEGER,

    backup_path TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (release_id)
        REFERENCES releases(id)
        ON DELETE SET NULL,

    UNIQUE (backup_path)
);


-- ============================================================
-- Movies
-- ============================================================
--
-- Represents logical movie identity independent of physical
-- releases.
--
-- The same movie may appear on multiple releases/discs.
--
-- Example:
--   Blade Runner (1982)
--
-- Multiple physical editions can all map to the same movie row.
-- ============================================================

CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY,

    name TEXT NOT NULL,
    year INTEGER NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (name, year)
);


-- ============================================================
-- Shows
-- ============================================================
--
-- Represents logical television-series identity.
--
-- Example:
--   Supernatural (2005)
--   One Step Beyond (1959)
-- ============================================================

CREATE TABLE IF NOT EXISTS shows (
    id INTEGER PRIMARY KEY,

    name TEXT NOT NULL,
    year INTEGER NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (name, year)
);


-- ============================================================
-- Episodes
-- ============================================================
--
-- Represents logical episode identity.
--
-- Season and episode numbers are first-class content identity.
--
-- Plex naming such as S01E03 is derived from these fields.
--
-- A single logical episode may appear on multiple physical
-- releases, but should exist only once in this table.
-- ============================================================

CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY,

    show_id INTEGER NOT NULL,

    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,

    title TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (show_id)
        REFERENCES shows(id)
        ON DELETE CASCADE,

    UNIQUE (show_id, season, episode)
);


-- ============================================================
-- Titles
-- ============================================================
--
-- A title represents a machine-discovered source title on a
-- physical disc.
--
-- This is the bridge between:
--
--   physical media
--       and
--   logical content identity
--
-- A title may identify either:
--
--   - one movie
--   - one television episode
--
-- but not both.
--
-- source_title is the MakeMKV title number.
--
-- Workflow state currently lives here because the existing
-- ingestion pipeline operates on title-level state.
-- ============================================================

CREATE TABLE IF NOT EXISTS titles (
    id INTEGER PRIMARY KEY,

    disc_id INTEGER NOT NULL,
    source_title INTEGER NOT NULL,

    duration TEXT,
    duration_seconds INTEGER NOT NULL DEFAULT 0,

    chapters INTEGER NOT NULL DEFAULT 0,
    size_bytes INTEGER NOT NULL DEFAULT 0,

    output_filename TEXT,

    media_type TEXT,

    movie_id INTEGER,
    episode_id INTEGER,

    approved INTEGER NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'discovered',
    notes TEXT,

    video_codec TEXT,
    audio_codec TEXT,

    width INTEGER NOT NULL DEFAULT 0,
    height INTEGER NOT NULL DEFAULT 0,

    display_aspect_ratio TEXT,
    frame_rate TEXT,
    field_order TEXT,

    audio_channels INTEGER NOT NULL DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (disc_id)
        REFERENCES discs(id)
        ON DELETE CASCADE,

    FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE SET NULL,

    FOREIGN KEY (episode_id)
        REFERENCES episodes(id)
        ON DELETE SET NULL,

    UNIQUE (disc_id, source_title),

    CHECK (
        approved IN (0, 1)
    ),

    CHECK (
        media_type IS NULL
        OR media_type IN ('movie', 'tv')
    ),

    CHECK (
        (
            media_type = 'movie'
            AND movie_id IS NOT NULL
            AND episode_id IS NULL
        )
        OR
        (
            media_type = 'tv'
            AND episode_id IS NOT NULL
            AND movie_id IS NULL
        )
        OR
        (
            media_type IS NULL
            AND movie_id IS NULL
            AND episode_id IS NULL
        )
    )
);


-- ============================================================
-- Artifacts
-- ============================================================
--
-- Represents files produced during media processing.
--
-- Examples:
--   extracted -> MakeMKV source MKV
--   encoded   -> H.264 encoded working file
--   published -> Plex-library copy
--
-- Keeping artifacts separate from titles allows multiple files
-- to exist for a single source title without adding more path
-- columns to the titles table.
-- ============================================================

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY,

    title_id INTEGER NOT NULL,

    artifact_type TEXT NOT NULL,

    path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (title_id)
        REFERENCES titles(id)
        ON DELETE CASCADE,

    CHECK (
        artifact_type IN (
            'extracted',
            'encoded',
            'published'
        )
    ),

    UNIQUE (title_id, artifact_type, path)
);


-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_discs_release_id
    ON discs(release_id);

CREATE INDEX IF NOT EXISTS idx_titles_disc_id
    ON titles(disc_id);

CREATE INDEX IF NOT EXISTS idx_titles_status
    ON titles(status);

CREATE INDEX IF NOT EXISTS idx_titles_movie_id
    ON titles(movie_id);

CREATE INDEX IF NOT EXISTS idx_titles_episode_id
    ON titles(episode_id);

CREATE INDEX IF NOT EXISTS idx_episodes_show_id
    ON episodes(show_id);

CREATE INDEX IF NOT EXISTS idx_artifacts_title_id
    ON artifacts(title_id);