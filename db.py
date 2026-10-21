from datetime import datetime, timezone
from threading import Lock

from models import Skill, SkillIn


def timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0)


class SkillStore:

    def __init__(self):
        self.lock = Lock()
        self.reset()

    def reset(self):
        self.skills = {}
        self.next_id = 1
        self.add(SkillIn(name="REST API design", category="Backend", proficiency=3,
                         status="learning", notes="Resources, verbs, status codes"))
        self.add(SkillIn(name="Python", category="Languages", proficiency=4,
                         status="mastered", notes="Used for this project"))
        self.add(SkillIn(name="Docker", category="DevOps", proficiency=1,
                         status="planned", notes="Next: containerise this API"))

    def all(self):
        return list(self.skills.values())

    def get(self, skill_id):
        return self.skills.get(skill_id)

    def name_taken(self, name, skip_id=None):
        for skill in self.skills.values():
            if skill.id != skip_id and skill.name.lower() == name.lower():
                return True
        return False

    def add(self, data):
        # lock so two requests at once can't get the same id
        with self.lock:
            now = timestamp()
            skill = Skill(id=self.next_id, created_at=now, updated_at=now, **data.model_dump())
            self.skills[skill.id] = skill
            self.next_id += 1
        return skill

    def save(self, skill):
        self.skills[skill.id] = skill
        return skill

    def remove(self, skill_id):
        return self.skills.pop(skill_id, None)
