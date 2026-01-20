"""Main application logic for osu! Beatmap Downloader."""

import asyncio
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, replace

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from .config import ConfigManager, Config
from .api_client import OsuApiClient, SearchFilters, BeatmapInfo, OsuMode
from .pp_calculator import PPCalculator
from .downloader import DownloadManager, DownloadTask, DownloadStatus, MirrorAPI
from .gui import MainWindow, ConfigDialog


class SearchWorker(QThread):
    """Worker thread for beatmap search and PP calculation."""

    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current, total
    pp_calculated = pyqtSignal(int, float)  # beatmap_id, pp

    def __init__(
        self,
        api_client: OsuApiClient,
        filters: SearchFilters,
        pp_range: tuple[int, int],
        max_results: int,
        cache_path: str,
        mirror: str = MirrorAPI.CATBOY
    ):
        super().__init__()
        self.api_client = api_client
        self.filters = filters
        self.pp_range = pp_range
        self.max_results = max_results
        self.cache_path = cache_path
        self.mirror = mirror
        self._cancelled = False

    def cancel(self):
        """Cancel the search."""
        self._cancelled = True

    def run(self):
        """Run the search in a separate thread."""
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            results = loop.run_until_complete(self._search_and_filter())
            loop.close()

            if not self._cancelled:
                self.finished.emit(results)

        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))

    async def _search_and_filter(self) -> List[BeatmapInfo]:
        """Search beatmaps and filter by PP."""
        # First, search for beatmaps matching the basic filters
        beatmaps = list(self.api_client.search_beatmaps(
            self.filters,
            max_results=self.max_results * 3  # Get extra to filter by PP
        ))

        if self._cancelled:
            return []

        self.progress.emit(0, len(beatmaps))

        # Create download manager for fetching .osu files
        download_manager = DownloadManager(
            cache_path=self.cache_path,
            download_path=self.cache_path,  # Not used for .osu files
            mirror=self.mirror
        )

        min_pp, max_pp = self.pp_range
        filtered_results = []
        processed = 0

        for beatmap in beatmaps:
            if self._cancelled:
                await download_manager.close()
                return []

            # Fetch .osu file
            osu_file = await download_manager.fetch_osu_file(beatmap.beatmap_id)

            if osu_file:
                # Calculate PP
                pp = PPCalculator.calculate_max_pp(osu_file, beatmap.mode)

                if pp is not None:
                    beatmap.calculated_pp = pp
                    self.pp_calculated.emit(beatmap.beatmap_id, pp)

                    # Filter by PP range
                    if min_pp <= pp <= max_pp:
                        filtered_results.append(beatmap)

                        # Stop if we have enough results
                        if len(filtered_results) >= self.max_results:
                            break

            processed += 1
            self.progress.emit(processed, len(beatmaps))

        await download_manager.close()
        return filtered_results


