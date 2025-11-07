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
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=context)
