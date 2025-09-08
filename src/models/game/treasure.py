class Treasure(object):
    def __init__(self, id: int, position: tuple[int, int], score: int):
        self.id: int = id
        self.position: tuple[int, int] = position
        self.score: int = score