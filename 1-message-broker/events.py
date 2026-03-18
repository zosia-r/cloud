class BaseEvent:
    def __init__(self, message):
        self.message = message

    def to_dict(self):
        return {"message": self.message}

    @classmethod
    def from_dict(cls, data):
        return cls(message=data.get("message"))
    
class Type1Event(BaseEvent):
    def __init__(self, message="Data Type 1"):
        super().__init__(message)

class Type2Event(BaseEvent):
    def __init__(self, message="Data Type 2"):
        super().__init__(message)

class Type3Event(BaseEvent):
    def __init__(self, message="Data Type 3"):
        super().__init__(message)

class Type4Event(BaseEvent):
    def __init__(self, message="Data Type 4"):
        super().__init__(message)