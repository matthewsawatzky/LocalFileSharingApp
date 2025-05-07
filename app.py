from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    redirect,
    url_for,
    jsonify,
)
import os
import json
import time
import random
import string
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "uploads"
STATS_FILE = "download_stats.json"
SPEEDTEST_FOLDER = "speedtest"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SPEEDTEST_FOLDER"] = SPEEDTEST_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # Limit uploads to 500MB

# Create necessary directories if they don't exist
for folder in [UPLOAD_FOLDER, SPEEDTEST_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)


# Initialize or load download stats
def get_download_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_download_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)


def generate_random_file(size_mb=10):
    """Generate a random file of specified size in MB for speed testing"""
    filename = f"speedtest_{int(time.time())}_{size_mb}MB.bin"
    filepath = os.path.join(app.config["SPEEDTEST_FOLDER"], filename)

    # Generate file with random content
    with open(filepath, "wb") as f:
        # Write in chunks to avoid memory issues
        chunk_size = 1024 * 1024  # 1MB chunks
        for _ in range(size_mb):
            f.write(os.urandom(chunk_size))

    return filename


@app.route("/")
def index():
    # Get list of files in upload directory
    files = []
    stats = get_download_stats()

    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                # Get file size
                size_bytes = os.path.getsize(file_path)
                # Format size
                if size_bytes < 1024:
                    size = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size = f"{size_bytes/1024:.1f} KB"
                else:
                    size = f"{size_bytes/(1024*1024):.1f} MB"

                download_count = stats.get(filename, 0)

                files.append(
                    {
                        "name": filename,
                        "size": size,
                        "size_bytes": size_bytes,
                        "downloads": download_count,
                    }
                )

    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part"})

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "message": "No selected file"})

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        # Save file
        start_time = time.time()
        file.save(file_path)
        upload_time = time.time() - start_time

        # Get file size
        size_bytes = os.path.getsize(file_path)

        # Calculate upload speed
        if upload_time > 0:
            upload_speed = size_bytes / upload_time / 1024 / 1024  # MB/s
        else:
            upload_speed = 0

        # Initialize download count for new file
        stats = get_download_stats()
        if filename not in stats:
            stats[filename] = 0
            save_download_stats(stats)

        return jsonify(
            {
                "success": True,
                "message": "File uploaded successfully",
                "filename": filename,
                "size": size_bytes,
                "upload_speed": f"{upload_speed:.2f} MB/s",
            }
        )


@app.route("/download/<filename>")
def download_file(filename):
    # Increment download count
    stats = get_download_stats()
    stats[filename] = stats.get(filename, 0) + 1
    save_download_stats(stats)

    return send_from_directory(
        app.config["UPLOAD_FOLDER"], filename, as_attachment=True
    )


@app.route("/delete/<filename>")
def delete_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

        # Remove from stats
        stats = get_download_stats()
        if filename in stats:
            del stats[filename]
            save_download_stats(stats)

    return redirect(url_for("index"))


@app.route("/generate_speedtest_file/<int:size>")
def generate_test_file(size):
    """Generate a file of specified size in MB for download speed testing"""
    try:
        # Limit the maximum size to prevent abuse
        if size > 100:
            size = 100  # Limit to 100MB

        filename = generate_random_file(size)
        return jsonify({"success": True, "filename": filename, "size_mb": size})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/speedtest/download/<filename>")
def download_test_file(filename):
    """Send the generated speed test file"""
    file_path = os.path.join(app.config["SPEEDTEST_FOLDER"], filename)
    if os.path.exists(file_path):
        return send_from_directory(
            app.config["SPEEDTEST_FOLDER"], filename, as_attachment=True
        )
    else:
        return "File not found", 404


@app.route("/speedtest/upload", methods=["POST"])
def upload_speed_test():
    """Handle upload speed test"""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part"})

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "message": "No selected file"})

    if file:
        # Get file size and timing info from request
        file_size = int(request.form.get("file_size", 0))
        start_time = float(request.form.get("start_time", 0))
        end_time = time.time()

        # Calculate upload speed
        duration = end_time - start_time
        upload_speed = file_size / duration / 1024 / 1024 if duration > 0 else 0  # MB/s

        # Delete the uploaded test file - we don't need to keep it
        # The file content is discarded

        return jsonify(
            {
                "success": True,
                "upload_speed": upload_speed,
                "upload_speed_formatted": f"{upload_speed:.2f} MB/s",
                "duration": f"{duration:.2f} seconds",
            }
        )