class DownloadWorker(QThread):
    """Worker thread for downloading beatmaps."""

    progress = pyqtSignal(object)  # DownloadTask
    batch_progress = pyqtSignal(int, int)  # completed, total
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        beatmaps: List[BeatmapInfo],
        download_path: str,
        cache_path: str,
        mirror: str = MirrorAPI.CATBOY,
        max_concurrent: int = 3
    ):
        super().__init__()
        self.beatmaps = beatmaps
        self.download_path = download_path
        self.cache_path = cache_path
        self.mirror = mirror
        self.max_concurrent = max_concurrent
        self._download_manager: Optional[DownloadManager] = None

    def cancel(self):
        """Cancel downloads."""
        if self._download_manager:
            self._download_manager.cancel_all()

    def run(self):
        """Run downloads in a separate thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            loop.run_until_complete(self._download_all())
            loop.close()

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    async def _download_all(self):
        """Download all beatmaps."""
        self._download_manager = DownloadManager(
            cache_path=self.cache_path,
            download_path=self.download_path,
            mirror=self.mirror,
            max_concurrent=self.max_concurrent
        )

        # Create download tasks (deduplicate by beatmapset_id)
        seen_sets = set()
        tasks = []
        for beatmap in self.beatmaps:
            if beatmap.beatmapset_id not in seen_sets:
                seen_sets.add(beatmap.beatmapset_id)
                tasks.append(DownloadTask(
                    beatmapset_id=beatmap.beatmapset_id,
                    beatmap_id=beatmap.beatmap_id,
                    title=f"{beatmap.artist} - {beatmap.title}"
                ))

        def progress_callback(task: DownloadTask):
            self.progress.emit(task)

        def batch_callback(completed: int, total: int):
            self.batch_progress.emit(completed, total)

        self.batch_progress.emit(0, len(tasks))

        await self._download_manager.download_batch(
            tasks,
            progress_callback=progress_callback,
            batch_callback=batch_callback
        )

        await self._download_manager.close()


class OsuBeatmapDownloader:
    """Main application class."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()

        self.api_client: Optional[OsuApiClient] = None
        self.search_worker: Optional[SearchWorker] = None
        self.download_worker: Optional[DownloadWorker] = None

        self._connect_signals()
        self._initialize_api()

    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.window.config_btn.clicked.connect(self._show_config_dialog)
        self.window.search_btn.clicked.connect(self._start_search)
        self.window.download_btn.clicked.connect(self._start_download)
        self.window.cancel_btn.clicked.connect(self._cancel_operation)
        self.window.open_folder_btn.clicked.connect(self._open_download_folder)

    def _initialize_api(self):
        """Initialize API client if credentials are available."""
        if self.config.is_valid():
            try:
                self.api_client = OsuApiClient(
                    self.config.client_id,
                    self.config.client_secret
                )
                self.window.status_bar.showMessage("API configured. Ready to search.")
            except Exception as e:
                self.window.status_bar.showMessage(f"API initialization failed: {e}")
                self.api_client = None
        else:
            self.window.status_bar.showMessage(
                "Please configure your osu! API credentials."
            )

    def _show_config_dialog(self):
        """Show configuration dialog."""
        dialog = ConfigDialog(
            self.window,
            client_id=self.config.client_id,
            client_secret=self.config.client_secret
        )

        if dialog.exec():
            client_id, client_secret = dialog.get_credentials()

            # Update config
            self.config = replace(
                self.config,
                client_id=client_id,
                client_secret=client_secret
            )
            self.config_manager.save(self.config)

            # Reinitialize API
            self._initialize_api()

    def _start_search(self):
        """Start beatmap search."""
        if not self.api_client:
            QMessageBox.warning(
                self.window,
                "Not Configured",
                "Please configure your osu! API credentials first."
            )
            return

        # Get filters from UI
        filters = self.window.get_search_filters()
        pp_range = self.window.get_pp_range()
        max_results = self.window.get_max_results()

        # Set UI to searching state
        self.window.set_searching(True)
        self.window.search_progress.setMaximum(100)
        self.window.search_progress.setValue(0)

        # Create and start worker
        self.search_worker = SearchWorker(
            api_client=self.api_client,
            filters=filters,
            pp_range=pp_range,
            max_results=max_results,
            cache_path=self.config.cache_path,
            mirror=MirrorAPI.CATBOY
        )

        self.search_worker.finished.connect(self._on_search_complete)
        self.search_worker.error.connect(self._on_search_error)
        self.search_worker.progress.connect(self._on_search_progress)
        self.search_worker.pp_calculated.connect(self._on_pp_calculated)

        self.search_worker.start()

    def _on_search_complete(self, beatmaps: List[BeatmapInfo]):
        """Handle search completion."""
        self.window.search_complete.emit(beatmaps)
        self.search_worker = None

    def _on_search_error(self, error: str):
        """Handle search error."""
        self.window.search_error.emit(error)
        self.search_worker = None

    def _on_search_progress(self, current: int, total: int):
        """Handle search progress update."""
        if total > 0:
            self.window.search_progress.setMaximum(total)
            self.window.search_progress.setValue(current)
            self.window.status_update.emit(
                f"Processing beatmaps: {current}/{total}"
            )

    def _on_pp_calculated(self, beatmap_id: int, pp: float):
        """Handle PP calculation result."""
        self.window.pp_calculated.emit(beatmap_id, pp)

    def _start_download(self):
        """Start downloading selected beatmaps."""
        selected = self.window.get_selected_beatmaps()

        if not selected:
            QMessageBox.information(
                self.window,
                "No Selection",
                "Please select beatmaps to download."
            )
            return

        # Set UI to downloading state
        self.window.set_downloading(True)

        # Create and start worker
        self.download_worker = DownloadWorker(
            beatmaps=selected,
            download_path=self.config.download_path,
            cache_path=self.config.cache_path,
            mirror=MirrorAPI.CATBOY,
            max_concurrent=self.config.max_concurrent_downloads
        )

        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.batch_progress.connect(self._on_batch_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.error.connect(self._on_download_error)

        self.download_worker.start()

    def _on_download_progress(self, task: DownloadTask):
        """Handle download progress update."""
        self.window.download_progress.emit(task)

    def _on_batch_progress(self, completed: int, total: int):
        """Handle batch download progress."""
        self.window.batch_progress.emit(completed, total)

    def _on_download_finished(self):
        """Handle download completion."""
        self.window.set_downloading(False)
        self.download_worker = None
        QMessageBox.information(
            self.window,
            "Downloads Complete",
            f"Beatmaps have been downloaded to:\n{self.config.download_path}"
        )

    def _on_download_error(self, error: str):
        """Handle download error."""
        self.window.set_downloading(False)
        self.download_worker = None
        QMessageBox.critical(
            self.window,
            "Download Error",
            f"An error occurred during download:\n{error}"
        )

    def _cancel_operation(self):
        """Cancel current operation."""
        if self.search_worker:
            self.search_worker.cancel()
            self.search_worker = None
            self.window.set_searching(False)
            self.window.status_bar.showMessage("Search cancelled")

        if self.download_worker:
            self.download_worker.cancel()
            self.download_worker = None
            self.window.set_downloading(False)
            self.window.status_bar.showMessage("Downloads cancelled")

    def _open_download_folder(self):
        """Open the downloads folder in file manager."""
        path = Path(self.config.download_path)
        path.mkdir(parents=True, exist_ok=True)

        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])

    def run(self) -> int:
        """Run the application."""
        self.window.show()
        return self.app.exec()


def main():
    """Application entry point."""
    app = OsuBeatmapDownloader()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
