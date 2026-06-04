# PostgreSQL Database Setup Guide for CCTRIX

Your CCTRIX application is now configured to work with PostgreSQL! Here are your options:

## Current Status
✅ **Code Updated** - All application code is updated to use PostgreSQL  
✅ **Database Module Ready** - `database.py` has all functions  
✅ **Tables Defined** - Schema is ready to create tables  

## Option 1: Use Railway (Cloud - Recommended for Deployment)
Your `.env` file is already configured for Railway!

**When to use:** When deploying to production on Railway  
**Current status:** Will work when deployed to Railway

**Connection Details (in .env):**
- Host: `postgres.railway.internal`
- Port: `5432`
- User: `postgres`
- Database: `railway`

## Option 2: Local PostgreSQL Setup (For Local Development)
This is best if you want to develop/test locally.

### Prerequisites:
1. **Install PostgreSQL locally** from https://www.postgresql.org/download/windows/
   - Download and run the Windows installer
   - During installation, set password for 'postgres' user (remember this!)
   - Choose port 5432 (default)
   - Install pgAdmin (optional, for GUI management)

2. **Update .env file** with local credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_NAME=cctrix_db
```

3. **Create the database** using pgAdmin or command line:
```bash
createdb -U postgres cctrix_db
```

4. **Run the test script**:
```bash
python test_db_setup.py
```

## Option 3: Use Docker (All-in-One Solution)
This runs PostgreSQL in a container, no local installation needed.

### Prerequisites:
- Docker Desktop installed (https://www.docker.com/products/docker-desktop)

### Steps:

1. **Create a `docker-compose.yml`** in your project directory:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: cctrix_password
      POSTGRES_DB: cctrix_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

2. **Start PostgreSQL container**:
```bash
docker-compose up -d
```

3. **Update .env file**:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=cctrix_password
DB_NAME=cctrix_db
```

4. **Run the test script**:
```bash
python test_db_setup.py
```

5. **Stop the container** (when done):
```bash
docker-compose down
```

## Option 4: Use a Remote PostgreSQL Service (Alternative Cloud Options)

### Neon (https://neon.tech)
- Free tier with good performance
- Get connection string from Neon dashboard
- Update .env with your Neon credentials

### Supabase (https://supabase.com)
- Built on PostgreSQL with free tier
- Get connection string from Supabase dashboard
- Update .env with your credentials

### Render (https://render.com)
- Has built-in PostgreSQL support
- Easy deployment alongside your Flask app
- Get connection string and add to .env

## Testing Your Setup

Once you've chosen an option and configured your database:

```bash
# Run the test script
python test_db_setup.py

# If successful, you'll see:
# ✅ ALL TESTS PASSED!
# Your PostgreSQL database is now ready to use!
```

## Using Your Application

### Start the Flask app:
```bash
python app.py
```

### Default Credentials:
- **Admin** - username: `admin`, password: `admin123`
- **Viewer** - username: `viewer`, password: `viewer123`

### Features Now Available:
✅ User login/logout with audit logs  
✅ Person detection logging  
✅ Failed login tracking with IP blocking  
✅ Admin dashboard with statistics  
✅ Export logs as CSV  
✅ System status monitoring  

## Troubleshooting

### "Connection refused" or "could not translate host name"
- Check that your database server is running
- Verify DB_HOST, DB_PORT in .env are correct
- Check DB_USER and DB_PASSWORD are correct

### "Database cctrix_db does not exist"
- Create the database using your database tool
- Or PostgreSQL will auto-create it on first connection (with some configurations)

### "permission denied for database"
- Verify your user has permissions
- Check that you're using correct DB_USER and DB_PASSWORD

### "Port 5432 already in use"
- Change DB_PORT to another port (5433, 5434, etc.)
- Or stop the service using that port

## Database Schema

Your application creates these tables automatically:

1. **users** - User accounts with roles
2. **detection_logs** - Person detection events
3. **auth_logs** - Login/logout audit trail
4. **failed_login_attempts** - Failed login tracking for security

All tables have automatic timestamps and indexes for performance.

## Backing Up Your Data

### PostgreSQL backup:
```bash
pg_dump -U postgres -d cctrix_db > backup.sql
```

### Restore from backup:
```bash
psql -U postgres -d cctrix_db < backup.sql
```

## Next Steps

1. **Choose your database option** (Local, Docker, or Cloud)
2. **Update your .env file** with the credentials
3. **Run the test script** to verify setup
4. **Start your Flask app** and enjoy CCTRIX!

---

**Questions?** Check the troubleshooting section or the main README.md
