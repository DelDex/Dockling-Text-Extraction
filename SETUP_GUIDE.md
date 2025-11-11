# Vector Database Setup Guide

This guide will help you run the hybrid_chunking.py script to process documents.

## Project Structure

```
vector_database/
├── venv/                    # Virtual environment (created)
├── documents/               # Input documents
├── outputs/                 # Generated chunks output
├── hybrid_chunking.py       # Main script
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
├── run.bat                  # Windows runner script
└── SETUP_GUIDE.md          # This file
```

## Quick Start

### Option 1: Using the Batch Script (Easiest)
```bash
run.bat
```

### Option 2: Manual Execution
```bash
# Activate virtual environment
venv\Scripts\activate

# Run the script
python hybrid_chunking.py
```

## Installation Steps

### 1. Virtual Environment (Already Created)
The virtual environment `venv` has been created for you.

### 2. Install Dependencies
```bash
venv\Scripts\pip.exe install -r requirements.txt
```

This installs:
- **docling** - Document processing library
- **transformers** - Tokenization and models
- **torch** - PyTorch for model operations
- **openai-whisper** - Audio transcription
- **hf-xet** - Hugging Face extras

### 3. Run the Script
```bash
python hybrid_chunking.py
```

## Configuration (.env file)

The `.env` file contains configuration variables:

```env
# Document Processing
MAX_TOKENS=512
INPUT_DOCUMENTS_PATH=documents
OUTPUT_CHUNKS_PATH=outputs

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Database (from your docker-compose.yml)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=postgres_db
```

## What the Script Does

1. **Loads** `documents/technical-architecture-guide.pdf`
2. **Converts** it using Docling
3. **Chunks** it intelligently (max 512 tokens per chunk)
4. **Analyzes** chunk statistics
5. **Saves** results to `outputs/output_chunks.txt`

## Expected Output

```
============================================================
Hybrid Chunking with Docling
============================================================

Input: documents/technical-architecture-guide.pdf
Max tokens per chunk: 512

📄 Processing: technical-architecture-guide.pdf
   Step 1: Converting document...
   Step 2: Initializing tokenizer...
   Step 3: Creating chunker (max 512 tokens)...
   Step 4: Generating chunks...

============================================================
CHUNK ANALYSIS
============================================================

--- Chunk 0 ---
Tokens: 487
Characters: 2341
Preview: ...

✓ Chunks saved to: outputs/output_chunks.txt
```

## Database Integration (Optional)

Your docker-compose.yml includes PostgreSQL with pgvector. To connect:

1. **Start the database:**
   ```bash
   cd C:\Users\Administrator\Desktop\Docker\n8n
   docker-compose up -d postgres
   ```

2. **Verify connection:**
   ```bash
   docker exec -it postgres psql -U postgres_user -d postgres_db
   ```

3. **Connection string:**
   ```
   postgresql://postgres_user:postgres_password@localhost:5432/postgres_db
   ```

## Troubleshooting

### Issue: Module not found
**Solution:** Ensure you activated the virtual environment
```bash
venv\Scripts\activate
```

### Issue: torch installation fails
**Solution:** Install CPU-only version
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue: Out of memory
**Solution:** Reduce MAX_TOKENS in .env file
```env
MAX_TOKENS=256
```

### Issue: PDF not found
**Solution:** Verify the PDF exists
```bash
dir documents\technical-architecture-guide.pdf
```

## Next Steps

1. ✓ Run the script to test it works
2. Process other documents (PDFs, DOCX, etc.)
3. Integrate with your n8n workflows
4. Store chunks in PostgreSQL with pgvector
5. Build RAG application with embeddings

## Additional Scripts

To process multiple documents or different formats, modify `hybrid_chunking.py`:

```python
# Process all PDFs
pdf_files = [
    "documents/technical-architecture-guide.pdf",
    "documents/q4-2024-business-review.pdf",
    "documents/client-review-globalfinance.pdf"
]

for pdf_path in pdf_files:
    chunks, tokenizer, chunker = chunk_document(pdf_path, max_tokens=512)
    # ... save each separately
```

## Resources

- **Docling Docs**: https://docling-project.github.io/docling/
- **Hybrid Chunking**: https://docling-project.github.io/docling/concepts/chunking/
- **Transformers**: https://huggingface.co/docs/transformers/
