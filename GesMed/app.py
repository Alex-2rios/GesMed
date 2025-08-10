from flask import Flask, jsonify
from flask_mysqldb import MySQL
from config import Config
import MySQLdb

mysql = MySQL()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    mysql.init_app(app)

    from controllers.mainController import mainBP
    app.register_blueprint(mainBP)

    @app.route("/DBCheck")
    def dbCheck():
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT 1")
            return jsonify({"status": "Ok", "message": "Conectado con exitote!!! ;)"})
        except MySQLdb.MySQLError as e:
            return jsonify({"status": "Error", "message": str(e)}), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method Not Allowed"}), 405

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=3000, debug=True)
