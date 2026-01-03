from supabase import create_client
from dotenv import load_dotenv
import os


load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


supabase = create_client(supabase_url=SUPABASE_URL ,supabase_key= SUPABASE_KEY)

data = supabase.table("users").select("*").execute()
print(data)
