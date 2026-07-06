"""Manual smoke test for discover_route_and_points.

Usage:
    .venv/bin/python3 scripts/retest.py --origin Ульяновск --destination Самара
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.route_discovery import discover_route_and_points
from app.schemas import JourneyJob, JourneyRequest, JourneyStatus, TransportMode


async def main(args: argparse.Namespace) -> None:
    job = JourneyJob(
        id="retest",
        status=JourneyStatus.queued,
        request=JourneyRequest(
            origin=args.origin,
            destination=args.destination,
            waypoints=args.waypoint,
            mode=TransportMode(args.mode),
        ),
    )
    jobs = {job.id: job}
    await discover_route_and_points(job.id, jobs)

    print("status:", job.status)
    print("error:", job.error)
    if job.points:
        print(f"points: {len(job.points)}")
        for p in job.points:
            print(f"  {p.distance_km:>6.1f} km  {p.title}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--waypoint", action="append", default=[], help="repeatable")
    parser.add_argument("--mode", choices=[m.value for m in TransportMode], default="car")
    asyncio.run(main(parser.parse_args()))
