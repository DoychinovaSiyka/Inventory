from models.location import Location
from storage.json_repository import  JSONRepository





class LocationController:
    def __init__(self,repo):
        self.repo = repo
        self.locations = self.repo.load()
# LocationController е важен,защото иначе няма кой да управлява:
# създаване на локации
# списък с локации
# връзка между склад и локация
# евентуално търсене по локация
