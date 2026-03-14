#!/usr/bin/env python3
"""
Check for missing RBAC tables and provide instructions.
Usage: python run_migrations.py
"""

from config.settings import get_supabase_config
from data.supabase_client import get_supabase_client

def check_tables():
    url, key, *_ = get_supabase_config()

    if not url or not key:
        print("❌ Supabase URL/KEY not found")
        return False

    try:
        client = get_supabase_client(url, key)
        if not client:
            print("❌ Failed to connect to Supabase")
            return False

        # Try to query the tables
        try:
            client.table("rbac_role_permissions").select("*").limit(1).execute()
            print("✅ rbac_role_permissions exists")
        except Exception as e:
            print(f"❌ rbac_role_permissions missing: {str(e)[:100]}")
            return False

        try:
            client.table("rbac_user_permissions").select("*").limit(1).execute()
            print("✅ rbac_user_permissions exists")
        except Exception as e:
            print(f"❌ rbac_user_permissions missing: {str(e)[:100]}")
            return False

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if check_tables():
        print("\n✅ All RBAC tables exist!")
    else:
        print("\n⚠️  RBAC tables are missing.")
        print("Run this SQL in Supabase SQL Editor:")
        print("1. Go to Supabase Dashboard > SQL Editor")
        print("2. Copy the entire contents of supabase_setup.sql")
        print("3. Paste and click Run")
