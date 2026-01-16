"""
Database models for pool occupancy data.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class OccupancyData(db.Model):
    """Model for storing pool occupancy readings."""
    __tablename__ = 'occupancy_data'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    current_count = db.Column(db.Integer, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    
    @property
    def percentage(self):
        """Calculate occupancy percentage from current count and max capacity."""
        if self.max_capacity > 0:
            return (self.current_count / self.max_capacity * 100)
        return 0.0
    
    def __repr__(self):
        return f'<OccupancyData {self.timestamp}: {self.current_count}/{self.max_capacity} ({self.percentage:.1f}%)>'
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'current_count': self.current_count,
            'max_capacity': self.max_capacity,
            'percentage': self.percentage
        }
