# ==========================================================
# Copyright (c) 2026 MGB Not Free Creator 
# All Rights Reserved.
#
# Project      : MGB Not Free Music Telegram Bot
# Powered By   : MGB Not Free Creator
# Type         : API Based Telegram Music Bot
#
# Bot          : @MUSIC1_NOT_FREE_BOT
# Channel      : https://t.me/MUSIC_SUPPORT_69
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
from Elevents import config, logger
from Elevents.helpers import Track, utils


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
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)(&[^\s]*)?"
        )

        # Cache search results (10 minute TTL)
        self.search_cache = {}
        self._download_semaphore = asyncio.Semaphore(5)
        self._max_video_height = config.VIDEO_MAX_HEIGHT

        # Log configuration
        logger.info("=" * 50)
        logger.info("⚡ YouTube Handler Initialized")
        logger.info(f"   API Priority: {'ENABLED' if self.enable_api else 'DISABLED'}")
        if self.enable_api:
            logger.info(f"   API URL: {self.api_url}")
            if self.artistbots_key:
                masked_key = self.artistbots_key[:8] + "..." if len(self.artistbots_key) > 8 else "***"
                logger.info(f"   API Key: {masked_key}")
            else:
                logger.warning("⚠️ No API Key configured!")
        logger.info(f"   Cookies Fallback: {'ENABLED' if self.enable_cookies_fallback else 'DISABLED'}")
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
            cookies_dir = "Elevents/cookies"
            if os.path.exists(cookies_dir):
                for file in os.listdir(cookies_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(file)
            self.checked = True
        
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("⚠️ Cookies are missing; downloads might fail.")
            return None
        
        cookie_file = f"Elevents/cookies/{random.choice(self.cookies)}"
        logger.debug(f"Using cookie file: {cookie_file}")
        return cookie_file

    async def save_cookies(self, urls: list[str]) -> None:
        """Save cookies from URLs to files."""
        logger.info("⚠️ Saving cookies from urls...")
        saved_count = 0
        
        cookies_dir = Path("Elevents/cookies")
        cookies_dir.mkdir(parents=True, exist_ok=True)
        
        for url in urls:
            try:
                path = cookies_dir / f"cookie{random.randint(10000, 99999)}.txt"
                
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
        Download audio/video using MGB Not Free / ArtistBots API (Primary Method).
        """
        if not self.enable_api:
            logger.debug("API is disabled in config")
            return None

        if not self.api_url:
            logger.debug("ARTISTBOTS_API_URL not configured")
            return None

        if "v=" in link:
            video_id = link.split("v=")[1].split("&")[0]
        elif "youtu.be" in link:
            video_id = link.split("/")[-1].split("?")[0]
        else:
            video_id = link

        if not video_id or len(video_id) < 3:
            logger.debug(f"Invalid video ID: {video_id}")
            return None

        DOWNLOAD_DIR = "downloads"
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        file_ext = ".mp4" if video else ".mp3"
        file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}{file_ext}")

        if os.path.exists(file_path):
            logger.debug(f"File already exists: {file_path}")
            return file_path

        try:
            download_type = "video" if video else "audio"
            logger.info(f"📥 [API PRIMARY] Trying API for {video_id} (type: {download_type})")
            
            params = {
                "url": video_id,
                "type": download_type,
            }
            
            if self.artistbots_key:
                params["api_key"] = self.artistbots_key
            else:
                logger.warning("No API key configured!")
                return None
            
            async with aiohttp.ClientSession() as session:
                api_endpoint = f"{self.api_url.rstrip('/')}/download"
                
                async with session.get(
                    api_endpoint,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.api_stream_timeout),
                ) as response:
                    if response.status != 200:
                        try:
                            error_text = await response.text()
                            logger.error(f"API returned status {response.status}: {error_text[:200]}")
                        except Exception:
                            logger.error(f"API returned status {response.status}")
                        return None
                    
                    content_length = response.headers.get('content-length')
                    downloaded = 0
                    last_log = 0
                    
                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(65536):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if downloaded - last_log >= 5 * 1024 * 1024:
                                progress_mb = downloaded / (1024 * 1024)
                                if content_length:
                                    total_mb = int(content_length) / (1024 * 1024)
                                    percent = (downloaded / int(content_length)) * 100
                                    logger.info(f"⏳ Progress: {progress_mb:.1f}/{total_mb:.1f} MB ({percent:.1f}%)")
                                else:
                                    logger.info(f"⏳ Downloaded: {progress_mb:.1f} MB")
                                last_log = downloaded
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        logger.info(f"✅ [API SUCCESS] Downloaded: {file_path} ({file_size_mb:.2f} MB)")
                        return file_path
                    else:
                        logger.error("❌ API download failed: file is empty or not created")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return None

        except asyncio.TimeoutError:
            logger.error(f"❌ API timeout for {video_id}")
            return None
        except Exception as e:
            logger.error(f"❌ API download failed for {video_id}: {type(e).__name__}: {e}")
            return None

    async def download_via_cookies(self, video_id: str, video: bool = False) -> Optional[str]:
        """
        Download audio/video using yt-dlp with cookies (Fallback Method).
        """
        if not self.enable_cookies_fallback:
            logger.debug("Cookies fallback is disabled in config")
            return None

        url = self.base + video_id
        filename_pattern = f"downloads/{video_id}"
        
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
                return video_candidates[0]
        else:
            audio_candidates = [
                f for f in existing_files
                if Path(f).suffix.lower() in {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}
            ]
            if audio_candidates:
                return audio_candidates[0]

        container_fallbacks = [
            f for f in existing_files
            if not Path(f).suffix.lower() in {".part", ".ytdl", ".info.json", ".temp"}
        ]
        if container_fallbacks:
            return container_fallbacks[0]

        cookie_file = self.get_cookies()
        
        ydl_opts = {
            "format": (
                f"bestvideo[height<=?{self._max_video_height}][ext=mp4]+bestaudio[ext=m4a]/"
                f"best[height<=?{self._max_video_height}][ext=mp4]/best"
            ) if video else "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": f"downloads/{video_id}.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "no_warnings": True,
            "quiet": True,
            "extract_flat": False,
        }
        
        if cookie_file and os.path.exists(cookie_file):
            ydl_opts["cookiefile"] = cookie_file

        if not video:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        async with self._download_semaphore:
            try:
                logger.info(f"📥 [COOKIES FALLBACK] Downloading via yt-dlp for {video_id} (video={video})")
                loop = asyncio.get_running_loop()
                def _dl():
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        return ydl.prepare_filename(info)
                
                file_path = await loop.run_in_executor(None, _dl)
                
                if not video:
                    base_path = os.path.splitext(file_path)[0]
                    mp3_path = base_path + ".mp3"
                    if os.path.exists(mp3_path):
                        file_path = mp3_path

                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    logger.info(f"✅ [COOKIES SUCCESS] Downloaded: {file_path}")
                    return file_path
            except Exception as e:
                logger.error(f"❌ yt-dlp cookie download failed for {video_id}: {e}")
        
        return None

    async def download(self, video_id: str, video: bool = False) -> Optional[str]:
        """
        Download video or audio using API first, falling back to yt-dlp cookies.
        """
        link = self.base + video_id if not video_id.startswith("http") else video_id
        
        vid = video_id
        if "v=" in link:
            vid = link.split("v=")[1].split("&")[0]
        elif "youtu.be" in link:
            vid = link.split("/")[-1].split("?")[0]

        existing = self._locate_download_file(vid, video)
        if existing:
            return existing

        # Method 1: API Primary
        file_path = await self.download_via_api(vid, video)
        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path

        # Method 2: Cookies Fallback
        if self.enable_cookies_fallback:
            file_path = await self.download_via_cookies(vid, video)
            if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path

        return None

    async def search(self, query: str, limit: int = 1) -> list:
        try:
            results = VideosSearch(query, limit=limit).result()
            return results.get("result", [])
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}")
            return []
