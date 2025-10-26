async function getVideoInfo() {
    const urlInput = document.getElementById('url-input');
    const videoInfo = document.getElementById('video-info');
    const videoDetails = document.getElementById('video-details');
    const qualityOptions = document.getElementById('quality-options');
    const loading = document.getElementById('loading');

    const url = urlInput.value.trim();
    if (!url) {
        alert('Please enter a YouTube URL');
        return;
    }

    try {
        loading.classList.remove('hidden');
        videoInfo.classList.add('hidden');

        const response = await fetch('/get-video-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to get video info');
        }

        videoDetails.innerHTML = `
            <h2>${data.title}</h2>
            <p>Duration: ${data.duration}</p>
        `;

        qualityOptions.innerHTML = data.formats.map(format => `
            <div class="quality-option">
                <span>${format.quality} (${format.ext})</span>
                <button onclick="downloadVideo('${url}', '${format.format_id}')">
                    Download
                </button>
            </div>
        `).join('');

        videoInfo.classList.remove('hidden');
    } catch (error) {
        alert(error.message);
    } finally {
        loading.classList.add('hidden');
    }
}

async function downloadVideo(url, formatId) {
    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: url,
                format_id: formatId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Download failed');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = 'video'; // The actual filename will be set by the server
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);
    } catch (error) {
        alert(error.message);
    }
}