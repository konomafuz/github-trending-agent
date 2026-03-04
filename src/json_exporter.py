"""JSON data exporter for web frontend."""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

def export_to_json(repos: list[dict[str, Any]], output_dir: str = "web/public/data") -> None:
    """Export analyzed repos to JSON for web frontend.

    Args:
        repos: List of analyzed repository data
        output_dir: Output directory for JSON file
    """
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Prepare data structure
        today = datetime.now().strftime("%Y-%m-%d")
        data = {
            "latest": today,
            "date": today,
            "repos": repos,
            "metadata": {
                "total": len(repos),
                "generated_at": datetime.now().isoformat()
            }
        }

        # Write to file
        output_file = output_path / "latest.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(repos)} repos to {output_file}")

    except Exception as e:
        logger.error(f"Failed to export JSON: {e}")
        raise
