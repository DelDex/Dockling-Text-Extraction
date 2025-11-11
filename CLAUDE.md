# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Vector Database Document Processing** project focused on converting complex documents (PDFs, DOCX, PPTX, audio) into chunked text suitable for RAG (Retrieval Augmented Generation) systems. The project uses **Docling** for advanced document processing with two processing modes: full-featured (Docling) and lightweight (PyPDF2).

## Core Architecture

### Two Processing Approaches

The codebase implements dual processing strategies to handle different system constraints:

**1. Full-Featured Processing (`hybrid_chunking.py`)**
- Uses Docling's HybridChunker for structure-aware chunking
- Preserves document structure (tables, sections, hierarchies)
- Memory requirement: 4-8GB RAM per document
- Best for: Production RAG systems requiring high-quality semantic chunks
- Note: Table extraction and OCR are **disabled by default** in current configuration (lines 178-181) to reduce memory usage

**2. Lightweight Processing (`hybrid_chunking_lightweight.py`)**
- Uses PyPDF2 for simple text extraction
- Memory requirement: 100-200MB per document
- Best for: Text-based PDFs on memory-constrained systems
- Limitations: No table extraction, no OCR, no structure preservation

### Key Design Decision

The scripts use **shared converter and tokenizer instances** across batch processing (see `hybrid_chunking.py:173-192`) to prevent memory exhaustion when processing multiple documents.

## Running the Code

### Environment Setup

**Activate virtual environment:**
```bash
venv\Scripts\activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Important PyTorch Note:**
PyTorch must be installed separately due to Windows DLL issues with version 2.9.0:
```bash
pip install torch==2.5.0+cpu torchvision==0.20.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

### Running Document Processing

**Full-featured processing (requires 8GB+ RAM):**
```bash
python hybrid_chunking.py
```

**Lightweight processing (works on 4GB RAM):**
```bash
python hybrid_chunking_lightweight.py
```

**Quick test with batch script:**
```bash
run.bat
```

### Testing Imports

Verify all dependencies are working:
```bash
venv\Scripts\python.exe -c "import torch; import transformers; import docling; print('All imports successful!'); print('PyTorch version:', torch.__version__); print('Transformers version:', transformers.__version__); print('Docling imported successfully')"
```

## Document Processing Flow

### Input Structure

```
documents/
├── knowledge/          # SONiC technical documentation (processed by scripts)
├── *.pdf              # General PDFs
├── *.docx             # Word documents
├── *.pptx             # PowerPoint files
└── *.mp3              # Audio files (transcription support available)
```

### Output Structure

```
outputs/
└── <filename>_chunks.txt    # Chunked text with separators and metadata
```

Each chunk file contains:
- Chunk separator headers (`CHUNK N`)
- Contextualized text (preserves headings via `chunker.contextualize()`)
- Token counts and character counts in analysis output

### Processing Configuration

**Max tokens per chunk:** 512 (configured for sentence-transformers/all-MiniLM-L6-v2)
- This matches typical embedding model limits
- Adjustable via `max_tokens` parameter in functions

**Chunking strategy (full-featured):**
- `merge_peers=True`: Combines small adjacent chunks for better context
- Respects semantic boundaries (paragraphs, sections, tables)
- Token-aware splitting prevents exceeding embedding limits

**Chunking strategy (lightweight):**
- Sentence-based splitting with token limits
- Falls back to word-level splitting for oversized sentences
- Simple regex sentence detection (`hybrid_chunking_lightweight.py:46-49`)

## Important Implementation Details

### Memory Management

The full-featured Docling processor (`hybrid_chunking.py`) implements critical memory optimizations:

1. **Shared Resources Pattern** (lines 173-192):
   - Single DocumentConverter instance reused across all files
   - Single AutoTokenizer instance shared
   - Prevents memory exhaustion from repeated model loading

2. **Minimal Pipeline Configuration**:
   ```python
   pipeline_options.do_table_structure = False  # Disables TableFormer model
   pipeline_options.do_ocr = False             # Disables OCR
   ```
   This configuration extracts **embedded text only**, suitable for text-based PDFs but sacrificing table extraction and OCR capabilities.

### Batch Processing

Both scripts support automatic batch processing:
- Scans `documents/knowledge/` directory
- Processes all supported file types (PDF, DOCX, PPTX, MD)
- Generates uniquely named output files per document
- Provides per-file error handling with traceback

### Chunk Contextualization

The full-featured processor uses `chunker.contextualize(chunk=chunk)` (`hybrid_chunking.py:136`) to preserve document context:
- Includes parent section headings
- Maintains hierarchical structure information
- Critical for RAG system comprehension

## Known System Constraints

**Current Development System:**
- Limited to ~4GB available RAM
- Cannot run full Docling processing with table extraction/OCR enabled
- Successfully processes documents with lightweight PyPDF2 approach
- All 6 SONiC documentation files processed (~3 minutes total)

**Recommendation for Production:**
- Process documents on cloud instance (AWS EC2 t3.large, Google Colab) with 8GB+ RAM
- Enable table extraction and OCR for technical documentation
- One-time processing cost: ~$0.50-1.00
- See `COMPARISON_AND_RECOMMENDATIONS.md` for detailed analysis

## Quality Trade-offs

**PyPDF2 Output Issues:**
- Configuration tables become unreadable concatenated text
- Command reference sections lose structure
- No context preservation for semantic relationships
- Example from CLI Reference Guide: "aaa accounting login default aaa authentication failthrough aaa authentication login default..." (all commands mashed together)

**Docling Output Benefits (when enabled):**
- Preserved table structures with column/row relationships
- Section headings maintained in chunks
- Context-aware boundaries respect semantic meaning
- Metadata includes document hierarchy information

## Integration Points

**PostgreSQL + PGVector (from docker-compose.yml):**
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=postgres_db
```

Connection string: `postgresql://postgres_user:postgres_password@localhost:5432/postgres_db`

The chunked outputs are designed for insertion into vector databases with embedding models.

## Audio Transcription Support

While not currently in active use, the project includes Whisper ASR dependencies for audio transcription:
- Requires FFmpeg installation
- Supports MP3, WAV, M4A, FLAC formats
- Provides timestamp-aware transcripts
- Reference implementation pattern available in Docling documentation

## Embedding Model

Default tokenizer: `sentence-transformers/all-MiniLM-L6-v2`
- 512 token limit
- Compatible with common RAG pipelines
- Pre-loaded in both processing scripts for consistency
