class OctothorpeUser(object):
    def __init__(self, user_id: str = '', username: str = '', spawnpoint: tuple[int, int] | None = None, score: int = 0):
        self.user_id: str = user_id
        self.username: str = username
        self.position: tuple[int, int] | None = spawnpoint
        self.score: int = score