import threading
import webview
from app import app

def start_flask():
    app.run(debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Launch desktop window pointing to Flask app
    webview.create_window("SQL Metadata Viewer", "http://127.0.0.1:5000/", width=1000, height=800)
    webview.start()