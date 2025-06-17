from pydantic import BaseModel
class ImageRequest(BaseModel):
    image: str 

class MessageRequest(BaseModel):
    message: str