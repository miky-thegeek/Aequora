"""Configuration and initialization for the Flask application."""
import os
from flask import Flask
from firefly_iii import FireflyIII

def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance with upload folder set.
    """
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'upload'
    return app

def init_firefly_iii():
    """Initialize and return FireflyIII client.
    
    Reads FireflyIII credentials from environment variables and creates
    a FireflyIII client instance.
    
    Returns:
        FireflyIII: Initialized FireflyIII client instance.
        
    Raises:
        ValueError: If required environment variables (fireflyIII_id or 
                    fireflyIII_secret) are missing.
    """
    fireflyIII_url = os.environ.get("fireflyIII_url")
    fireflyIII_id = os.environ.get("fireflyIII_id")
    fireflyIII_secret = os.environ.get("fireflyIII_secret")
    
    if not fireflyIII_id or not fireflyIII_secret:
        raise ValueError("Missing required environment variables: fireflyIII_id and fireflyIII_secret")

    return FireflyIII(fireflyIII_url, fireflyIII_id, fireflyIII_secret)