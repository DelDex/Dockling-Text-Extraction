"""
Hybrid Chunking with Docling - HPC Optimized
=============================================

This script demonstrates Docling's HybridChunker for intelligent
document chunking that respects both document structure and
token limits.

CONFIGURATION: HPC-Optimized (Full Features Enabled)
- Table extraction: ENABLED (TableFormer model)
- OCR: ENABLED (for scanned documents)
- High-resolution image processing: ENABLED (2.0x scale)
- Page/picture image generation: ENABLED

What is Hybrid Chunking?
- Combines hierarchical document structure with token-aware splitting
- Respects semantic boundaries (paragraphs, sections, tables)
- Ensures chunks fit within token limits for embeddings
- Preserves metadata and document hierarchy

Why use it?
- Better for RAG systems than naive text splitting
- Maintains semantic coherence within chunks
- Optimized for embedding models with token limits
- Preserves document structure and context
- Extracts tables with proper structure preservation
- Handles scanned PDFs via OCR

Usage:
    python hybrid_chunking.py

Requirements:
    - Recommended: 8GB+ RAM for full feature set
    - HPC environment recommended for batch processing
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.chunking import HybridChunker
from transformers import AutoTokenizer
from pathlib import Path
import os
import glob

def chunk_document(file_path: str, max_tokens: int = 512, converter=None, tokenizer=None):
    """Convert and chunk document using HybridChunker.

    Args:
        file_path: Path to document to process
        max_tokens: Maximum tokens per chunk
        converter: Reusable DocumentConverter instance (prevents memory exhaustion)
        tokenizer: Reusable AutoTokenizer instance (prevents memory exhaustion)
    """

    print(f"\n[*] Processing: {Path(file_path).name}")

    # Step 1: Convert document to DoclingDocument
    print("   Step 1: Converting document...")
    if converter is None:
        converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document

    # Step 2: Initialize tokenizer (using sentence-transformers model)
    if tokenizer is None:
        print("   Step 2: Initializing tokenizer...")
        model_id = "sentence-transformers/all-MiniLM-L6-v2"
        tokenizer = AutoTokenizer.from_pretrained(model_id)
    else:
        print("   Step 2: Using shared tokenizer...")

    # Step 3: Create HybridChunker
    print(f"   Step 3: Creating chunker (max {max_tokens} tokens)...")
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        merge_peers=True  # Merge small adjacent chunks
    )

    # Step 4: Generate chunks
    print("   Step 4: Generating chunks...")
    chunk_iter = chunker.chunk(dl_doc=doc)
    chunks = list(chunk_iter)

    return chunks, chunker

def analyze_chunks(chunks, tokenizer):
    """Analyze and display chunk statistics."""

    print("\n" + "=" * 60)
    print("CHUNK ANALYSIS")
    print("=" * 60)

    total_tokens = 0
    chunk_sizes = []

    for i, chunk in enumerate(chunks):
        # Get text content
        text = chunk.text
        tokens = tokenizer.encode(text)
        token_count = len(tokens)

        total_tokens += token_count
        chunk_sizes.append(token_count)

        # Display first 3 chunks in detail
        if i < 3:
            print(f"\n--- Chunk {i} ---")
            print(f"Tokens: {token_count}")
            print(f"Characters: {len(text)}")
            print(f"Preview: {text[:150]}...")

            # Show metadata if available
            if hasattr(chunk, 'meta') and chunk.meta:
                print(f"Metadata: {chunk.meta}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total chunks: {len(chunks)}")
    print(f"Total tokens: {total_tokens}")
    print(f"Average tokens per chunk: {total_tokens / len(chunks):.1f}")
    print(f"Min tokens: {min(chunk_sizes)}")
    print(f"Max tokens: {max(chunk_sizes)}")

    # Token distribution
    print(f"\nToken distribution:")
    ranges = [(0, 128), (128, 256), (256, 384), (384, 512)]
    for start, end in ranges:
        count = sum(1 for size in chunk_sizes if start <= size < end)
        print(f"  {start}-{end} tokens: {count} chunks")

def save_chunks(chunks, chunker, output_path: str):
    """Save chunks to file with separators, preserving context and headings."""

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            f.write(f"{'='*60}\n")
            f.write(f"CHUNK {i}\n")
            f.write(f"{'='*60}\n")

            # Use contextualize to preserve headings and metadata
            contextualized_text = chunker.contextualize(chunk=chunk)
            f.write(contextualized_text)
            f.write("\n\n")

    print(f"\n[OK] Chunks saved to: {output_path}")
    print("   (with preserved headings and document context)")

def main():
    print("=" * 60)
    print("Hybrid Chunking with Docling - Batch Processing")
    print("=" * 60)

    # Configuration
    documents_dir = "documents/knowledge"
    max_tokens = 512  # Typical limit for embedding models

    # Supported file extensions
    supported_extensions = ['*.pdf', '*.docx', '*.pptx', '*.md']

    # Find all supported documents
    all_files = []
    for ext in supported_extensions:
        pattern = os.path.join(documents_dir, ext)
        all_files.extend(glob.glob(pattern))

    if not all_files:
        print(f"\n[ERROR] No supported documents found in '{documents_dir}/' folder")
        print(f"Supported formats: PDF, DOCX, PPTX, MD")
        return

    print(f"\nFound {len(all_files)} document(s) to process")
    print(f"Max tokens per chunk: {max_tokens}")
    print("\nSupported files:")
    for file in all_files:
        print(f"  - {Path(file).name}")
    print()

    # Initialize shared resources (prevents memory exhaustion)
    print("\n[*] Initializing shared converter and tokenizer...")
    print("   (Using FULL-FEATURED configuration - optimized for HPC)")
    print("   (Table extraction, OCR, and structure preservation enabled)")

    # Configure PDF pipeline with MAXIMUM quality options for HPC
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True   # Enable TableFormer for table extraction
    pipeline_options.do_ocr = True              # Enable OCR for scanned documents
    pipeline_options.images_scale = 2.0         # Higher resolution for better OCR (default: 1.0)
    pipeline_options.generate_page_images = True  # Generate page images for analysis
    pipeline_options.generate_picture_images = True  # Extract embedded images

    # Create converter with FULL-FEATURED options for HPC
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    print("[OK] Shared resources initialized")

    # Process each file
    processed_count = 0
    failed_count = 0

    for file_path in all_files:
        file_name = Path(file_path).stem  # Get filename without extension
        print("\n" + "=" * 60)
        print(f"Processing: {Path(file_path).name}")
        print("=" * 60)

        try:
            # Generate chunks (using shared converter and tokenizer)
            chunks, chunker = chunk_document(file_path, max_tokens, converter, tokenizer)

            # Analyze chunks
            analyze_chunks(chunks, tokenizer)

            # Save chunks with unique filename
            output_path = f"outputs/{file_name}_chunks.txt"
            save_chunks(chunks, chunker, output_path)

            processed_count += 1

        except Exception as e:
            print(f"\n[ERROR] Failed to process {Path(file_path).name}: {e}")
            failed_count += 1
            import traceback
            traceback.print_exc()

    # Final summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"[+] Successfully processed: {processed_count} file(s)")
    if failed_count > 0:
        print(f"[-] Failed: {failed_count} file(s)")
    print(f"\n[+] Output location: outputs/")

    print("\n" + "=" * 60)
    print("KEY BENEFITS OF HYBRID CHUNKING")
    print("=" * 60)
    print("[+] Respects document structure (sections, paragraphs)")
    print("[+] Token-aware (fits embedding model limits)")
    print("[+] Semantic coherence (doesn't split mid-sentence)")
    print("[+] Metadata preservation (headings, document context)")
    print("[+] Ready for RAG (optimized chunk sizes)")

if __name__ == "__main__":
    main()
