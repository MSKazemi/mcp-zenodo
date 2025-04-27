# Zenodo MCP

A Python application for interacting with Zenodo records, including comparing multiple records.

## Features

- Compare multiple Zenodo records
- Analyze metadata fields such as title, authors, topics, and publication date
- Calculate similarity scores between records
- Visualize differences between records

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/zenodo-mcp.git
   cd zenodo-mcp
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. Update the `.env` file with your Zenodo API token and other configuration options.

## Usage

1. Start the server:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. Access the API documentation at `http://localhost:8000/docs`

3. Use the API to compare Zenodo records:
   ```python
   import requests

   # Example: Compare two records
   response = requests.post(
       "http://localhost:8000/api/compare",
       json={
           "record_ids": ["1234567", "7654321"],
           "compare_fields": ["title", "authors", "topics", "publication_date"]
       }
   )
   print(response.json())
   ```

## API Endpoints

- `POST /api/compare`: Compare multiple Zenodo records
  - Request body:
    ```json
    {
        "record_ids": ["1234567", "7654321"],
        "compare_fields": ["title", "authors", "topics", "publication_date"]
    }
    ```
  - Response:
    ```json
    {
        "comparison_results": [
            {
                "field": "title",
                "values": {
                    "1234567": "Title 1",
                    "7654321": "Title 2"
                },
                "similarity_score": 0.8
            },
            ...
        ]
    }
    ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 