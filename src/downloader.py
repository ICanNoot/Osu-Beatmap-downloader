"""Download manager for beatmap files."""

import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import time


class DownloadStatus(Enum):
    """Status of a download."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """A download task."""
    beatmapset_id: int
    beatmap_id: int
    title: str
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    error: Optional[str] = None
    file_path: Optional[str] = None


class MirrorAPI:
    """Mirror API endpoints."""

    CATBOY = "catboy"
    NERINYAN = "nerinyan"

    MIRRORS = {
        CATBOY: {
            "osu_file": "https://catboy.best/osu/{beatmap_id}",
            "osz_file": "https://catboy.best/d/{beatmapset_id}",
            "name": "catboy.best"
        },
        NERINYAN: {
            "osu_file": "https://api.nerinyan.moe/osu/{beatmap_id}",
            "osz_file": "https://api.nerinyan.moe/d/{beatmapset_id}",
            "name": "nerinyan.moe"
        }
    }

    @classmethod
    def get_osu_url(cls, beatmap_id: int, mirror: str = CATBOY) -> str:
        """Get URL for .osu file."""
        return cls.MIRRORS[mirror]["osu_file"].format(beatmap_id=beatmap_id)

    @classmethod
    def get_osz_url(cls, beatmapset_id: int, mirror: str = CATBOY) -> str:
        """Get URL for .osz file."""
        return cls.MIRRORS[mirror]["osz_file"].format(beatmapset_id=beatmapset_id)


class DownloadManager:
    """Manages beatmap downloads."""

    def __init__(
        self,
        cache_path: str,
        download_path: str,
        mirror: str = MirrorAPI.CATBOY,
        max_concurrent: int = 3
    ):
        """Initialize download manager.

        Args:
            cache_path: Path to cache .osu files
            download_path: Path to save .osz files
            mirror: Mirror to use for downloads
            max_concurrent: Maximum concurrent downloads
        """
        self.cache_path = Path(cache_path)
        self.download_path = Path(download_path)
        self.mirror = mirror
        self.max_concurrent = max_concurrent
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._cancelled = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=300, connect=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def cancel_all(self) -> None:
        """Cancel all pending downloads."""
        self._cancelled = True

    def reset_cancellation(self) -> None:
        """Reset cancellation flag."""
        self._cancelled = False

    async def fetch_osu_file(
        self,
        beatmap_id: int,
        force_refresh: bool = False
    ) -> Optional[str]:
        """Fetch .osu file for PP calculation.

        Args:
            beatmap_id: The beatmap ID
            force_refresh: Force re-download even if cached

        Returns:
            Path to the .osu file or None if failed
        """
        cache_file = self.cache_path / f"{beatmap_id}.osu"

        # Check cache
        if cache_file.exists() and not force_refresh:
            return str(cache_file)

        # Download from mirror
        url = MirrorAPI.get_osu_url(beatmap_id, self.mirror)

        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()

                    # Save to cache
                    self.cache_path.mkdir(parents=True, exist_ok=True)
                    async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                        await f.write(content)

                    return str(cache_file)
                else:
                    print(f"Failed to fetch .osu file: HTTP {response.status}")
                    return None

        except Exception as e:
            print(f"Error fetching .osu file for {beatmap_id}: {e}")
            return None

    async def download_osz(
        self,
        task: DownloadTask,
        progress_callback: Optional[Callable[[DownloadTask], None]] = None
    ) -> bool:
        """Download .osz file for a beatmapset.

        Args:
            task: Download task
            progress_callback: Callback for progress updates

        Returns:
            True if successful
        """
        if self._cancelled:
            task.status = DownloadStatus.CANCELLED
            return False

        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)

        async with self._semaphore:
            if self._cancelled:
                task.status = DownloadStatus.CANCELLED
                return False

            task.status = DownloadStatus.DOWNLOADING
            task.progress = 0.0
            if progress_callback:
                progress_callback(task)

            url = MirrorAPI.get_osz_url(task.beatmapset_id, self.mirror)
            # Sanitize filename
            safe_title = "".join(c for c in task.title if c.isalnum() or c in " -_()[]").strip()
            filename = f"{task.beatmapset_id} {safe_title}.osz"
            file_path = self.download_path / filename

            try:
                session = await self._get_session()
                async with session.get(url) as response:
                    if response.status != 200:
                        task.status = DownloadStatus.FAILED
                        task.error = f"HTTP {response.status}"
                        if progress_callback:
                            progress_callback(task)
                        return False

                    # Get content length for progress
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0

                    self.download_path.mkdir(parents=True, exist_ok=True)
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if self._cancelled:
                                task.status = DownloadStatus.CANCELLED
                                if progress_callback:
                                    progress_callback(task)
                                return False

                            await f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                task.progress = (downloaded / total_size) * 100
                                if progress_callback:
                                    progress_callback(task)

                    task.status = DownloadStatus.COMPLETED
                    task.progress = 100.0
                    task.file_path = str(file_path)
                    if progress_callback:
                        progress_callback(task)
                    return True

            except asyncio.CancelledError:
                task.status = DownloadStatus.CANCELLED
                if progress_callback:
                    progress_callback(task)
                return False
            except Exception as e:
                task.status = DownloadStatus.FAILED
                task.error = str(e)
                if progress_callback:
                    progress_callback(task)
                return False

    async def download_batch(
        self,
        tasks: List[DownloadTask],
        progress_callback: Optional[Callable[[DownloadTask], None]] = None,
        batch_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[DownloadTask]:
        """Download multiple beatmapsets.

        Args:
            tasks: List of download tasks
            progress_callback: Callback for individual task progress
            batch_callback: Callback for batch progress (completed, total)

        Returns:
            List of completed tasks
        """
        self.reset_cancellation()
        completed = 0

        async def download_with_tracking(task: DownloadTask) -> DownloadTask:
            nonlocal completed
            await self.download_osz(task, progress_callback)
            completed += 1
            if batch_callback:
                batch_callback(completed, len(tasks))
            return task

        # Create tasks for concurrent download
        download_coros = [download_with_tracking(task) for task in tasks]
        results = await asyncio.gather(*download_coros, return_exceptions=True)

        return tasks
