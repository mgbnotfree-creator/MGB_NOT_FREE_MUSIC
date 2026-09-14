# ==========================================================
# Copyright (c) 2026 MGB NOT FREE 
# All Rights Reserved.
#
# Project      : mgb not free
# Powered By   : MGB NOT FREE 
# Type         : API Based Telegram Music Bot
#
# Bot          : @RIYA_MUSIC_X_BOT
# Channel      : https://t.me/RIYA_MUSIC_BOT_786
# GitHub       : https://github.com/mgbnotfree-creator/MGB_NOT_FREE_MUSIC
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

import os
import re
import glob
import time
import yt_dlp
import random
import asyncio
import aiohttp
from dataclasses import replace
from pathlib import Path
from typing import Optional, Union

from pyrogram import enums, types
from py_yt import Playlist, VideosSearch
from Elevenyts import config, logger
from Elevenyts.helpers import Track, utils


class YouTube:
    def __init__(self):
        """Initialize YouTube handler with configuration and caching."""
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.warned = False

        # Get API configuration from config
        self.api_url = config.ARTISTBOTS_API_URL
        self.artistbots_key = config.ARTISTBOTS_KEY
        self.enable_api = config.ENABLE_API
        self.enable_cookies_fallback = config.ENABLE_COOKIES_FALLBACK
        self.api_timeout = config.API_TIMEOUT
        self.api_stream_timeout = config.API_STREAM_TIMEOUT

        # Regular expression to match YouTube URLs
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|live/|embed/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

        # Cache search results (10 minute TTL)
        self.search_cache = {}
        self._download_semaphore = asyncio.Semaphore(5)
        self._max_video_height = config.VIDEO_MAX_HEIGHT

        # Log configuration
        logger.info("=" * 50)
        logger.info("📡 YouTube Handler Initialized")
        logger.info(f"🎯 API Priority: {'ENABLED' if self.enable_api else 'DISABLED'}")
        if self.enable_api:
            logger.info(f"🔗 API URL: {self.api_url}")
            if self.artistbots_key:
                masked_key = self.artistbots_key[:8] + "..." if len(self.artistbots_key) > 8 else "***"
                logger.info(f"🔑 API Key: {masked_key}")
            else:
                logger.warning("⚠️ No API Key configured!")
        logger.info(f"🍪 Cookies Fallback: {'ENABLED' if self.enable_cookies_fallback else 'DISABLED'}")
        logger.info("=" * 50)

    def _locate_download_file(self, video_id: str, video: bool = False) -> Optional[str]:
        """Locate any completed download file for a video id."""
        pattern = f"downloads/{video_id}*"
        candidates = sorted([
            path for path in glob.glob(pattern)
            if not path.endswith((".part", ".ytdl", ".info.json", ".temp"))
        ])

        video_exts = {".mp4", ".mkv", ".webm", ".mov"}
        audio_exts = {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}

        if video:
            for path in candidates:
                if os.path.isdir(path):
                        continue
                if Path(path).suffix.lower() in video_exts:
                    return path
        else:
            for path in candidates:
                if os.path.isdir(path):
                    continue
                if Path(path).suffix.lower() in audio_exts:
                    return path

        for path in candidates:
            if os.path.isdir(path):
                continue
            return path
        return None

    def get_cookies(self):
        """Get random cookie file from cookies directory."""
        if not self.checked:
            cookies_dir = "Elevenyts/cookies"
            if os.path.exists(cookies_dir):
                for file in os.listdir(cookies_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(file)
            self.checked = True
        
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("🍪 Cookies are missing; downloads might fail.")
            return None
        
        cookie_file = f"Elevenyts/cookies/{random.choice(self.cookies)}"
        logger.debug(f"Using cookie file: {cookie_file}")
        return cookie_file

    async def save_cookies(self, urls: list[str]) -> None:
        """Save cookies from URLs to files."""
        logger.info("🍪 Saving cookies from urls...")
        saved_count = 0
        
        # Create cookies directory if not exists
        cookies_dir = Path("Elevenyts/cookies")
        cookies_dir.mkdir(parents=True, exist_ok=True)
        
        for url in urls:
            try:
                # Generate unique filename
                path = cookies_dir / f"cookie{random.randint(10000, 99999)}.txt"
                
                # Convert to raw URL if needed
                if "pastebin.com" in url:
                    link = url.replace("pastebin.com", "pastebin.com/raw")
                elif "batbin.me" in url:
                    link = url.replace("batbin.me", "batbin.me/raw")
                else:
                    link = url
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(link, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status != 200:
                            logger.error(f"❌ Cookie download failed: HTTP {resp.status} from {url}")
                            continue
                        
                        content = await resp.read()
                        if not content or len(content) < 50:
                            logger.error(f"❌ Cookie file empty or invalid from {url}")
                            continue
                        
                        # Save cookie file
                        with open(path, "wb") as fw:
                            fw.write(content)
                        
                        if path.exists() and path.stat().st_size > 0:
                            saved_count += 1
                            cookie_filename = path.name
                            if cookie_filename not in self.cookies:
                                self.cookies.append(cookie_filename)
                            logger.info(f"✅ Saved: {cookie_filename} ({len(content)} bytes)")
                        
            except asyncio.TimeoutError:
                logger.error(f"❌ Cookie download timeout from {url}")
            except Exception as e:
                logger.error(f"❌ Cookie download error from {url}: {e}")
        
        self.checked = True
        
        if saved_count > 0:
            logger.info(f"✅ Cookies saved successfully! ({saved_count} file(s))")
        else:
            logger.error("❌ No cookies saved! Check COOKIE_URL in .env.")

    async def download_via_api(self, link: str, video: bool = False) -> Optional[str]:
        """
        Download audio/video using API (Primary Method).
        
        Args:
            link: YouTube URL or video ID
            video: True for video download, False for audio download
        
        Returns:
            Path to downloaded file or None if failed
        """
        if not self.enable_api:
            logger.debug("API is disabled in config")
            return None

        if not self.api_url:
            logger.debug("ARTISTBOTS_API_URL not configured")
            return None

        # Extract video ID from URL
        if "v=" in link:
            video_id = link.split("v=")[-1].split("&")[0]
        elif "youtu.be" in link:
            video_id = link.split("/")[-1].split("?")[0]
        else:
            video_id = link

        if not video_id or len(video_id) < 3:
            logger.debug(f"Invalid video ID: {video_id}")
            return None

        DOWNLOAD_DIR = "downloads"
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        # Set file extension based on type
        file_ext = ".mp4" if video else ".mp3"
        file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}{file_ext}")

        # Check if already downloaded
        if os.path.exists(file_path):
            logger.debug(f"File already exists: {file_path}")
            return file_path

        try:
            download_type = "video" if video else "audio"
            logger.info(f"🚀 [API PRIMARY] Trying API for {video_id} (type: {download_type})")
            
            # Prepare API parameters
            params = {
                "url": video_id,
                "type": download_type,
            }
            
            # Add API key if available
            if self.artistbots_key:
                params["api_key"] = self.artistbots_key
                logger.debug(f"Using API key: {self.artistbots_key[:8]}...")
            else:
                logger.warning("No API key configured!")
                return None
            
            async with aiohttp.ClientSession() as session:
                api_endpoint = f"{self.api_url.rstrip('/')}/download"
                logger.debug(f"Calling API: {api_endpoint}")
                
                async with session.get(
                    api_endpoint,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.api_stream_timeout),
                ) as response:
                    logger.debug(f"API response status: {response.status}")
                    
                    if response.status != 200:
                        try:
                            error_text = await response.text()
                            logger.error(f"API returned status {response.status}: {error_text[:200]}")
                        except:
                            logger.error(f"API returned status {response.status}")
                        return None
                    
                    # Handle direct binary download
                    logger.info(f"📥 Downloading {download_type} via API for {video_id}...")
                    
                    # Get total file size if available
                    content_length = response.headers.get('content-length')
                    if content_length:
                        file_size_mb = int(content_length) / (1024 * 1024)
                        logger.info(f"📦 File size: {file_size_mb:.2f} MB")
                    
                    # Download file with progress
                    downloaded = 0
                    last_log = 0
                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(65536):  # 64KB chunks
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Log progress every 5MB
                            if downloaded - last_log >= 5 * 1024 * 1024:
                                progress_mb = downloaded / (1024 * 1024)
                                if content_length:
                                    total_mb = int(content_length) / (1024 * 1024)
                                    percent = (downloaded / int(content_length)) * 100
                                    logger.info(f"📊 Progress: {progress_mb:.1f}/{total_mb:.1f} MB ({percent:.1f}%)")
                                else:
                                    logger.info(f"📊 Downloaded: {progress_mb:.1f} MB")
                                last_log = downloaded
                    
                    # Verify file was created and has content
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        logger.info(f"✅ [API SUCCESS] Downloaded: {file_path} ({file_size_mb:.2f} MB)")
                        return file_path
                    else:
                        logger.error(f"❌ API download failed: file is empty or not created")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return None

        except asyncio.TimeoutError:
            logger.error(f"⏱ API timeout for {video_id} after {self.api_stream_timeout} seconds")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"🌐 API client error for {video_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ API download failed for {video_id}: {type(e).__name__}: {e}")
            return None

    async def download_via_cookies(self, video_id: str, video: bool = False) -> Optional[str]:
        """
        Download audio/video using yt-dlp with cookies (Fallback Method).
        
        Args:
            video_id: YouTube video ID
            video: True for video download, False for audio download
        
        Returns:
            Path to downloaded file or None if failed
        """
        if not self.enable_cookies_fallback:
            logger.debug("Cookies fallback is disabled in config")
            return None

        url = self.base + video_id
        filename_pattern = f"downloads/{video_id}"
        
        # Check existing files
        existing_files = [
            f for f in glob.glob(f"{filename_pattern}.*")
            if not f.endswith('.part')
        ]
        
        if video:
            video_candidates = [
                f for f in existing_files
                if Path(f).suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}
            ]
            if video_candidates:
                logger.debug(f"Found existing video file: {video_candidates[0]}")
                return video_candidates[0]
        else:
            audio_candidates = [
                f for f in existing_files
                if Path(f).suffix.lower() in {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}
            ]
            if audio_candidates:
                logger.debug(f"Found existing audio file: {audio_candidates[0]}")
                return audio_candidates[0]

        container_fallbacks = [
            f for f in existing_files
            if Path(f).suffix.lower() not in {".part", ".ytdl", ".info.json", ".temp"}
        ]
        if container_fallbacks:
            return container_fallbacks[0]

        cookie_file = self.get_cookies()
        logger.info(f"🚀 [COOKIES FALLBACK] Downloading {'video' if video else 'audio'} for {video_id}...")

        opts = {
            "format": f"bestvideo[height<=?{self._max_video_height}]+bestaudio/best" if video else "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": f"{filename_pattern}.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
        }
        
        if not video:
            opts["extract_audio"] = True

        if cookie_file:
            opts["cookiefile"] = cookie_file

        try:
            loop = asyncio.get_event_loop()
            def extract():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=True)
            
            info = await loop.run_in_executor(None, extract)
            ext = info.get("ext", "mp4" if video else "m4a")
            downloaded_file = f"{filename_pattern}.{ext}"
            
            if os.path.exists(downloaded_file):
                logger.info(f"✅ [COOKIES SUCCESS] Downloaded: {downloaded_file}")
                return downloaded_file
            return None
        except Exception as e:
            logger.error(f"❌ yt-dlp download error for {video_id}: {e}")
            return None

    async def download(self, video_id: str, is_live: bool = False, video: bool = False) -> Optional[str]:
        """Main download method: Try API first, then cookies fallback."""
        async with self._download_semaphore:
            # 1. API Method
            result = await self.download_via_api(video_id, video)
            if result:
                return result
            
            # 2. Cookies Fallback
            result = await self.download_via_cookies(video_id, video)
            return result

    async def get_track(self, video_id: str) -> Optional[Track]:
        """Fetch video metadata and return as Track object."""
        try:
            loop = asyncio.get_event_loop()
            
            def get_info():
                opts = {
                    "format": "bestaudio/best",
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": True,
                }
                cookie = self.get_cookies()
                if cookie:
                    opts["cookiefile"] = cookie
                    
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

            info = await loop.run_in_executor(None, get_info)
            if not info:
                return None
            
            duration_sec = info.get("duration", 0)
            
            return Track(
                id=info.get("id"),
                title=info.get("title", "Unknown Title")[:50],
                duration=utils.format_time(duration_sec),
                duration_sec=duration_sec,
                url=info.get("webpage_url", f"https://www.youtube.com/watch?v={video_id}"),
                thumb=info.get("thumbnail", config.DEFAULT_THUMB),
                user=info.get("uploader", "Unknown Artist")
            )
        except Exception as e:
            logger.error(f"Error fetching track metadata for {video_id}: {e}")
            return None
        
