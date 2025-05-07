# Local Network File Sharing Server

A simple yet powerful Python-based file sharing server for local networks with speed testing capabilities.

![File Sharing Demo](https://via.placeholder.com/800x400?text=Local+File+Sharing+Server)

## Features

- **Easy File Sharing**
  - Upload and download files across your local network
  - Keep track of download counts for each file
  - Delete files when no longer needed
  - Handles files up to 500MB

- **Real-time Progress Tracking**
  - Loading bars for file uploads and downloads
  - Live transfer speed indicators
  - Success/error notifications

- **Network Speed Testing**
  - Test download speeds (5MB, 10MB, 25MB, or 50MB files)
  - Test upload speeds (5MB, 10MB, 25MB, or 50MB files)
  - Get accurate measurements of your connection to the server
  - Real-time speed monitoring during tests

- **User-Friendly Interface**
  - Clean, responsive design
  - Tabbed interface for file sharing and speed testing
  - File information including size and download count

## Installation

### Prerequisites
- Python 3.6 or higher
- Flask

### Setup

1. Clone this repository or download the `file_sharing_app.py` file

2. Install required dependencies:
   ```bash
   pip install flask
   ```

3. Run the application:
   ```bash
   python file_sharing_app.py
   ```

4. The server will start on port 5000. You'll see output similar to:
   ```
   * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
   ```

## Usage

### Accessing the Server

- **From the host computer**:
  - Open a web browser and navigate to `http://localhost:5000`

- **From other devices on your network**:
  - Find your computer's IP address (e.g., 192.168.1.x)
  - From other devices on the same network, open a browser and go to `http://[YOUR_IP_ADDRESS]:5000`

### File Sharing

1. **Upload Files**:
   - Click "Choose File" to select a file from your device
   - Click "Upload" to start the upload process
   - Watch the progress bar and speed indicator

2. **Download Files**:
   - Browse the list of available files
   - Click "Download" next to the file you want
   - Watch the progress bar during download

3. **Delete Files**:
   - Click "Delete" next to a file to remove it from the server
   - Confirm the deletion when prompted

### Speed Testing

1. **Test Download Speed**:
   - Go to the "Speed Test" tab
   - Choose a file size (5MB, 10MB, 25MB, or 50MB)
   - Click the corresponding button to start the test
   - View real-time progress and final speed results

2. **Test Upload Speed**:
   - Go to the "Speed Test" tab
   - Choose a file size (5MB, 10MB, 25MB, or 50MB)
   - Click the corresponding button under "Upload Speed Test"
   - View real-time progress and final speed results

## Project Structure

When running the application, the following directories and files will be created:

- `uploads/` - Directory containing all uploaded files
- `speedtest/` - Directory containing temporary speed test files
- `download_stats.json` - File tracking download counts
- `templates/` - Directory containing the HTML template

## Technical Details

- Built with Flask, a lightweight Python web framework
- Uses XMLHttpRequest for tracking upload/download progress
- Employs JavaScript for client-side progress visualization
- Automatically cleans up temporary speed test files
- Tracks download statistics in a JSON file

## Security Notes

- This server is intended for use on trusted local networks only
- No authentication is implemented
- No encryption is used for data transfer
- Not recommended for use on public networks

## Customization

You can modify the following settings in the code:

- `UPLOAD_FOLDER` - Path where uploaded files are stored
- `SPEEDTEST_FOLDER` - Path where speed test files are generated
- `app.config['MAX_CONTENT_LENGTH']` - Maximum file size allowed (default: 500MB)

## Troubleshooting

- **Server won't start**: Make sure port 5000 is not in use by another application
- **Can't access from other devices**: Check firewall settings and make sure devices are on the same network
- **Upload/download failures**: Check available disk space and file permissions

## License

This project is open source and available under the MIT License.

## Acknowledgements

- Built with [Flask](https://flask.palletsprojects.com/)
- Uses modern JavaScript for progress tracking
