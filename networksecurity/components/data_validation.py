import os
import sys
import numpy as np
import pandas as pd

from networksecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.constants.training_pipeline import SCHEMA_FILE_PATH
from networksecurity.logging.logger import logging
from scipy.stats import ks_2samp
from networksecurity.utils.main_utils.utils import read_yaml_file, write_yaml_file


class DataValidation:
    def __init__(self, data_ingestion_artifact: DataIngestionArtifact,
                 data_validation_config: DataValidationConfig):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # ✅ COLUMN VALIDATION (FIXED)
    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            # Extract column names from schema (list of dicts)
            schema_columns = set([list(col.keys())[0] for col in self._schema_config["columns"]])
            df_columns = set(dataframe.columns)

            missing_cols = schema_columns - df_columns
            extra_cols = df_columns - schema_columns

            print("\nSchema columns:", schema_columns)
            print("DataFrame columns:", df_columns)
            print("Missing columns:", missing_cols)
            print("Extra columns:", extra_cols)

            return len(missing_cols) == 0 and len(extra_cols) == 0

        except Exception as e:
            raise NetworkSecurityException(e, sys)
        
    # ✅ DATA DRIFT (FIXED)
    def detect_dataset_drift(self, base_df: pd.DataFrame,
                             current_df: pd.DataFrame,
                             threshold=0.05) -> bool:
        try:
            status = True
            report = {}

            for column in base_df.columns:
                d1 = base_df[column]
                d2 = current_df[column]

                is_same_dist = ks_2samp(d1, d2)

                if threshold <= is_same_dist.pvalue:
                    is_found = False
                else:
                    is_found = True
                    status = False

                report[column] = {
                    "p_value": float(is_same_dist.pvalue),
                    "drift_status": is_found
                }

            drift_report_file_path = self.data_validation_config.drift_report_file_path

            os.makedirs(os.path.dirname(drift_report_file_path), exist_ok=True)

            write_yaml_file(file_path=drift_report_file_path, content=report)

            return status

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # ✅ READ DATA (FIXED for extra column issue)
    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path, index_col=0)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # ✅ MAIN FUNCTION (FULLY FIXED)
    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            error_message = ""

            train_file_path = self.data_ingestion_artifact.trained_file_path
            test_file_path = self.data_ingestion_artifact.test_file_path

            # Read data
            train_dataframe = self.read_data(train_file_path)
            test_dataframe = self.read_data(test_file_path)

            # Clean column names
            train_dataframe.columns = train_dataframe.columns.str.strip()
            test_dataframe.columns = test_dataframe.columns.str.strip()

            # DEBUG PRINT
            print("\n===== DEBUG START =====")
            print("Schema columns:", self._schema_config["columns"])
            print("Train columns:", list(train_dataframe.columns))
            print("Test columns:", list(test_dataframe.columns))
            print("===== DEBUG END =====\n")

            # Validate columns
            if not self.validate_number_of_columns(train_dataframe):
                error_message += "Train dataframe does not contain all columns.\n"

            if not self.validate_number_of_columns(test_dataframe):
                error_message += "Test dataframe does not contain all columns.\n"

            if error_message != "":
                raise Exception(error_message)

            # Check data drift
            status = self.detect_dataset_drift(
                base_df=train_dataframe,
                current_df=test_dataframe
            )

            # Create directory
            os.makedirs(
                os.path.dirname(self.data_validation_config.valid_train_file_path),
                exist_ok=True
            )

            # Save valid data
            train_dataframe.to_csv(
                self.data_validation_config.valid_train_file_path,
                index=False,
                header=True
            )

            test_dataframe.to_csv(
                self.data_validation_config.valid_test_file_path,
                index=False,
                header=True
            )

            # Create artifact
            data_validation_artifact = DataValidationArtifact(
                validation_status=status,
                valid_train_file_path=self.data_validation_config.valid_train_file_path,
                valid_test_file_path=self.data_validation_config.valid_test_file_path,
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path
            )

            return data_validation_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)