from os import path
import yt_dlp

# Global YouTubeDL options
ytdl = yt_dlp.YoutubeDL(
    {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "format": "bestaudio/best",
        "geo_bypass": True,
        "nocheckcertificate": True,
        "cookiefile": "cookies.txt",
    }
)


def download(url: str, my_hook) -> str:
    ydl_optssx = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "geo_bypass": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": "cookies.txt",
    }

    try:
        info = ytdl.extract_info(url, download=False)

        x = yt_dlp.YoutubeDL(ydl_optssx)
        x.add_progress_hook(my_hook)
        x.download([url])

        file_path = path.join("downloads", f"{info['id']}.{info['ext']}")
        return file_path

    except Exception as e:
        print(f"Download error: {e}")
        return None