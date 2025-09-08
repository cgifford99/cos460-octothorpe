class OctothorpeUser(object):
    def __init__(self, username: str = '', spawnpoint: tuple[int, int] | None = None, score: int = 0):
        self.username: str = username
        self.position: tuple[int, int] | None = spawnpoint
        self.score: int = score