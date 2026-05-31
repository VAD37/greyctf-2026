import os

from flask import Flask, Response, render_template, request

from crypto import encrypt_blob


app = Flask(__name__)
app.secret_key = "fortknocks-local-session-key"
SEAL_PASSWORD = os.environ.get("FORTKNOCKIES_SEAL_KEY", "rookie-local-test-key")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/encrypt", methods=["POST"])
def encrypt_upload():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return render_template("index.html", error="Pick a file first."), 400
    sealed = encrypt_blob(upload.read(), SEAL_PASSWORD, upload.filename)
    out_name = f"{upload.filename}.enc"
    return Response(
        sealed,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={out_name}"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
