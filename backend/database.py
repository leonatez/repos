from supabase import create_client, Client
from config import settings

# anon client — used only for verifying user JWTs in auth.py
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# service client — bypasses RLS for all backend DB operations
supabase_service: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
