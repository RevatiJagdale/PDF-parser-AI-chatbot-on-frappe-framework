### PDF Parser Chatbot on Frappe Framework

This chatbot allows users to upload PDF documents, which are then processed using font-size-based section extraction, indexed into a vector database, and made searchable through a conversational AI interface. 
The implementation focuses on document structural awareness, ensuring that the AI understands the hierarchy of the content it retrieves.

### Key Features

* Section-Aware Extraction: Uses PDF metadata and font sizes to identify headers and group related text, rather than using fixed-length character splitting.
* Hybrid Retrieval: Combines Vector Store retrieval with a keyword-based re-ranking layer to improve accuracy for specific terminology.
* Local Embeddings: Utilizes the BAAI/bge-large-en-v1.5 model for generating document vectors without external API dependency.
* Integrated UI: A native Frappe Page interface built with modern JavaScript and CSS, providing real-time upload tracking and formatted AI responses.
* Contextual Prompting: Dynamic system prompts that adjust based on whether the user is asking for a general query or a document comparison.

### Tech Stack

* Backend: FastAPI, Uvicorn
* Frontend: Frappe Framework (HTML5, jQuery, CSS3)
* RAG Framework: LlamaIndex
* Vector Database: ChromaDB
* PDF Engine: PyMuPDF (fitz)
* LLM: Qwen 2.5 Coder 14b (via OpenAI-compatible API)
* Embedding Model: HuggingFace BGE-Large-v1.5

### Installation

1. Clone the repository into your Frappe bench apps folder:
   ```bash
   cd frappe-bench/apps
   git clone [repository-url]
   ```

2. Install the Python dependencies for the FastAPI server:
   ```bash
   pip install fastapi uvicorn chromadb pymupdf llama-index llama-index-embeddings-huggingface llama-index-vector-stores-chroma openai
   ```

3. Ensure the Frappe application is installed on your site:
   ```bash
   bench --site [your-site-name] install-app [app-name]
   ```

### Configuration

The server configuration is located in `server.py`. Update the following variables as per your environment:

* STORAGE_DIR: Directory for temporary PDF storage.
* CHROMA_DIR: Directory for the persistent vector database.
* INTERNAL_API_KEY: Your LLM provider API key.
* LLM_MODEL: The specific model identifier (default: qwen2.5-coder:14b).

### Usage

1. Start the FastAPI backend:
   ```bash
   python server.py
   ```
   The server runs by default on `http://0.0.0.0:8003`.

2. Access the interface within Frappe:
   Navigate to the "ichat" page within your Frappe application.

3. Document Processing:
   * Use the sidebar to upload one or more PDF files.
   * Wait for the "Indexed successfully" notification.
   * Enter queries in the chat input. The system will provide answers with inline citations formatted as (Filename - Section).

### Project Structure

* server.py: The FastAPI backend handling PDF processing, vector indexing, and RAG logic.
* ichat.js: Frontend logic for handling file uploads, API communication, and chat rendering.
* ichat.html: The structural layout for the document sidebar and chat interface.
* ichat.css: Styling for the chat bubbles, upload zones, and responsive layout.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/ichat
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
