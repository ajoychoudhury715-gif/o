-- ============================================================
-- THE DENTAL BOND — Supabase Table Setup
-- Paste this entire script into your Supabase SQL Editor
-- and click "Run". Safe to run multiple times (IF NOT EXISTS).
-- ============================================================


-- ── 1. Schedule / Allotment State ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tdb_allotment_state (
    id          TEXT PRIMARY KEY,
    payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE tdb_allotment_state ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'tdb_allotment_state'
      AND policyname = 'allow_all_tdb_allotment_state'
  ) THEN
    CREATE POLICY allow_all_tdb_allotment_state
      ON tdb_allotment_state FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 2. Profiles (Assistants & Doctors) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS profiles (
    profile_id      TEXT PRIMARY KEY,
    kind            TEXT NOT NULL,           -- 'Assistants' or 'Doctors'
    name            TEXT NOT NULL DEFAULT '',
    role            TEXT DEFAULT '',
    department      TEXT DEFAULT '',
    phone           TEXT DEFAULT '',
    email           TEXT DEFAULT '',
    experience      INTEGER DEFAULT 0,
    weekly_off      TEXT DEFAULT '',          -- semicolon-separated day names
    notes           TEXT DEFAULT '',
    is_active       BOOLEAN DEFAULT true,
    specialisation  TEXT DEFAULT '',
    reg_number      TEXT DEFAULT '',
    can_first       BOOLEAN DEFAULT false,
    can_second      BOOLEAN DEFAULT false,
    can_third       BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'profiles'
      AND policyname = 'allow_all_profiles'
  ) THEN
    CREATE POLICY allow_all_profiles
      ON profiles FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 3. Assistant Attendance ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assistant_attendance (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date        TEXT NOT NULL,
    assistant   TEXT NOT NULL,
    punch_in    TEXT DEFAULT '',
    punch_out   TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE assistant_attendance ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'assistant_attendance'
      AND policyname = 'allow_all_attendance'
  ) THEN
    CREATE POLICY allow_all_attendance
      ON assistant_attendance FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 4. Duties Master ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS duties_master (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL DEFAULT '',
    description  TEXT DEFAULT '',
    frequency    TEXT DEFAULT '',
    est_minutes  INTEGER DEFAULT 30,
    active       BOOLEAN DEFAULT true
);

ALTER TABLE duties_master ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'duties_master'
      AND policyname = 'allow_all_duties_master'
  ) THEN
    CREATE POLICY allow_all_duties_master
      ON duties_master FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 5. Duty Assignments ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS duty_assignments (
    id           TEXT PRIMARY KEY,
    duty_id      TEXT DEFAULT '',
    assistant    TEXT DEFAULT '',
    op           TEXT DEFAULT '',
    est_minutes  INTEGER DEFAULT 30,
    active       BOOLEAN DEFAULT true
);

ALTER TABLE duty_assignments ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'duty_assignments'
      AND policyname = 'allow_all_duty_assignments'
  ) THEN
    CREATE POLICY allow_all_duty_assignments
      ON duty_assignments FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 6. Duty Runs ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS duty_runs (
    id           TEXT PRIMARY KEY,
    date         TEXT DEFAULT '',
    assistant    TEXT DEFAULT '',
    duty_id      TEXT DEFAULT '',
    status       TEXT DEFAULT '',
    started_at   TEXT DEFAULT '',
    due_at       TEXT DEFAULT '',
    ended_at     TEXT DEFAULT '',
    est_minutes  INTEGER DEFAULT 30,
    op           TEXT DEFAULT ''
);

ALTER TABLE duty_runs ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'duty_runs'
      AND policyname = 'allow_all_duty_runs'
  ) THEN
    CREATE POLICY allow_all_duty_runs
      ON duty_runs FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 7. Patients ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id    TEXT PRIMARY KEY,
    name  TEXT NOT NULL DEFAULT '',
    phone TEXT DEFAULT '',
    notes TEXT DEFAULT ''
);

ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'patients'
      AND policyname = 'allow_all_patients'
  ) THEN
    CREATE POLICY allow_all_patients
      ON patients FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 8. Users (Login & Auth) ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,     -- format: {salt_hex}:{pbkdf2_sha256_hex}
    role            TEXT NOT NULL DEFAULT 'assistant',
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'users'
      AND policyname = 'allow_all_users'
  ) THEN
    CREATE POLICY allow_all_users
      ON users FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 9. RBAC Role Permissions ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rbac_role_permissions (
    role               TEXT PRIMARY KEY,
    allowed_functions  JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at         TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE rbac_role_permissions ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'rbac_role_permissions'
      AND policyname = 'allow_all_rbac_role_permissions'
  ) THEN
    CREATE POLICY allow_all_rbac_role_permissions
      ON rbac_role_permissions FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── 10. RBAC User Overrides ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rbac_user_permissions (
    user_id            UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    override_enabled   BOOLEAN NOT NULL DEFAULT false,
    allowed_functions  JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at         TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE rbac_user_permissions ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'rbac_user_permissions'
      AND policyname = 'allow_all_rbac_user_permissions'
  ) THEN
    CREATE POLICY allow_all_rbac_user_permissions
      ON rbac_user_permissions FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;


-- ── Done ──────────────────────────────────────────────────────────────────────
-- Core + RBAC tables created with permissive RLS policies.
-- Your app is ready to connect.
