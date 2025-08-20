from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# Import your existing function from app.py
from app import process_audio_file
from config import OUTPUT_DIR

app = Flask(__name__)
CORS(app)

@app.route("/api/health", methods=["GET"])
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}

@app.route("/api/process", methods=["POST"])
def process_api():
    if "audio" not in request.files:
        return jsonify({"error": "No file part 'audio' in request"}), 400

    f = request.files["audio"]
    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400

    target_language = request.form.get("language", "en")
    output_format = request.form.get("format", "pdf")
    summary_style = request.form.get("style", "concise")

    uploads_dir = OUTPUT_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    upload_path = uploads_dir / f.filename
    f.save(upload_path)

    try:
        saved_path = process_audio_file(
            audio_path=str(upload_path),
            target_language=target_language,
            output_format=output_format,
            summary_style=summary_style,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    saved = Path(saved_path)
    return jsonify({
        "message": "Success",
        "filename": saved.name,
        "path": str(saved),
        "download_url": f"/api/download/{saved.name}"
    })

@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
