from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
import csv
import codecs
import uvicorn
import os
import time
import pandas as pd
import openpyxl
import xml.etree.ElementTree as ET

app = FastAPI(title='Upload and Download in XML',
              description="Upload file and Download in XML format")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
timestr = time.strftime("%Y%m%d-%H%M%S")

@app.get("/Welcome")
def read_root():
    return {"Hello": "User"}

def convert_to_xml(data_dict):
    root = ET.Element("Data")
    for row in data_dict:
        item = ET.SubElement(root, "Item")
        for key, value in row.items():
            ET.SubElement(item, key).text = str(value)
    tree = ET.ElementTree(root)
    return tree

@app.post("/uploadndownload")
def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if file.filename.endswith('.csv') or file.filename.endswith('.xlsx') or file.filename.endswith('.tsv') or file.filename.endswith('.TSV'):
        if file.filename.endswith('.csv'):
            data = list(csv.DictReader(codecs.iterdecode(file.file, 'utf-8')))
        elif file.filename.endswith('.xlsx'):
            data = pd.read_excel(file.file.read(), index_col=0).to_dict(orient='records')
        elif file.filename.endswith('.tsv'):
            data = list(csv.DictReader(codecs.iterdecode(file.file, 'utf-8'), delimiter='\t'))
        else:
            data = list(csv.DictReader(codecs.iterdecode(file.file, 'utf-8'), delimiter='\t'))

        background_tasks.add_task(convert_and_save_to_xml, data, file.filename)
        return {"message": "File uploaded successfully and will be converted to XML shortly."}
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only CSV, XLSX, and TSV files are supported.")

def convert_and_save_to_xml(data, filename):
    xml_tree = convert_to_xml(data)
    xml_filename = os.path.join(BASE_DIR, "uploads", f"{os.path.splitext(filename)[0]}.xml")
    xml_tree.write(xml_filename)
    print(f"File converted and saved to {xml_filename}")

@app.get("/download/{filename}")
def download(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename, media_type="application/octet-stream")
    else:
        raise HTTPException(status_code=404, detail="File not found.")
