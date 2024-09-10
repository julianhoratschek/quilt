class Entry:
    """Convenience class for entry data for mapping"""
    def __init__(self, content: str | list, skip: bool = False):
        self.skip: bool = skip
        self.content: str | list = content

