import json
import re
import google.generativeai as genai
from typing import List
from app.config import Config


genai.configure(api_key=Config.GEMINI_API_KEY)

async def generate_table_mapping(headers: List[str], sample_data: List[dict]) -> dict:
    prompt = f"""
    You're a data integration expert. Given CSV headers and sample data, return a JSON mapping of input columns to fields in a normalized patient profile table.
    Map only the provided input columns (headers)
    If headers are missing, infer them from sample data.
    new headers not in schema should be in extras. Don't map ids or timestamps.
    Headers: {headers}
    Sample Data: {sample_data}
    Return a JSON object that maps only the relevant fields from the CSV to the appropriate normalized database tables.
    ```json
    {{
        "mappings": {{
            "patient": {{
                "first_name": "First Name",
                "last_name": "Last Name",
                "date_of_birth": "DOB",
                "gender": "Gender",
                "phone": "Phone",
                "email": "Email",
                "address": "Address" or ["address_line", "landmark", "city", "state"],
                "country": "Country",
            }},
            "hospital": {{
                "hospital_name": "Hospital Name",
                "hospital_address": "Hospital Address" or  ["address_line", "landmark", "city", "state"]
            }},
            "lifestyle": {{
                "smoking_status": "Smoking",
                "alcohol_use": "Alcohol",
                "exercise_habit": "Exercise",
                "diet": "Diet"
            }},
            "lab_result": {{
                "test_name": "Test Name",
                "test_value": "Value",
                "unit": "Unit",
                "test_date": "Date"
            }},
            "treatment": {{
                "treatment_type": "Treatment Type",
                "start_date": "Start",
                "end_date": "End",
                "outcome": "Outcome"
            }},
            "diagnosis": {{
                "diagnosis_date": "Diagnosis Date",
                "condition_id": "condition_name" or "disease" or "illness"
            }},
            "family_history": {{
                "relative": "Relative"
            }}, 
            {{
            "medical_condition": {{
                "condition_name: "condition_name" or "disease" or "illness"
            }}
            }}
        }}
    }}
    ```

    Here is my schema for your reference:

    -- Hospital Table
    CREATE TABLE hospital (
        hospital_id SERIAL PRIMARY KEY,
        hospital_name TEXT,
        hospital_address TEXT
    );

    -- Patient Table
    CREATE TABLE patient (
        patient_id SERIAL PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        date_of_birth DATE,
        gender TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        country TEXT,
        hospital_id INT REFERENCES hospital(hospital_id)
    );

    -- Condition Table
    CREATE TABLE medical_condition (
        condition_id SERIAL PRIMARY KEY,
        condition_name TEXT
    );

    -- Family History Table
    CREATE TABLE family_history (
        history_id SERIAL PRIMARY KEY,
        patient_id INT REFERENCES patient(patient_id),
        relative TEXT,
        condition_id INT REFERENCES medical_condition(condition_id)
    );

    -- Diagnosis Table
    CREATE TABLE diagnosis (
        diagnosis_id SERIAL PRIMARY KEY,
        patient_id INT REFERENCES patient(patient_id),
        diagnosis_date DATE,
        condition_id INT REFERENCES medical_condition(condition_id)
    );

    -- Treatment Table
    CREATE TABLE treatment (
        treatment_id SERIAL PRIMARY KEY,
        patient_id INT REFERENCES patient(patient_id),
        treatment_type TEXT,
        start_date DATE,
        end_date DATE,
        outcome TEXT
    );

    -- Lifestyle Table
    CREATE TABLE lifestyle (
        lifestyle_id SERIAL PRIMARY KEY,
        patient_id INT REFERENCES patient(patient_id),
        smoking_status TEXT,
        alcohol_use TEXT,
        exercise_habit TEXT,
        diet TEXT
    );

    -- Lab Result Table
    CREATE TABLE lab_result (
        result_id SERIAL PRIMARY KEY,
        patient_id INT REFERENCES patient(patient_id),
        test_name TEXT,
        test_value TEXT,
        unit TEXT,
        test_date DATE
    );

    -- Junction Table: Patient ↔ Condition
    CREATE TABLE patient_condition (
        patient_id INT REFERENCES patient(patient_id),
        condition_id INT REFERENCES medical_condition(condition_id),
        PRIMARY KEY (patient_id, condition_id)
    );

    -- File Upload Log
    CREATE TABLE file_upload_log (
        file_id SERIAL PRIMARY KEY,
        filename TEXT,
        file_type TEXT,
        upload_time TIMESTAMP DEFAULT NOW(),
        status TEXT,
        mapped_tables TEXT[],
        mapped_columns TEXT[],
        missing_columns TEXT[],
        extra_columns TEXT[],
        empty_cells INT,
        invalid_types TEXT[],
        total_rows INT,
        local_path TEXT
    );

    Note: Strictly only return valid JSON response without any explanations or extra text.
    """

    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        generation_config={
            "temperature": 0.3,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 1024
        }
    )

    try:
        response = await model.generate_content_async(
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )

        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                raise

        if not isinstance(result, dict) or "mappings" not in result:
            raise ValueError("Invalid JSON structure: missing 'mappings'")

        print("\n\nMapping Result created from Response\n", result)
        return result

    except Exception as e:
        print(f"Error generating or parsing Gemini response: {e}")
        raise
