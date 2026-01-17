
import json
from datetime import datetime
from typing import Dict, List, Any
from logger import logger
from config import Config

def log_visitor_session(name: str, arrived_at: datetime, left_at: datetime, logfile: str) -> None:
    """
    Log a visitor session as a JSON object per line.
    """
    try:
        record = {
            "Timestamp": arrived_at.strftime("%Y-%m-%d"),
            "visitor": name,
            "from": arrived_at.strftime("%H:%M:%S"),
            "to": left_at.strftime("%H:%M:%S"),
        }
        with open(logfile, "a") as f:
            f.write(json.dumps(record) + "\n")
        logger.info(f"Logged session for visitor: {name}")
    except Exception as e:
        logger.error(f"Failed to log visitor session: {e}", exc_info=True)


def update_visitors(
    detected_names: List[str], 
    active_visitors: Dict[str, Any], 
    logfile: str, 
    grace_period_sec: int
) -> Dict[str, Any]:
    """
    Update visitor status based on detected names.
    Log arrivals and departures.
    """
    now = datetime.now()

    # Handle arrivals
    for name in detected_names:
        if name == "Unknown":
            continue
            
        if name not in active_visitors:
            # First time seeing this visitor
            active_visitors[name] = {"last_seen": now, "arrived_at": now}
            logger.info(f"New visitor detected: {name}")
        else:
            active_visitors[name]["last_seen"] = now

    # Handle departures
    to_remove = []
    for name, data in active_visitors.items():
        if name not in detected_names:
            # Person is no longer detected -> check if departed
            time_absent = (now - data["last_seen"]).total_seconds()
            
            if time_absent > grace_period_sec:
                logger.info(f"Visitor {name} considered departed (absent for {time_absent:.1f}s)")
                log_visitor_session(
                    name, data["arrived_at"], data["last_seen"], logfile
                )
                to_remove.append(name)

    for name in to_remove:
        del active_visitors[name]

    return active_visitors