@app.route("/clean_speedtest_files")
def clean_speedtest_files():
    """Clean up old speedtest files"""
    try:
        count = 0
        for filename in os.listdir(app.config["SPEEDTEST_FOLDER"]):
            file_path = os.path.join(app.config["SPEEDTEST_FOLDER"], filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                count += 1

        return jsonify({"success": True, "message": f"Removed {count} speedtest files"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


if __name__ == "__main__":
    # Create templates directory and index.html
    if not os.path.exists("templates"):
        os.makedirs("templates")

    with open("templates/index.html", "w") as f:
        f.write(
            """<!DOCTYPE html>
<html>
<head>
    <title>Local File Sharing</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2 {
            color: #333;
        }
        .section {
            margin: 30px 0;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .file-list {
            margin-top: 30px;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .file-name {
            flex-grow: 1;
            word-break: break-all;
        }
        .file-info {
            color: #666;
            margin-right: 15px;
            white-space: nowrap;
        }
        .button, .download-btn, .delete-btn {
            display: inline-block;
            padding: 5px 10px;
            text-decoration: none;
            border-radius: 3px;
            color: white;
            font-size: 14px;
            cursor: pointer;
            border: none;
        }
        .button {
            background-color: #2196F3;
        }
        .download-btn {
            background-color: #4CAF50;
            margin-right: 5px;
        }
        .delete-btn {
            background-color: #f44336;
        }
        .empty-list {
            padding: 20px;
            color: #666;
            text-align: center;
        }
        .progress-container {
            width: 100%;
            background-color: #ddd;
            border-radius: 3px;
            margin: 10px 0;
            display: none;
        }
        .progress-bar {
            width: 0%;
            height: 20px;
            background-color: #4CAF50;
            border-radius: 3px;
            text-align: center;
            line-height: 20px;
            color: white;
        }
        .speedtest-results {
            margin-top: 15px;
            padding: 10px;
            background-color: #e8f5e9;
            border-radius: 3px;
            display: none;
        }
        .speedtest-buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .speedtest-file-sizes {
            display: flex;
            gap: 10px;
            margin: 10px 0;
        }
        .speedtest-file-sizes button {
            flex: 1;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid #ddd;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            background-color: #f1f1f1;
            border: 1px solid #ddd;
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }
        .tab.active {
            background-color: white;
            border-bottom: 1px solid white;
            margin-bottom: -1px;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 3px;
            display: none;
        }
        .success {
            background-color: #dff0d8;
            color: #3c763d;
        }
        .error {
            background-color: #f2dede;
            color: #a94442;
        }
    </style>
</head>
<body>
    <h1>Local File Sharing</h1>
    
    <div class="tabs">
        <div class="tab active" data-tab="files">Files</div>
        <div class="tab" data-tab="speedtest">Speed Test</div>
    </div>
    
    <div id="filesTab" class="tab-content active">
        <div class="section">
            <h2>Upload File</h2>
            <div id="uploadMessage" class="message"></div>
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="fileInput" name="file" required>
                <button type="submit" class="button">Upload</button>
                <div class="progress-container" id="uploadProgressContainer">
                    <div class="progress-bar" id="uploadProgressBar">0%</div>
                </div>
                <div id="uploadSpeed" style="margin-top: 5px;"></div>
            </form>
        </div>
        
        <div class="file-list">
            <h2>Available Files</h2>
            <div id="filesList">
                {% if files %}
                    {% for file in files %}
                        <div class="file-item">
                            <div class="file-name">{{ file.name }}</div>
                            <div class="file-info">{{ file.size }} | {{ file.downloads }} downloads</div>
                            <a href="#" class="download-btn" data-filename="{{ file.name }}" data-size="{{ file.size_bytes }}">Download</a>
                            <a href="{{ url_for('delete_file', filename=file.name) }}" class="delete-btn" onclick="return confirm('Are you sure you want to delete this file?')">Delete</a>
                        </div>
                        <div class="progress-container download-progress" id="download-{{ file.name }}" style="display: none;">
                            <div class="progress-bar">0%</div>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-list">No files available</div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <div id="speedtestTab" class="tab-content">
        <div class="section">
            <h2>Network Speed Test</h2>
            <p>Test your connection speed with this server:</p>
            
            <h3>Download Speed Test</h3>
            <div class="speedtest-file-sizes">
                <button class="button" onclick="startDownloadTest(5)">5 MB</button>
                <button class="button" onclick="startDownloadTest(10)">10 MB</button>
                <button class="button" onclick="startDownloadTest(25)">25 MB</button>
                <button class="button" onclick="startDownloadTest(50)">50 MB</button>
            </div>
            <div class="progress-container" id="downloadTestProgress">
                <div class="progress-bar" id="downloadTestProgressBar">0%</div>
            </div>
            <div id="downloadTestResult" class="speedtest-results"></div>
            
            <h3>Upload Speed Test</h3>
            <div class="speedtest-file-sizes">
                <button class="button" onclick="startUploadTest(5)">5 MB</button>
                <button class="button" onclick="startUploadTest(10)">10 MB</button>
                <button class="button" onclick="startUploadTest(25)">25 MB</button>
                <button class="button" onclick="startUploadTest(50)">50 MB</button>
            </div>
            <div class="progress-container" id="uploadTestProgress">
                <div class="progress-bar" id="uploadTestProgressBar">0%</div>
            </div>
            <div id="uploadTestResult" class="speedtest-results"></div>
        </div>
    </div>

    <script>
        // Tab functionality
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and content
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab + 'Tab').classList.add('active');
            });
        });
        
        // File upload with progress bar
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                showMessage('uploadMessage', 'Please select a file to upload', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            const xhr = new XMLHttpRequest();
            
            // Setup progress event
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = Math.round((event.loaded / event.total) * 100);
                    document.getElementById('uploadProgressContainer').style.display = 'block';
                    document.getElementById('uploadProgressBar').style.width = percentComplete + '%';
                    document.getElementById('uploadProgressBar').textContent = percentComplete + '%';
                    
                    // Calculate and display upload speed
                    const elapsedTime = (new Date().getTime() - uploadStartTime) / 1000; // seconds
                    if (elapsedTime > 0) {
                        const bytesPerSecond = event.loaded / elapsedTime;
                        const mbps = (bytesPerSecond / (1024 * 1024)).toFixed(2);
                        document.getElementById('uploadSpeed').textContent = `Current speed: ${mbps} MB/s`;
                    }
                }
            });
            
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        const response = JSON.parse(xhr.responseText);
                        if (response.success) {
                            showMessage('uploadMessage', 'File uploaded successfully! ' + response.upload_speed, 'success');
                            // Reload the page to show the new file
                            setTimeout(() => {
                                window.location.reload();
                            }, 1500);
                        } else {
                            showMessage('uploadMessage', 'Upload failed: ' + response.message, 'error');
                        }
                    } else {
                        showMessage('uploadMessage', 'Upload failed. Server error.', 'error');
                    }
                }
            };
            
            // Start upload
            const uploadStartTime = new Date().getTime();
            xhr.open('POST', '/upload', true);
            xhr.send(formData);
        });
        
        // File download with progress bar
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                
                const filename = this.dataset.filename;
                const fileSize = parseInt(this.dataset.size);
                const progressContainer = document.getElementById('download-' + filename);
                const progressBar = progressContainer.querySelector('.progress-bar');
                
                // Show progress container
                progressContainer.style.display = 'block';
                progressBar.style.width = '0%';
                progressBar.textContent = '0%';
                
                // Create a hidden iframe to avoid page navigation
                const iframe = document.createElement('iframe');
                iframe.style.display = 'none';
                document.body.appendChild(iframe);
                
                // Track download progress
                const downloadStartTime = new Date().getTime();
                let lastCheckedAt = downloadStartTime;
                let lastCheckedSize = 0;
                
                // Poll download progress
                const progressInterval = setInterval(() => {
                    // Simulate progress since browser doesn't provide direct download progress
                    // This is a rough estimation
                    const elapsedMs = new Date().getTime() - downloadStartTime;
                    const estimatedProgress = Math.min(99, Math.round((elapsedMs / (fileSize / 50000)) * 100));
                    
                    progressBar.style.width = estimatedProgress + '%';
                    progressBar.textContent = estimatedProgress + '%';
                    
                    // If we estimate it's likely finished
                    if (estimatedProgress >= 99) {
                        clearInterval(progressInterval);
                        setTimeout(() => {
                            progressBar.style.width = '100%';
                            progressBar.textContent = '100%';
                            
                            // Hide progress bar after a short delay
                            setTimeout(() => {
                                progressContainer.style.display = 'none';
                            }, 1000);
                        }, 500);
                    }
                }, 100);
                
                // Start the download
                iframe.src = '/download/' + encodeURIComponent(filename);
            });
        });
        
        // Download speed test
        function startDownloadTest(sizeMb) {
            // Show progress bar
            const progressContainer = document.getElementById('downloadTestProgress');
            const progressBar = document.getElementById('downloadTestProgressBar');
            progressContainer.style.display = 'block';
            progressBar.style.width = '0%';
            progressBar.textContent = 'Generating test file...';
            
            // First request a test file of the specified size
            fetch('/generate_speedtest_file/' + sizeMb)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Now download the file and measure speed
                        const filename = data.filename;
                        const fileSize = data.size_mb * 1024 * 1024; // Convert MB to bytes
                        
                        const downloadStartTime = new Date().getTime();
                        progressBar.textContent = 'Downloading...';
                        
                        // Create XMLHttpRequest to track download progress
                        const xhr = new XMLHttpRequest();
                        xhr.open('GET', '/speedtest/download/' + encodeURIComponent(filename), true);
                        xhr.responseType = 'blob';
                        
                        xhr.addEventListener('progress', (event) => {
                            if (event.lengthComputable) {
                                const percentComplete = Math.round((event.loaded / event.total) * 100);
                                progressBar.style.width = percentComplete + '%';
                                progressBar.textContent = percentComplete + '%';
                                
                                // Calculate current speed
                                const elapsedSeconds = (new Date().getTime() - downloadStartTime) / 1000;
                                if (elapsedSeconds > 0) {
                                    const mbps = (event.loaded / elapsedSeconds / 1024 / 1024).toFixed(2);
                                    document.getElementById('downloadTestResult').style.display = 'block';
                                    document.getElementById('downloadTestResult').innerHTML = 
                                        `Current Download Speed: <strong>${mbps} MB/s</strong><br>` +
                                        `Downloaded: ${Math.round(event.loaded/1024/1024)}/${Math.round(event.total/1024/1024)} MB`;
                                }
                            }
                        });
                        
                        xhr.addEventListener('load', () => {
                            if (xhr.status === 200) {
                                const downloadTime = (new Date().getTime() - downloadStartTime) / 1000;
                                const speed = fileSize / downloadTime / 1024 / 1024;
                                
                                progressBar.style.width = '100%';
                                progressBar.textContent = '100%';
                                
                                document.getElementById('downloadTestResult').style.display = 'block';
                                document.getElementById('downloadTestResult').innerHTML = 
                                    `Download Speed: <strong>${speed.toFixed(2)} MB/s</strong><br>` +
                                    `Downloaded: ${sizeMb} MB in ${downloadTime.toFixed(2)} seconds`;
                                    
                                // Clean up the test file
                                fetch('/clean_speedtest_files');
                            }
                        });
                        
                        xhr.addEventListener('error', () => {
                            document.getElementById('downloadTestResult').style.display = 'block';
                            document.getElementById('downloadTestResult').innerHTML = 'Download test failed';
                            progressContainer.style.display = 'none';
                        });
                        
                        xhr.send();
                    } else {
                        document.getElementById('downloadTestResult').style.display = 'block';
                        document.getElementById('downloadTestResult').innerHTML = 'Failed to generate test file: ' + data.message;
                        progressContainer.style.display = 'none';
                    }
                })
                .catch(error => {
                    document.getElementById('downloadTestResult').style.display = 'block';
                    document.getElementById('downloadTestResult').innerHTML = 'Error: ' + error;
                    progressContainer.style.display = 'none';
                });
        }
        
        // Upload speed test
        function startUploadTest(sizeMb) {
            // Show progress bar
            const progressContainer = document.getElementById('uploadTestProgress');
            const progressBar = document.getElementById('uploadTestProgressBar');
            progressContainer.style.display = 'block';
            progressBar.style.width = '0%';
            progressBar.textContent = 'Generating test file...';
            
            document.getElementById('uploadTestResult').style.display = 'block';
            document.getElementById('uploadTestResult').innerHTML = 'Preparing test data...';
            
            // Generate random data for upload
            const byteSize = sizeMb * 1024 * 1024;
            const chunkSize = 1024 * 1024; // 1MB chunks
            const totalChunks = Math.ceil(byteSize / chunkSize);
            let generatedSize = 0;
            const chunks = [];
            
            // Generate data in smaller chunks to avoid browser memory issues
            function generateNextChunk() {
                if (generatedSize >= byteSize) {
                    performUploadTest();
                    return;
                }
                
                const currentChunkSize = Math.min(chunkSize, byteSize - generatedSize);
                const chunk = new Uint8Array(currentChunkSize);
                
                // Fill with random data
                window.crypto.getRandomValues(chunk);
                chunks.push(chunk);
                
                generatedSize += currentChunkSize;
                const percentDone = Math.round((generatedSize / byteSize) * 100);
                
                progressBar.style.width = percentDone + '%';
                progressBar.textContent = 'Preparing: ' + percentDone + '%';
                
                // Continue generating data in the next tick to avoid UI freezing
                setTimeout(generateNextChunk, 0);
            }
            
            function performUploadTest() {
                // Create a file from the generated chunks
                const blob = new Blob(chunks);
                const testFile = new File([blob], 'speedtest_upload.bin', { type: 'application/octet-stream' });
                
                // Prepare form data
                const formData = new FormData();
                formData.append('file', testFile);
                formData.append('file_size', byteSize);
                formData.append('start_time', new Date().getTime() / 1000);
                
                const xhr = new XMLHttpRequest();
                
                // Setup progress event
                xhr.upload.addEventListener('progress', (event) => {
                    if (event.lengthComputable) {
                        const percentComplete = Math.round((event.loaded / event.total) * 100);
                        progressBar.style.width = percentComplete + '%';
                        progressBar.textContent = percentComplete + '%';
                        
                        // Calculate current speed
                        const elapsedSeconds = (new Date().getTime() / 1000) - parseFloat(formData.get('start_time'));
                        if (elapsedSeconds > 0) {
                            const mbps = (event.loaded / elapsedSeconds / 1024 / 1024).toFixed(2);
                            document.getElementById('uploadTestResult').innerHTML = 
                                `Current Upload Speed: <strong>${mbps} MB/s</strong><br>` +
                                `Uploaded: ${Math.round(event.loaded/1024/1024)}/${Math.round(event.total/1024/1024)} MB`;
                        }
                    }
                });
                
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            const response = JSON.parse(xhr.responseText);
                            if (response.success) {
                                document.getElementById('uploadTestResult').innerHTML = 
                                    `Upload Speed: <strong>${response.upload_speed_formatted}</strong><br>` +
                                    `Uploaded: ${sizeMb} MB in ${response.duration}`;
                            } else {
                                document.getElementById('uploadTestResult').innerHTML = 'Upload test failed: ' + response.message;
                            }
                        } else {
                            document.getElementById('uploadTestResult').innerHTML = 'Upload test failed. Server error.';
                        }
                    }
                };
                
                // Start upload
                xhr.open('POST', '/speedtest/upload', true);
                xhr.send(formData);
            }
            
            // Start generating data
            generateNextChunk();
        }
        
        // Helper to show messages
        function showMessage(elementId, message, type) {
            const messageElement = document.getElementById(elementId);
            messageElement.textContent = message;
            messageElement.className = 'message ' + type;
            messageElement.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 5000);
        }
        
        // Global upload start time
        let uploadStartTime = 0;
    </script>
</body>
</html>"""
        )

    # Run the app on all network interfaces
    app.run(host="0.0.0.0", port=8282, debug=True)
