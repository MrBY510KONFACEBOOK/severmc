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
            'cookiefile': 'cookies.txt',
            'format': 'best',
            'extract_flat': False,  # We need full extraction for formats
            'youtube_include_dash_manifest': False,  # Skip DASH manifests
            'youtube_include_hls_manifest': True,  # Include HLS/m3u8 formats
            'format_sort': ['res', 'fps', 'codec', 'size', 'br', 'asr']
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Filter and process formats
            formats = []
            for f in info['formats']:
                # Skip storyboard formats and formats without video
                if f.get('format_note', '').startswith('storyboard') or f.get('vcodec') == 'none':
                    continue

                # Get resolution
                width = f.get('width', 0)
                height = f.get('height', 0)
                resolution = f"{width}x{height}" if width and height else f.get('format_note', 'unknown')

                # Calculate filesize
                filesize = f.get('filesize') or f.get('filesize_approx')
                if filesize:
                    filesize_mb = round(filesize / (1024 * 1024), 2)
                    filesize_str = f"{filesize_mb} MB"
                elif f.get('tbr') and f.get('duration'):
                    # Estimate size for m3u8 streams based on bitrate and duration
                    estimated_size = (f.get('tbr', 0) * 128) * f.get('duration', 0) / 8192  # Convert to MB
                    filesize_str = f"~{estimated_size:.2f} MB"
                else:
                    filesize_str = "Unknown size"

                # Get bitrate
                tbr = f.get('tbr')
                if tbr:
                    if tbr >= 1000:
                        tbr_str = f"{tbr/1000:.1f}Mbps"
                    else:
                        tbr_str = f"{int(tbr)}Kbps"
                else:
                    tbr_str = ""

                format_info = {
                    'format_id': f['format_id'],
                    'ext': f.get('ext', 'mp4'),
                    'resolution': resolution,
                    'filesize': filesize_str,
                    'fps': f.get('fps', 30),
                    'tbr': tbr_str,
                    'format_note': f.get('format_note', ''),
                    'vcodec': f.get('vcodec', '').split('.')[0],
                    'acodec': f.get('acodec', '').split('.')[0]
                }
                
                # Skip formats that don't have necessary information
                if resolution == 'unknown' and not format_info['format_note']:
                    continue
                    
                formats.append(format_info)
            
            # Sort formats by resolution (height) in descending order
            formats.sort(key=lambda x: int(x['resolution'].split('x')[1]) if 'x' in x['resolution'] else 0, reverse=True)

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

        ydl_opts = {
            'format': format_id,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'youtube_include_dash_manifest': False,
            'youtube_include_hls_manifest': True,
            'extract_flat': False,
            'format_sort': ['res', 'fps', 'codec', 'size', 'br', 'asr']
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get the URL for the specific format
            for f in info.get('formats', []):
                if f.get('format_id') == format_id and 'url' in f:
                    direct_url = f['url']
                    return jsonify({
                        'url': direct_url,
                        'title': info.get('title', 'video'),
                        'ext': f.get('ext', 'mp4')
                    })
            
            # If we couldn't find the format, try to get the URL directly
            try:
                format_selector = f'{format_id}+bestaudio/best'
                direct_url = ydl.extract_info(url, download=False, process=False)['url']
                return jsonify({
                    'url': direct_url,
                    'title': info.get('title', 'video'),
                    'ext': info.get('ext', 'mp4')
                })
            except Exception as format_error:
                print(f"Format error: {format_error}")
                return jsonify({'error': 'Could not get direct URL'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)