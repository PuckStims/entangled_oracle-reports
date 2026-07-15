import os

from app.web import create_app


app = create_app()


if __name__ == "__main__":
    debug = os.environ.get("EO_STUDIO_DEBUG") == "1"
    app.run(host="127.0.0.1", port=5055, debug=debug, use_reloader=False)
