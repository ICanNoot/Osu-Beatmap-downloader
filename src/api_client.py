"""osu! API client wrapper using ossapi."""

from typing import Optional, List, Generator
from dataclasses import dataclass
from enum import IntEnum

from ossapi import Ossapi, BeatmapsetSearchFilter
from ossapi.enums import RankStatus, GameMode


class OsuMode(IntEnum):
    """osu! game modes."""
    STANDARD = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3


@dataclass
class SearchFilters:
    """Search filters for beatmap search."""
    mode: OsuMode = OsuMode.STANDARD
    min_stars: float = 0.0
    max_stars: float = 10.0
    min_length: int = 0  # seconds
    max_length: int = 600  # seconds
    min_bpm: float = 0.0
    max_bpm: float = 500.0
    mania_keys: Optional[int] = None  # 4 or 7 for mania


@dataclass
class BeatmapInfo:
    """Information about a beatmap."""
    beatmap_id: int
    beatmapset_id: int
    title: str
    artist: str
    version: str  # difficulty name
    creator: str
    mode: OsuMode
    stars: float
    length: int  # seconds
    bpm: float
    max_combo: int
    cs: float
    ar: float
    od: float
    hp: float
    calculated_pp: Optional[float] = None

    @property
    def display_name(self) -> str:
        """Get display name for the beatmap."""
        return f"{self.artist} - {self.title} [{self.version}]"

    @property
    def formatted_length(self) -> str:
        """Get formatted length string."""
        minutes = self.length // 60
        seconds = self.length % 60
        return f"{minutes}:{seconds:02d}"


class OsuApiClient:
    """Client for interacting with osu! API."""

    def __init__(self, client_id: int, client_secret: str):
        """Initialize API client.

        Args:
            client_id: osu! OAuth client ID
            client_secret: osu! OAuth client secret
        """
        self.api = Ossapi(client_id, client_secret)

    def search_beatmaps(
        self,
        filters: SearchFilters,
        max_results: int = 100
    ) -> Generator[BeatmapInfo, None, None]:
        """Search for beatmaps matching filters.

        Args:
            filters: Search filters to apply
            max_results: Maximum number of results to return

        Yields:
            BeatmapInfo objects for matching beatmaps
        """
        # Convert mode to ossapi GameMode
        game_mode = GameMode(filters.mode.value)

        # Build query string for star rating
        query_parts = []
        if filters.min_stars > 0:
            query_parts.append(f"stars>={filters.min_stars}")
        if filters.max_stars < 10:
            query_parts.append(f"stars<={filters.max_stars}")

        # Add BPM filter to query
        if filters.min_bpm > 0:
            query_parts.append(f"bpm>={filters.min_bpm}")
        if filters.max_bpm < 500:
            query_parts.append(f"bpm<={filters.max_bpm}")

        # Add length filter (in seconds)
        if filters.min_length > 0:
            query_parts.append(f"length>={filters.min_length}")
        if filters.max_length < 600:
            query_parts.append(f"length<={filters.max_length}")

        # Add mania key filter
        if filters.mode == OsuMode.MANIA and filters.mania_keys:
            query_parts.append(f"keys={filters.mania_keys}")

        query = " ".join(query_parts) if query_parts else None

        count = 0
        cursor = None

        while count < max_results:
            # Search beatmapsets
            result = self.api.search_beatmapsets(
                query=query,
                mode=game_mode,
                cursor=cursor,
                category=BeatmapsetSearchFilter.RANKED
            )

            if not result.beatmapsets:
                break

            for beatmapset in result.beatmapsets:
                # Filter individual beatmaps within the set
                for beatmap in beatmapset.beatmaps:
                    # Check if mode matches
                    if beatmap.mode != game_mode:
                        continue

                    # Check star rating
                    if not (filters.min_stars <= beatmap.difficulty_rating <= filters.max_stars):
                        continue

                    # Check length
                    if not (filters.min_length <= beatmap.total_length <= filters.max_length):
                        continue

                    # Check BPM
                    if not (filters.min_bpm <= beatmap.bpm <= filters.max_bpm):
                        continue

                    # Check mania keys
                    if filters.mode == OsuMode.MANIA and filters.mania_keys:
                        if beatmap.cs != filters.mania_keys:
                            continue

                    yield BeatmapInfo(
                        beatmap_id=beatmap.id,
                        beatmapset_id=beatmapset.id,
                        title=beatmapset.title,
                        artist=beatmapset.artist,
                        version=beatmap.version,
                        creator=beatmapset.creator,
                        mode=OsuMode(beatmap.mode.value),
                        stars=beatmap.difficulty_rating,
                        length=beatmap.total_length,
                        bpm=beatmap.bpm,
                        max_combo=beatmap.max_combo or 0,
                        cs=beatmap.cs,
                        ar=beatmap.ar,
                        od=beatmap.accuracy,
                        hp=beatmap.drain
                    )

                    count += 1
                    if count >= max_results:
                        return

            # Get next page
            cursor = result.cursor
            if cursor is None:
                break

    def get_beatmap(self, beatmap_id: int) -> Optional[BeatmapInfo]:
        """Get a specific beatmap by ID.

        Args:
            beatmap_id: The beatmap ID

        Returns:
            BeatmapInfo or None if not found
        """
        try:
            beatmap = self.api.beatmap(beatmap_id)
            beatmapset = beatmap.beatmapset

            return BeatmapInfo(
                beatmap_id=beatmap.id,
                beatmapset_id=beatmapset.id,
                title=beatmapset.title,
                artist=beatmapset.artist,
                version=beatmap.version,
                creator=beatmapset.creator,
                mode=OsuMode(beatmap.mode.value),
                stars=beatmap.difficulty_rating,
                length=beatmap.total_length,
                bpm=beatmap.bpm,
                max_combo=beatmap.max_combo or 0,
                cs=beatmap.cs,
                ar=beatmap.ar,
                od=beatmap.accuracy,
                hp=beatmap.drain
            )
        except Exception:
            return None
