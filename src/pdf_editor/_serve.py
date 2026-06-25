def main():
    import uvicorn
    uvicorn.run("pdf_editor.api.app:app", host="0.0.0.0", port=8000)
