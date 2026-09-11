"""FFmpeg discovery, execution, media probing, and custom error types."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class FFmpegNotFoundError(Exception):
    """Raised when FFmpeg executable cannot be located on host system."""
    pass


class AssemblyError(Exception):
    """Raised when FFmpeg media assembly, concatenation, or filtergraph fails."""
    pass


def get_ffmpeg_binary() -> str:
    """Locate FFmpeg executable from environment, system PATH, or bundled package."""
    # 1. Environment variable override
    env_path = os.environ.get("FFMPEG_PATH")
    if env_path and Path(env_path).is_file():
        return env_path

    # 2. System PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 3. Bundled imageio_ffmpeg
    try:
        import imageio_ffmpeg
        bundled_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled_exe and Path(bundled_exe).is_file():
            return bundled_exe
    except ImportError:
        pass

    raise FFmpegNotFoundError(
        "FFmpeg executable not found. Ensure FFmpeg is installed and added to PATH, "
        "set the FFMPEG_PATH environment variable, or install 'imageio-ffmpeg'."
    )


def run_ffmpeg(
    args: List[str],
    ffmpeg_bin: Optional[str] = None,
    timeout: float = 180.0,
) -> subprocess.CompletedProcess:
    """Execute FFmpeg command with standard error capture and exception handling.

    Args:
        args: Command-line arguments passed to FFmpeg (excluding the executable itself).
        ffmpeg_bin: Optional explicit path to FFmpeg binary.
        timeout: Subprocess timeout in seconds.

    Returns:
        CompletedProcess instance on success.

    Raises:
        FFmpegNotFoundError: If FFmpeg cannot be located.
        AssemblyError: If FFmpeg returns a non-zero exit code or times out.
    """
    binary = ffmpeg_bin or get_ffmpeg_binary()
    cmd = [binary] + args

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as err:
        raise AssemblyError(f"FFmpeg execution timed out after {timeout} seconds: {' '.join(cmd)}") from err
    except Exception as err:
        raise AssemblyError(f"Failed to execute FFmpeg command: {err}") from err

    if result.returncode != 0:
        stderr_snippet = result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
        raise AssemblyError(
            f"FFmpeg command failed with exit code {result.returncode}.\n"
            f"Command: {' '.join(cmd)}\n"
            f"Error details:\n{stderr_snippet.strip()}"
        )

    return result


def probe_media(file_path: Path | str, ffmpeg_bin: Optional[str] = None) -> Dict[str, Any]:
    """Probe video/audio media file using FFmpeg stderr metadata inspection.

    Args:
        file_path: Path to the media file.
        ffmpeg_bin: Optional explicit path to FFmpeg binary.

    Returns:
        Dictionary with:
            - duration: float (seconds)
            - width: Optional[int]
            - height: Optional[int]
            - fps: Optional[float]
            - video_codec: Optional[str]
            - has_audio: bool
            - file_size_bytes: int
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Media file not found: {path}")

    file_size = path.stat().st_size
    info: Dict[str, Any] = {
        "file_path": str(path),
        "file_size_bytes": file_size,
        "duration": 0.0,
        "width": None,
        "height": None,
        "fps": None,
        "video_codec": None,
        "has_audio": False,
    }

    try:
        binary = ffmpeg_bin or get_ffmpeg_binary()
        # Run ffmpeg -i <path> (returns non-zero because no output is specified, which is expected)
        cmd = [binary, "-i", str(path)]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        output = result.stderr

        # Parse duration: Duration: 00:00:01.50, start: 0.000000, bitrate: 21 kb/s
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
        if dur_match:
            hours, minutes, seconds = dur_match.groups()
            info["duration"] = round(int(hours) * 3600 + int(minutes) * 60 + float(seconds), 3)

        # Parse video stream: Stream #0:0[...]: Video: h264 (...), yuv420p, 1280x720 ..., 30 fps
        vid_match = re.search(r"Stream #\d+:\d+.*?: Video: ([^,\s]+)", output)
        if vid_match:
            info["video_codec"] = vid_match.group(1).lower()

        res_match = re.search(r",\s*(\d{2,5})x(\d{2,5})", output)
        if res_match:
            info["width"] = int(res_match.group(1))
            info["height"] = int(res_match.group(2))

        fps_match = re.search(r",\s*(\d+(?:\.\d+)?)\s*fps", output)
        if fps_match:
            info["fps"] = float(fps_match.group(1))

        # Check for audio stream: Stream #0:1[...]: Audio: aac (...), 44100 Hz, mono
        aud_match = re.search(r"Stream #\d+:\d+.*?: Audio: ([^,\s]+)", output)
        if aud_match:
            info["has_audio"] = True
            info["audio_codec"] = aud_match.group(1).lower()
        elif "Audio:" in output:
            info["has_audio"] = True

    except FFmpegNotFoundError:
        # Fallback when FFmpeg is not present
        pass
    except Exception:
        # If parsing encounters an anomaly, preserve default info
        pass

    return info


def verify_media_decodable(file_path: Path | str, ffmpeg_bin: Optional[str] = None, timeout: float = 30.0) -> bool:
    """Verify that a media file is decodable without fatal container or stream corruptions.

    Executes FFmpeg decoding frames into the null muxer. Returns True if returncode is 0.

    Args:
        file_path: Path to the media file to verify.
        ffmpeg_bin: Optional explicit path to FFmpeg binary.
        timeout: Subprocess timeout in seconds.

    Returns:
        True if the file can be fully decoded without fatal errors, False otherwise.
    """
    path = Path(file_path)
    if not path.is_file():
        return False

    try:
        binary = ffmpeg_bin or get_ffmpeg_binary()
        cmd = [binary, "-v", "error", "-i", str(path), "-f", "null", "-"]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False
