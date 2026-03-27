import sys
import os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()
mongo_db_url = os.getenv("MONGODB_URL_KEY")
print(mongo_db_url)
import pymongo
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile,Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse
import pandas as pd

from networksecurity.utils.main_utils.utils import load_object

from networksecurity.utils.ml_utils.model.estimator import NetworkModel


client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)

from networksecurity.constants.training_pipeline import DATA_INGESTION_COLLECTION_NAME
from networksecurity.constants.training_pipeline import DATA_INGESTION_DATABASE_NAME

database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="./templates")

@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")

@app.get("/train")
async def train_route():
    try:
        train_pipeline=TrainingPipeline()
        train_pipeline.run_pipeline()
        return Response("Training is successful")
    except Exception as e:
        raise NetworkSecurityException(e,sys)
    
@app.post("/predict")
async def predict_route(request: Request, file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        df.columns = df.columns.str.strip()

        preprocessor = load_object("final_model/preprocessor.pkl")
        final_model = load_object("final_model/model.pkl")

        rename_map = {
            "having_ip_address": "having_IP_Address",
            "url_length": "URL_Length",
            "shortining_service": "Shortining_Service",
            "having_at_symbol": "having_At_Symbol",
            "double_slash_redirecting": "double_slash_redirecting",
            "prefix_suffix": "Prefix_Suffix",
            "having_sub_domain": "having_Sub_Domain",
            "sslfinal_state": "SSLfinal_State",
            "domain_registeration_length": "Domain_registeration_length",
            "favicon": "Favicon",
            "port": "port",
            "https_token": "HTTPS_token",
            "request_url": "Request_URL",
            "url_of_anchor": "URL_of_Anchor",
            "links_in_tags": "Links_in_tags",
            "sfh": "SFH",
            "submitting_to_email": "Submitting_to_email",
            "abnormal_url": "Abnormal_URL",
            "redirect": "Redirect",
            "on_mouseover": "on_mouseover",
            "rightclick": "RightClick",
            "popupwidnow": "popUpWidnow",
            "iframe": "Iframe",
            "age_of_domain": "age_of_domain",
            "dnsrecord": "DNSRecord",
            "web_traffic": "web_traffic",
            "page_rank": "Page_Rank",
            "google_index": "Google_Index",
            "links_pointing_to_page": "Links_pointing_to_page",
            "statistical_report": "Statistical_report"
        }

        df = df.rename(columns=rename_map)

        print("CSV columns after rename:", df.columns.tolist())
        print("Expected columns:", preprocessor.feature_names_in_.tolist())

        expected_columns = list(preprocessor.feature_names_in_)

        missing_cols = [col for col in expected_columns if col not in df.columns]
        extra_cols = [col for col in df.columns if col not in expected_columns]

        print("Missing columns:", missing_cols)
        print("Extra columns:", extra_cols)

        if missing_cols:
            return Response(
                content=f"Missing columns in uploaded CSV: {missing_cols}",
                status_code=400
            )

        df = df[expected_columns]

        network_model = NetworkModel(preprocessor=preprocessor, model=final_model)
        y_pred = network_model.predict(df)

        df["predicted_column"] = y_pred

        os.makedirs("prediction_output", exist_ok=True)
        df.to_csv("prediction_output/output.csv", index=False)

        table_html = df.to_html(classes="table table-striped")

        return templates.TemplateResponse(
            "table.html",
            {"request": request, "table": table_html}
        )

    except Exception as e:
        print("ACTUAL ERROR:", repr(e))
        raise
     


        

    
if __name__=="__main__":
    app_run(app,host="0.0.0.0",port=8000)
