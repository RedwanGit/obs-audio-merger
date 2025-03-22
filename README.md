# OBS Audio Merger

A Python utility that processes OBS recordings with multiple audio channels, merging them into a single audio track while preserving video quality.

## Overview

When recording with OBS Studio, you often end up with videos containing multiple separate audio tracks (e.g., microphone, desktop audio, browser, etc.). This tool simplifies post-processing by combining all audio channels into a single stereo track, making the recordings more compatible with video editors and media players.

## Features

- Automatically detects the number of audio streams in your OBS recordings
- Merges multiple audio channels into a single stereo track
- Preserves original video quality using stream copying
- Provides a real-time progress bar during processing
- Handles errors gracefully with detailed feedback

## Requirements

- Python 3.6+
- FFmpeg (installed and accessible in PATH)
- Python dependencies:
  - ffmpeg-python
  - (All other dependencies are standard library)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/obs-audio-merger.git
   cd obs-audio-merger
   ```

2. Install required Python packages:
   ```
   pip install ffmpeg-python
   ```

3. Ensure FFmpeg is installed on your system:
   - **Linux**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

## Usage

1. Edit the script to set your OBS recordings folder and filename:
   ```python
   default_folder = "/path/to/your/OBS/recordings/"
   input_filename = "your-recording.mp4"
   ```

2. Run the script:
   ```
   python obs_audio_merger.py
   ```

3. The processed file will be saved in the same directory with "CONVERTED_" prefix.

## Customization

You can modify the script to suit your specific needs:

- Change output file naming convention
- Adjust audio encoding parameters
- Modify the directory structure logic
- Add command-line arguments for greater flexibility

## How It Works

The tool uses FFmpeg's powerful filtering capabilities:

1. It probes the input video to detect all audio streams
2. For videos with multiple audio tracks, it applies the 'amerge' filter to combine them
3. For videos with more than two audio tracks, it uses the 'pan' filter to properly map channels to stereo output
4. The video track is stream-copied to avoid re-encoding and quality loss
5. Audio is encoded to AAC format for maximum compatibility

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- FFmpeg for the powerful underlying media processing
- OBS Studio team for the excellent recording software
