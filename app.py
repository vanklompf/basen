"""
Flask application for monitoring swimming pool occupancy.
"""
import logging
import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, has_app_context
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

from models import db, OccupancyData
from scraper import fetch_pool_occupancy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure instance directory exists
instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_dir, exist_ok=True)

# Use absolute path for database
db_path = os.path.join(instance_dir, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database initialized")

# Initialize scheduler
scheduler = BackgroundScheduler(daemon=True)
scheduler.start()

# Define polling hours (6:00 - 22:00)
POLLING_START_TIME = datetime.strptime('06:00', '%H:%M').time()
POLLING_END_TIME = datetime.strptime('22:00', '%H:%M').time()


def fetch_and_store_occupancy():
    """Background job to fetch and store pool occupancy data."""
    # Check if current time is within polling hours (6:00 - 22:00)
    current_time = datetime.now().time()
    if current_time < POLLING_START_TIME or current_time > POLLING_END_TIME:
        logger.debug(f"Skipping fetch outside polling hours (6:00-22:00). Current time: {current_time.strftime('%H:%M')}")
        return
    
    logger.info("Fetching pool occupancy data...")
    result = fetch_pool_occupancy()
    
    if result:
        current_count, max_capacity = result
        
        # Use application context for database operations
        with app.app_context():
            # Check if we already have a recent reading (within last 4 minutes)
            # to avoid duplicate entries
            recent = db.session.query(OccupancyData).filter(
                OccupancyData.timestamp >= datetime.utcnow() - timedelta(minutes=4)
            ).first()
            
            if not recent or recent.current_count != current_count or recent.max_capacity != max_capacity:
                occupancy = OccupancyData(
                    current_count=current_count,
                    max_capacity=max_capacity
                )
                db.session.add(occupancy)
                db.session.commit()
                percentage = (current_count / max_capacity * 100) if max_capacity > 0 else 0
                logger.info(f"Stored occupancy data: {current_count}/{max_capacity} ({percentage:.1f}%)")
            else:
                logger.info("Skipping duplicate reading")
    else:
        logger.warning("Failed to fetch occupancy data")


# Get polling interval from environment variable, default to 5 minutes
try:
    polling_interval = int(os.getenv('POLLING_INTERVAL_MINUTES', '5'))
    if polling_interval < 1:
        logger.warning(f"Invalid polling interval {polling_interval}, using default of 5 minutes")
        polling_interval = 5
except (ValueError, TypeError):
    logger.warning("Invalid POLLING_INTERVAL_MINUTES value, using default of 5 minutes")
    polling_interval = 5

logger.info(f"Polling interval set to {polling_interval} minutes")

# Schedule the job to run at configured interval
scheduler.add_job(
    func=fetch_and_store_occupancy,
    trigger=IntervalTrigger(minutes=polling_interval),
    id='fetch_occupancy',
    name=f'Fetch pool occupancy every {polling_interval} minutes',
    replace_existing=True
)

# Fetch initial data on startup (only if within polling hours)
with app.app_context():
    current_time = datetime.now().time()
    if current_time >= POLLING_START_TIME and current_time <= POLLING_END_TIME:
        fetch_and_store_occupancy()
    else:
        logger.info(f"Skipping initial fetch outside polling hours (6:00-22:00). Current time: {current_time.strftime('%H:%M')}")

# Shut down scheduler when app exits
atexit.register(lambda: scheduler.shutdown())


@app.route('/')
def index():
    """Main page with chart visualization."""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """API endpoint to get historical occupancy data."""
    try:
        # Get data from last 24 hours by default
        hours = int(request.args.get('hours', 24))
        since = datetime.utcnow() - timedelta(hours=hours)
        
        data = db.session.query(OccupancyData).filter(
            OccupancyData.timestamp >= since
        ).order_by(OccupancyData.timestamp.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in data]
        })
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/latest')
def get_latest():
    """API endpoint to get the most recent occupancy reading."""
    try:
        latest = db.session.query(OccupancyData).order_by(
            OccupancyData.timestamp.desc()
        ).first()
        
        if latest:
            return jsonify({
                'success': True,
                'data': latest.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404
    except Exception as e:
        logger.error(f"Error fetching latest data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
