from fastapi import FastAPI, HTTPException
from pydantic import BaseModel,Field
from typing import Dict
from document_downloader import DocumentDownloader  

app = FastAPI()

class DownloadRequest(BaseModel):
    temas_legales: Dict[str, int] = Field(
        default={"Divorcio": 10, "PQR": 2, "Abandono de bienes": 10, "Abandono de menores": 10},
        description="A dictionary where the keys are legal topics and the values are the number of documents to download for each topic."
    )

@app.post("/download_documents/")
async def download_documents(request: DownloadRequest):
    try:
        downloader = DocumentDownloader(
            topics=request.temas_legales
        )
        downloader.run()
        return {"status": "success", "message": "Documents downloaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)