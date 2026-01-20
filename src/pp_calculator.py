"""PP calculation using rosu-pp-py."""

from pathlib import Path
from typing import Optional
import rosu_pp_py as rosu

from .api_client import OsuMode


class PPCalculator:
    """Calculate PP for beatmaps using rosu-pp-py."""

    @staticmethod
    def calculate_max_pp(
        osu_file_path: str,
        mode: Optional[OsuMode] = None
    ) -> Optional[float]:
        """Calculate maximum PP (100% SS) for a beatmap.

        Args:
            osu_file_path: Path to the .osu file
            mode: Game mode (None = use map's native mode)

        Returns:
            Maximum PP value or None if calculation fails
        """
        try:
            # Read the beatmap file
            with open(osu_file_path, 'r', encoding='utf-8') as f:
                beatmap_content = f.read()

            # Parse the beatmap
            beatmap = rosu.Beatmap(content=beatmap_content)

            # Create performance calculator
            perf = rosu.Performance()

            # Set mode if specified (for converts)
            if mode is not None:
                perf.set_mode(mode.value)

            # Set 100% accuracy for SS
            perf.set_accuracy(100.0)

            # Calculate performance
            result = perf.calculate(beatmap)

            return result.pp

        except Exception as e:
            print(f"Error calculating PP for {osu_file_path}: {e}")
            return None

    @staticmethod
    def calculate_pp_with_accuracy(
        osu_file_path: str,
        accuracy: float = 100.0,
        combo: Optional[int] = None,
        misses: int = 0,
        mode: Optional[OsuMode] = None
    ) -> Optional[float]:
        """Calculate PP with specific accuracy and combo.

        Args:
            osu_file_path: Path to the .osu file
            accuracy: Accuracy percentage (0-100)
            combo: Combo count (None = max combo)
            misses: Number of misses
            mode: Game mode (None = use map's native mode)

        Returns:
            PP value or None if calculation fails
        """
        try:
            with open(osu_file_path, 'r', encoding='utf-8') as f:
                beatmap_content = f.read()

            beatmap = rosu.Beatmap(content=beatmap_content)

            perf = rosu.Performance()

            if mode is not None:
                perf.set_mode(mode.value)

            perf.set_accuracy(accuracy)
            perf.set_misses(misses)

            if combo is not None:
                perf.set_combo(combo)

            result = perf.calculate(beatmap)

            return result.pp

        except Exception as e:
            print(f"Error calculating PP: {e}")
            return None

    @staticmethod
    def get_beatmap_attributes(
        osu_file_path: str,
        mode: Optional[OsuMode] = None
    ) -> Optional[dict]:
        """Get beatmap difficulty attributes.

        Args:
            osu_file_path: Path to the .osu file
            mode: Game mode (None = use map's native mode)

        Returns:
            Dictionary with beatmap attributes or None
        """
        try:
            with open(osu_file_path, 'r', encoding='utf-8') as f:
                beatmap_content = f.read()

            beatmap = rosu.Beatmap(content=beatmap_content)

            # Calculate difficulty
            diff = rosu.Difficulty()
            if mode is not None:
                diff.set_mode(mode.value)

            attrs = diff.calculate(beatmap)

            return {
                'stars': attrs.stars,
                'max_combo': attrs.max_combo,
            }

        except Exception as e:
            print(f"Error getting beatmap attributes: {e}")
            return None
