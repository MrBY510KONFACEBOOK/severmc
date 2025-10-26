from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import tempfile
import os

app = Flask(__name__)

def format_duration(duration):
    minutes = duration // 60
    seconds = duration % 60
    return f"{minutes}:{seconds:02d}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-video-info', methods=['POST'])
def get_video_info():
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Filter and process formats
            formats = []
            seen_qualities = set()
            
            for f in info['formats']:
                # Skip audio-only formats
                if f.get('vcodec') == 'none':
                    continue
                    
                quality = f.get('format_note', 'unknown')
                # Avoid duplicate qualities
                if quality in seen_qualities:
                    continue
                    
                seen_qualities.add(quality)
                formats.append({
                    'format_id': f['format_id'],
                    'quality': quality,
                    'ext': f['ext']
                })

            return jsonify({
                'title': info['title'],
                'duration': format_duration(info['duration']),
                'formats': formats
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        url = request.json.get('url')
        format_id = request.json.get('format_id')
        
        if not url or not format_id:
            return jsonify({'error': 'URL and format_id are required'}), 400

        # Create a temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'video.%(ext)s')

        ydl_opts = {
            'format': format_id,
            'outtmpl': temp_file,
            'quiet': True,
            'no_warnings': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            
            # Send the file and then clean up
            response = send_file(
                downloaded_file,
                as_attachment=True,
                download_name=f"{info['title']}.{info['ext']}"
            )
            
            # Delete the temporary file after sending
            @response.call_on_close
            def cleanup():
                try:
                    os.remove(downloaded_file)
                    os.rmdir(temp_dir)
                except:
                    pass
                    
            return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)