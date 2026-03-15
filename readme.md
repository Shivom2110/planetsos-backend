## Setup

1. Clone the repo

2. Create `.env` file:
   ```env
   FEATHERLESS_API_KEY=...
   ELEVENLABS_API_KEY=...
   ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
   
   # Optional: Supabase for user/department accounts
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Set up Supabase:
   - Create a Supabase project at https://supabase.com
   - Run the SQL in `supabase_migration.sql` in Supabase SQL Editor
   - See `SUPABASE_SETUP.md` for detailed instructions

5. Run:
   ```bash
   uvicorn app:app --reload
   ```

## Features

- **Incident Reporting**: Upload images, text, or voice notes to report environmental issues
- **AI Analysis**: Featherless AI analyzes incidents and provides risk assessment
- **Voice Integration**: ElevenLabs TTS/STT for voice-based reporting
- **User Accounts**: (Optional) Supabase integration for user authentication
- **Department Accounts**: (Optional) Supabase integration for responder accounts
- **Ticket Management**: Create, view, and respond to environmental incident tickets

## API Endpoints

### Core Endpoints
- `POST /report` - Create a new incident ticket
- `GET /ticket/{ticket_id}` - Get ticket details
- `GET /tickets` - List all tickets
- `POST /respond` - Respond to a ticket
- `POST /transcribe` - Transcribe audio
- `POST /tts` - Text-to-speech

### Authentication Endpoints (Requires Supabase)
- `POST /auth/user/register` - Register user account
- `POST /auth/user/login` - Login user
- `GET /auth/user/profile` - Get user profile
- `POST /auth/department/register` - Register department account
- `POST /auth/department/login` - Login department
- `GET /auth/departments` - List all departments

See `README_SUPABASE.md` for detailed Supabase integration documentation.