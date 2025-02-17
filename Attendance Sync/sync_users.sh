#!/bin/bash

# Wait until internet is available (check every 10 seconds for 2 minutes)
for i in {1..12}; do
    if ping -c 1 google.com &> /dev/null; then
        echo "Internet is available. Running sync_users.py..."
        /home/rudra/maverick/new/sas-r/venv/bin/python /home/rudra/maverick/new/sas-r/Attendance\ Sync/sync_users.py
        exit 0
    fi
    echo "Waiting for internet..."
    sleep 10
done

echo "Internet not available. sync_users.py skipped."
exit 1
