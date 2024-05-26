from fastapi import FastAPI
from fastapi.responses import JSONResponse
from extract_ocr import getInfor
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


origins = [
    "*",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/Infomation/Passport", response_class=JSONResponse)
def main(file_url: str):
    return JSONResponse(getInfor(file_url))
