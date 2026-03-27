# Ensure the data directory exists
mkdir -p /app/data

# If the volume-mapped DB doesn't exist, seed it from the image's copy
if [ ! -f /app/data/ismap.db ] && [ -f /app/ismap.db ]; then
    echo "Seeding initial database to volume..."
    cp /app/ismap.db /app/data/ismap.db
fi

# Run the Flask application with a single worker to prevent duplicate schedulers
exec gunicorn --bind 0.0.0.0:5000 --timeout 120 --workers 1 app:app

