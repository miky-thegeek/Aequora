# This file is part of Aequora.
#
# Aequora is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Aequora is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Aequora.  If not, see <https://www.gnu.org/licenses/>.
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