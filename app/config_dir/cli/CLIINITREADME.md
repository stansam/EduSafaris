# EduSafaris Database Initialization CLI Guide

Complete guide for initializing and managing test data in the EduSafaris application.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Available Commands](#available-commands)
- [Command Details](#command-details)
- [Data Structure](#data-structure)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Installation

### 1. Register CLI Commands

Add the following to your Flask application factory (`app/__init__.py`):

```python
from app.cli.cli_init_db import register_cli_commands

def create_app(config_name='development'):
    app = Flask(__name__)
    # ... other initialization code ...
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app
```

### 2. Required Dependencies

Ensure these packages are in your `requirements.txt`:

```txt
Flask>=2.3.0
Flask-SQLAlchemy>=3.0.0
click>=8.1.0
Faker>=18.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### Initialize Complete Database

```bash
# Clear existing data and initialize everything
flask init-db clear-all
flask init-db init-all
```

### Check Status

```bash
# View database statistics
flask init-db stats

# Check if tables have data
flask init-db check
```

## Available Commands

### Main Commands

| Command | Description |
|---------|-------------|
| `init-all` | Initialize all tables with sample data |
| `clear-all` | **WARNING:** Delete all data from database |
| `stats` | Display database statistics |
| `check [--table TABLE]` | Check if tables have data |

### Individual Table Commands

| Command | Description | Dependencies |
|---------|-------------|--------------|
| `init-schools` | Initialize schools | None |
| `init-users` | Initialize users (admins, teachers, parents, vendors) | Schools |
| `init-vendors` | Initialize vendor profiles | Vendor users |
| `init-participants` | Initialize participants (children/students) | Parent users |
| `init-trips` | Initialize educational trips | Teachers, Schools |
| `init-registrations` | Initialize trip registrations | Participants, Trips |
| `init-payments` | Initialize payment records | Registrations |
| `init-bookings` | Initialize service bookings | Trips, Vendors |
| `init-ads` | Initialize advertisements | Vendors, Trips |
| `init-documents` | Initialize documents | Trips, Participants, Vendors |
| `init-consents` | Initialize consent forms | Registrations |
| `init-locations` | Initialize location tracking data | Trips, Participants |
| `init-emergencies` | Initialize emergency records | Completed trips |
| `init-messages` | Initialize messages | Teachers, Parents, Trips |
| `init-notifications` | Initialize notifications | Parents, Trips |
| `init-reviews` | Initialize reviews | Completed registrations, Vendors |
| `init-activity-logs` | Initialize activity logs | Users, Trips, Registrations |

### Utility Commands

| Command | Description |
|---------|-------------|
| `show-user --email EMAIL` | Display detailed user information |
| `show-trips` | Display all trips summary |

## Command Details

### Full Initialization

Initialize the entire database with realistic test data:

```bash
flask init-db init-all
```

**What it creates:**
- 5 schools (Nairobi, Mombasa, Arusha, etc.)
- 15+ users (1 admin, 4 teachers, 10 parents, 4 vendors)
- 4 vendor profiles (transport, accommodation, activities)
- 20+ participants (children)
- 7 trips (wildlife, marine, mountain, etc.)
- 50+ registrations (various statuses)
- 40+ payments (completed, partial)
- 15+ service bookings
- 4 advertisements
- 20+ documents
- 20+ consents
- 100+ location records
- 2 emergency records (resolved)
- 10+ messages
- 30+ notifications
- 15+ reviews
- 100+ activity logs

**Execution time:** ~10-30 seconds depending on system

### Clear Database

**⚠️ WARNING: This deletes all data permanently!**

```bash
flask init-db clear-all
```

You will be prompted to confirm:
```
Are you sure you want to delete ALL data? [y/N]:
```

### View Statistics

Get a comprehensive overview of your database:

```bash
flask init-db stats
```

**Output example:**
```
=== EduSafaris Database Statistics ===

Schools: 5
Users: 15
  - Admins: 1
  - Teachers: 4
  - Parents: 10
  - Vendors: 4
Vendors: 4
Participants: 20
Trips: 7
  - Published: 6
  - Registration Open: 4
  - Completed: 1
Registrations: 55
  - Confirmed: 35
  - Pending: 15
  - Completed: 5
...

Financial Summary:
Total Revenue: KES 145,250.00
```

### Check Tables

Check which tables have data:

```bash
# Check all tables
flask init-db check

# Check specific table
flask init-db check --table users
```

### Show User Details

Display detailed information about a specific user:

```bash
flask init-db show-user --email john.kamau@nairobiintl.ac.ke
```

**Output example:**
```
=== User Details ===

Name: John Kamau
Email: john.kamau@nairobiintl.ac.ke
Phone: +254-722-111111
Role: teacher
Active: True
Verified: True
Created: 2024-11-02 10:30:45

School: Nairobi International School
Department: Science
Active Trips: 2
Total Students: 45
```

### Show Trips

Display summary of all trips:

```bash
flask init-db show-trips
```

## Data Structure

### Default Users Created

#### Admin
- **Email:** admin@edusafaris.com
- **Password:** Admin@123
- **Role:** admin

#### Teachers
1. **Email:** john.kamau@nairobiintl.ac.ke
   - **Password:** Teacher@123
   - **School:** Nairobi International School

2. **Email:** mary.wanjiru@brookhouse.ac.ke
   - **Password:** Teacher@123
   - **School:** Brookhouse School

3. **Email:** david.omondi@braeburn.ac.tz
   - **Password:** Teacher@123
   - **School:** Braeburn School Arusha

4. **Email:** sarah.mwangi@satschool.com
   - **Password:** Teacher@123
   - **School:** St. Andrews School Turi

#### Parents
- **Password:** Parent@123 (all parents)
- **Emails:** james.njoroge@email.com, grace.akinyi@email.com, etc.

#### Vendors
- **Password:** Vendor@123 (all vendors)
- **Emails:** contact@safaritrans.com, info@wildcamping.com, etc.

### Sample Trips Created

1. **Maasai Mara Wildlife Safari** (3 days)
   - Status: Registration Open
   - Price: KES 350.00
   - Max Participants: 40

2. **Mount Kenya Climbing Expedition** (5 days)
   - Status: Registration Open
   - Price: KES 450.00
   - Max Participants: 25

3. **Mombasa Marine Biology Workshop** (4 days)
   - Status: Registration Open
   - Price: KES 400.00
   - Max Participants: 35

4. **Lake Nakuru Flamingo Study** (2 days)
   - Status: Registration Open
   - Price: KES 200.00
   - Max Participants: 30

5. **Hell's Gate Cycling Adventure** (2 days)
   - Status: Completed
   - Price: KES 250.00

## Troubleshooting

### Error: "Tables must be initialized first"

**Problem:** Foreign key dependencies not met

**Solution:** Initialize tables in correct order:
```bash
flask init-db init-schools
flask init-db init-users
flask init-db init-vendors
flask init-db init-participants
flask init-db init-trips
# ... continue in order
```

Or use `init-all` which handles dependencies automatically.

### Error: "Already exist, skipping..."

**Problem:** Data already exists in table

**Solution:** 
- Clear existing data: `flask init-db clear-all`
- Or manually delete specific records from database

### Error: "No vendor users found"

**Problem:** Users table doesn't have vendor role users

**Solution:**
```bash
flask init-db init-users
flask init-db init-vendors
```

### Slow Performance

**Problem:** Large dataset initialization taking too long

**Solution:**
- Initialize tables individually instead of `init-all`
- Check database connections and indexes
- Reduce sample data size in code if needed

### Import Errors

**Problem:** Cannot import models or extensions

**Solution:**
```bash
# Ensure proper Flask app context
export FLASK_APP=run.py
flask shell

# Test imports
from app.models import User, Trip
```

## Best Practices

### 1. Development Workflow

```bash
# Start fresh
flask init-db clear-all
flask init-db init-all

# Check results
flask init-db stats
flask init-db check
```

### 2. Testing Specific Features

```bash
# Only initialize what you need
flask init-db init-schools
flask init-db init-users
flask init-db init-trips
```

### 3. Staging Environment

```bash
# Use consistent seed for reproducible data
# (Modify code to use seed: random.seed(42))

flask init-db init-all
```

### 4. Production

**⚠️ NEVER use these commands in production!**

These CLI commands are for **development and testing only**. Production data should:
- Be imported from real sources
- Use proper migrations
- Have backups before any modifications

### 5. Regular Maintenance

```bash
# Weekly: Check data consistency
flask init-db stats

# Before major changes: Backup
# (Use your database backup tools)

# After changes: Verify
flask init-db check
```

## Advanced Usage

### Custom Initialization Scripts

Create your own initialization functions in `cli_helpers.py`:

```python
def init_custom_data():
    """Initialize custom data for specific test scenarios"""
    # Your custom logic here
    pass
```

Register in `cli_init_db.py`:

```python
@init_db.command()
@with_appcontext
def init_custom():
    """Initialize custom test data"""
    init_custom_data()
```

### Batch Operations

```python
from app.cli.cli_helpers import BatchProcessor

processor = BatchProcessor(batch_size=100)

for item in large_dataset:
    batch = processor.add(item)
    if batch:
        db.session.bulk_save_objects(batch)
        db.session.commit()

# Flush remaining
if processor.has_items():
    db.session.bulk_save_objects(processor.flush())
    db.session.commit()
```

### Progress Tracking

```python
from app.cli.cli_helpers import ProgressTracker

tracker = ProgressTracker(total=100, description="Creating users")

for i in range(100):
    # Create user
    print(tracker.update())
```

## Logging

All CLI operations are logged using Flask's logger. View logs:

```bash
# Terminal output
flask init-db init-all

# Check application logs
tail -f logs/app.log
```

Log levels:
- `INFO`: Normal operations
- `WARNING`: Skipped operations (data exists)
- `ERROR`: Failed operations with traceback

## Support

For issues or questions:

1. Check logs: `tail -f logs/app.log`
2. Verify database connection
3. Check model imports
4. Review error traceback

## License

Internal tool for EduSafaris development team.