

@app.post("/make-video")
def make_video():
    data = request.get_json(silent=True) or {}
    images = data.get("images", [])
    audio_url = data.get("audio_url")

    if not images or not audio_url:
        return jsonify({
            "error": "Images aur audio_url dena zaroori hai"
        }), 400

    job = BASE / str(uuid.uuid4())
    job.mkdir(parents=True, exist_ok=True)

    try:
        local_images = []

        for i, url in enumerate(images):
            path = job / f"scene_{i:03d}.jpg"
            response = requests.get(url, timeout=45)
            response.raise_for_status()
            path.write_bytes(response.content)
            local_images.append(path)

        audio = job / "voice.mp3"
        response = requests.get(audio_url, timeout=45)
        response.raise_for_status()
        audio.write_bytes(response.content)

        concat_file = job / "images.txt"

        with open(concat_file, "w", encoding="utf-8") as f:
            for path in local_images:
                f.write(f"file '{path}'\n")
                f.write("duration 4\n")
            f.write(f"file '{local_images[-1]}'\n")

        output = job / "RealSoulToon.mp4"

        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-i", str(audio),
            "-vf",
            "scale=720:1280:force_original_aspect_ratio=decrease,"
            "pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-r", "24",
            "-c:a", "aac",
            "-shortest",
            "-movflags", "+faststart",
            str(output)
        ], check=True, timeout=240)

        return send_file(
            output,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="RealSoulToon.mp4"
        )

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500
