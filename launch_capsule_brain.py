import uvicorn, os
if __name__ == '__main__': uvicorn.run('capsule_brain.api.server:app', host=os.getenv('HOST','0.0.0.0'), port=int(os.getenv('PORT','8000')), reload=True)
