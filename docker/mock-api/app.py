import logging

from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)


@app.route("/user/create", methods=["POST"])
def user_create():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "invalid JSON body"}), 400

    app.logger.info("POST /user/create — payload: %s", body)
    return jsonify({"status": "created", "user": body}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
