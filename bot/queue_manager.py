import os
import json
import time
import uuid
import logging
from config.settings import QUEUE_FILE

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        self.submissions = {}
        self.load()

    def load(self):
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    self.submissions = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load queue from {QUEUE_FILE}: {e}")
                self.submissions = {}
        else:
            self.submissions = {}

    def save(self):
        try:
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.submissions, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save queue to {QUEUE_FILE}: {e}")

    def add_submission(self, from_user_id: int, from_user_name: str, file_id: str, file_unique_id: str, emoji: str, original_file_name: str = None) -> dict:
        """
        Adds a new submission to the queue. Returns the created submission dict or None if duplicate.
        """
        # Deduplication check
        if self.is_duplicate(file_unique_id):
            return None

        sub_id = str(uuid.uuid4())[:8] # Short 8-character ID
        
        submission = {
            "id": sub_id,
            "file_id": file_id,
            "file_unique_id": file_unique_id,
            "original_file_name": original_file_name,
            "emoji": emoji,
            "from_user_id": from_user_id,
            "from_user_name": from_user_name,
            "timestamp": int(time.time()),
            "status": "pending"
        }
        
        self.submissions[sub_id] = submission
        self.save()
        return submission

    def get_submission(self, sub_id: str) -> dict:
        return self.submissions.get(sub_id)

    def get_pending(self) -> list:
        return [s for s in self.submissions.values() if isinstance(s, dict) and s.get("status") == "pending"]

    def update_status(self, sub_id: str, status: str, reason: str = None):
        if sub_id in self.submissions:
            self.submissions[sub_id]["status"] = status
            if reason:
                self.submissions[sub_id]["reason"] = reason
            self.save()
            return True
        return False

    def is_duplicate(self, file_unique_id: str) -> bool:
        """Checks if a file_unique_id already exists in the queue (pending, approved, or rejected)."""
        for sub in self.submissions.values():
            if isinstance(sub, dict) and sub.get("file_unique_id") == file_unique_id:
                return True
        return False

    def get_stats(self) -> dict:
        stats = {"total": 0, "pending": 0, "approved": 0, "rejected": 0}
        for sub in self.submissions.values():
            if not isinstance(sub, dict):
                continue
            stats["total"] += 1
            status = sub.get("status")
            if status in stats:
                stats[status] += 1
        return stats

    def is_blocked(self, user_id: int) -> bool:
        # type: ignore
        if "blocked_users" not in self.submissions:
            self.submissions["blocked_users"] = [] # type: ignore
        return user_id in self.submissions["blocked_users"] # type: ignore

    def block_user(self, user_id: int):
        # type: ignore
        if "blocked_users" not in self.submissions:
            self.submissions["blocked_users"] = [] # type: ignore
        if user_id not in self.submissions["blocked_users"]: # type: ignore
            self.submissions["blocked_users"].append(user_id) # type: ignore
            self.save()

    def get_user_submission_count_last_hour(self, user_id: int) -> int:
        now = int(time.time())
        count = 0
        for key, sub in self.submissions.items():
            if key == "blocked_users": continue
            # type: ignore
            if isinstance(sub, dict) and sub.get("from_user_id") == user_id and sub.get("timestamp", 0) > now - 3600:
                count += 1
        return count
