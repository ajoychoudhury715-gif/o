-- RBAC Tables Only (paste into Supabase SQL Editor)

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
