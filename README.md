# Smart Attendance System

### Project Files

1. `main` directory - contains all the main files needed to run the system

   - `library.py` contains all the functions
   - `enrollment.py` is the script for enrolling new users
   - `attendance.py` is the script that runs as the service (`sasr.service`) and always waits for fingerprints on the sensor and logs attendance

2. `data` directory contains the data of logs and users enrolled in the system.

   - if you dont have this file than create it

   ```bash
    mkdir data
   ```

3. `Attendance Sync` directory contains the python scripts for syncing data with google sheets.
   - `sync_current_log.sh` runs as cron job every hour
   - `sync_users.sh` runs as cron job every hour

### Maintaining the Project

1. Start and Stop the service named `sasr.service`, it is set to automatically run on system startup and this service runs the `attendance.py` script in the `main` directory.

2. Logs are stored in `/var/logs/sasr.log`
