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
                <span>${format.resolution} - ${format.ext} 
                      ${format.fps}fps ${format.tbr}
                      <small>(~${format.filesize})</small></span>
                <button 
                    class="download-button"
                    onclick="downloadVideo('${url}', '${format.format_id}')"
                >
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
    const button = event.target;
    const originalText = button.textContent;
    
    try {
        // Add loading state
        button.classList.add('loading');
        button.textContent = 'Preparing...';

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

        const data = await response.json();
        
        // Show preparing state
        button.classList.remove('loading');
        button.textContent = 'Starting...';
        button.style.backgroundColor = '#28a745';

        // Open the video URL in a new tab
        window.open(data.url, '_blank');

        // Show success state
        button.textContent = 'Started!';
        button.style.backgroundColor = '#28a745';
        
        // Reset button after 2 seconds
        setTimeout(() => {
            button.textContent = originalText;
            button.style.backgroundColor = '';
        }, 2000);

    } catch (error) {
        // Show error state
        button.classList.remove('loading');
        button.textContent = 'Error!';
        button.style.backgroundColor = '#dc3545';
        
        // Reset button after 2 seconds
        setTimeout(() => {
            button.textContent = originalText;
            button.style.backgroundColor = '';
        }, 2000);
        
        console.error(error);
    }
}