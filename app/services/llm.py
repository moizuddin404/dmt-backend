import os
import openai
from typing import List
from app.config import OPENAI_API_KEY

client = openai.AsyncOpenAI(
    api_key=OPENAI_API_KEY,
)

async def generate_table_mapping(headers: List[str], sample_data: List[dict]) -> dict:
    prompt = f"""
              You are an expert in data integration. Given these headers and some sample data from a CSV file,
              return a JSON object that maps the data to the normalized patient profile database tables.
              Headers: {headers}
              Sample Data: {sample_data}
              Output format:
              {{
              "table_name": "patients",
              "mappings": {{
                    "first_name": "FirstName",
                    "date_of birth": "DOB",
                    ...
                }}
              }}
              """
        
    response = await client.chat.completions.create(
            model="gpt-4o", # Using gpt-4o for better JSON output and understanding
            response_format={"type": "json_object"}, # Instruct the model to output JSON
            messages=[
                {"role": "system", "content": "You are an expert in data integration and provide JSON mappings."},
                {"role": "user", "content": prompt}
            ]
        )

    return response.choices[0].message["content"]