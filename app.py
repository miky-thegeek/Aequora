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
"""Main entry point for the Flask application."""
import os
from config import create_app, init_firefly_iii
from routes import register_routes

# Create Flask app and initialize FireflyIII
app = create_app()
fireflyIII = init_firefly_iii()

# Register all routes
register_routes(app, fireflyIII)

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Validate SSL certificate files exist
    cert_file = 'certs/server.crt'
    key_file = 'certs/server.key'
    
    if not os.path.exists(cert_file):
        print(f"Error: SSL certificate file not found: {cert_file}")
        exit(1)
    
    if not os.path.exists(key_file):
        print(f"Error: SSL key file not found: {key_file}")
        exit(1)
    
    context = (cert_file, key_file)
    debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    APP_PORT = int(os.getenv('APP_PORT', 8443))
    app.run(host='0.0.0.0', port=APP_PORT, debug=debug, ssl_context=context)
