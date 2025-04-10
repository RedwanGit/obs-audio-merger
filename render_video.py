import ffmpeg
import os
import subprocess
import re
import time
import sys

def render_video():
    # Default folder path
    default_folder = "/path/to/video/directory/"

    # Hard-coded input file name
    input_filename = "file-name.mp4"

    # Complete input file path
    input_file = os.path.join(default_folder, input_filename)

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file does not exist: {input_file}")
        return

    # Generate output file name
    directory, filename = os.path.split(input_file)
    output_file = os.path.join(directory, "CONVERTED_" + filename)

    try:
        # Get video information
        probe = ffmpeg.probe(input_file)
        duration = float(probe['format']['duration'])
        
        # Count audio streams
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        num_audio_streams = len(audio_streams)
        
        print(f"Detected {num_audio_streams} audio stream(s) in the input file")
        
        # Additional debugging information
        for i, stream in enumerate(audio_streams):
            print(f"Audio stream {i}: channels={stream.get('channels', 'unknown')}, codec={stream.get('codec_name', 'unknown')}")
        
        # Build ffmpeg command
        input_stream = ffmpeg.input(input_file)
        video_stream = input_stream.video
        
        # Handle audio streams based on count
        if num_audio_streams <= 1:
            # If there's only one audio stream, just use it directly
            audio_stream = input_stream.audio
            output = ffmpeg.output(
                video_stream, 
                audio_stream, 
                output_file, 
                vcodec='copy',
                acodec='aac',
                strict='experimental',
                # Ensure standard audio parameters for cross-platform compatibility
                ar='48000',        # Sample rate: 48kHz is standard for video
                ac='2',            # 2 channels (stereo)
                ab='192k'          # Bitrate
            ).overwrite_output()
        else:
            # If there are multiple audio streams, merge them with clearer channel mapping
            merged_audio = ffmpeg.filter(
                [input_stream[f'a:{i}'] for i in range(num_audio_streams)],
                'amerge',
                inputs=num_audio_streams
            )
            
            # For 2 audio streams, use a simpler approach - just merge them
            if num_audio_streams == 2:
                # Simple stereo output - just use the merged streams directly
                stereo_audio = merged_audio
            else:
                # For more than 2 streams, use explicit channel mapping
                # Dynamically create the channel mapping based on actual number of channels
                # First half of channels go to left, second half to right
                left_channels = []
                right_channels = []
                
                for i in range(num_audio_streams):
                    if i % 2 == 0:  # Even channels go to left
                        left_channels.append(f'c{i}')
                    else:  # Odd channels go to right
                        right_channels.append(f'c{i}')
                
                # Create the channel mapping strings
                left_map = '+'.join(left_channels) if left_channels else 'c0'
                right_map = '+'.join(right_channels) if right_channels else 'c1'
                
                print(f"Using channel mapping: Left={left_map}, Right={right_map}")
                
                # Apply the pan filter with dynamic mapping
                stereo_audio = merged_audio.filter(
                    'pan', 
                    channels=2,
                    c0=left_map,
                    c1=right_map
                )
            
            output = ffmpeg.output(
                video_stream, 
                stereo_audio, 
                output_file, 
                vcodec='copy',
                acodec='aac',
                strict='experimental',
                # Ensure standard audio parameters for cross-platform compatibility  
                ar='48000',        # Sample rate: 48kHz is standard for video
                ac='2',            # 2 channels (stereo)
                ab='192k'          # Bitrate
            ).overwrite_output()
        
        cmd = ffmpeg.compile(output)
        
        # Print the command for debugging
        print("Running FFmpeg command:")
        print(" ".join(cmd))
        
        # Use custom progress bar instead of tqdm
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        time_pattern = re.compile(r'time=(\d+):(\d+):(\d+)\.(\d+)')
        start_time = time.time()
        last_update = 0
        
        # Create a custom single-line progress bar
        print("Starting video rendering...")
        
        for line in iter(process.stderr.readline, ''):
            # Print any error lines to help with debugging
            if "Error" in line or "Invalid" in line:
                print(f"FFmpeg message: {line.strip()}")
                
            matches = time_pattern.search(line)
            if matches:
                # Calculate progress
                hrs, mins, secs, ms = map(int, matches.groups())
                current_time = hrs * 3600 + mins * 60 + secs + ms / 100
                progress = min(100, current_time / duration * 100)
                
                # Only update every half second to avoid excessive output
                current = time.time()
                if current - last_update >= 0.5:
                    # Calculate time stats
                    elapsed = current - start_time
                    if progress > 0:
                        remaining = elapsed * (100 - progress) / progress
                    else:
                        remaining = 0
                    
                    # Format elapsed and remaining time
                    elapsed_min, elapsed_sec = divmod(int(elapsed), 60)
                    remaining_min, remaining_sec = divmod(int(remaining), 60)
                    
                    # Create the progress bar
                    bar_length = 30
                    filled_length = int(bar_length * progress / 100)
                    bar = '█' * filled_length + ' ' * (bar_length - filled_length)
                    
                    # Create the progress text (fixed width to ensure consistent clearing)
                    progress_text = f"Rendering: {progress:5.1f}% |{bar}| {elapsed_min:02d}:{elapsed_sec:02d}/{remaining_min:02d}:{remaining_sec:02d}"
                    
                    # Use carriage return only (no newline) to update in place
                    sys.stdout.write('\r' + progress_text.ljust(100))
                    sys.stdout.flush()
                    
                    last_update = current
        
        # Wait for process to complete
        process.wait()
        
        # Add a newline after the progress is complete
        print()  # This adds a newline after the progress bar
        
        # Check if process completed successfully
        if process.returncode == 0:
            print(f"Rendered video saved as: {output_file}")
            if num_audio_streams > 1:
                print(f"Successfully merged {num_audio_streams} audio channels into a stereo track compatible with Windows and Linux")
            
            # Optional: Also create a fallback version with PCM audio if needed
            create_fallback = False  # Set to True if you want a fallback version
            if create_fallback and num_audio_streams > 1:
                fallback_file = os.path.join(directory, "FALLBACK_" + filename)
                print(f"Creating fallback version with PCM audio: {fallback_file}")
                
                # Create a fallback with PCM audio (highly compatible)
                fallback_cmd = [
                    "ffmpeg", "-i", output_file,
                    "-c:v", "copy", 
                    "-c:a", "pcm_s16le",  # PCM audio (very compatible)
                    "-ar", "44100",        # CD quality
                    "-ac", "2",            # Stereo
                    fallback_file
                ]
                
                subprocess.run(fallback_cmd)
                print(f"Fallback video created: {fallback_file}")
        else:
            print(f"Error: ffmpeg process exited with code {process.returncode}")
            print("Check the output above for more details on the error")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Run the function
if __name__ == "__main__":
    render_video()
