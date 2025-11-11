"""
Lightweight PDF Chunking
=========================

This script provides a memory-efficient alternative to Docling's HybridChunker
for systems with limited RAM. It uses PyPDF2 for simple text extraction.

Trade-offs:
- Lower memory usage (no ML models loaded)
- Faster processing
- No table extraction or OCR
- No document structure preservation
- Simple sentence-based chunking with token limits

Best for:
- Text-based PDFs (not scanned documents)
- Systems with limited RAM
- When you need basic text chunking without advanced features

Usage:
    python hybrid_chunking_lightweight.py
"""

import PyPDF2
from transformers import AutoTokenizer
from pathlib import Path
import os
import glob
import re


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file using PyPDF2."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {e}")


def split_into_sentences(text: str) -> list:
    """Split text into sentences using simple regex."""
    # Simple sentence splitting - can be improved with nltk.sent_tokenize
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(text: str, tokenizer, max_tokens: int = 512) -> list:
    """
    Chunk text into segments that fit within token limits.

    Strategy:
    1. Split text into sentences
    2. Combine sentences until we approach the token limit
    3. Create new chunk when adding next sentence would exceed limit
    """
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = len(tokenizer.encode(sentence, add_special_tokens=False))

        # If single sentence exceeds max_tokens, split it into smaller pieces
        if sentence_tokens > max_tokens:
            # Save current chunk if it has content
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_tokens = 0

            # Split long sentence by words
            words = sentence.split()
            word_chunk = []
            word_tokens = 0

            for word in words:
                word_token_count = len(tokenizer.encode(word, add_special_tokens=False))
                if word_tokens + word_token_count > max_tokens:
                    if word_chunk:
                        chunks.append(" ".join(word_chunk))
                    word_chunk = [word]
                    word_tokens = word_token_count
                else:
                    word_chunk.append(word)
                    word_tokens += word_token_count

            if word_chunk:
                chunks.append(" ".join(word_chunk))
            continue

        # Check if adding this sentence would exceed the limit
        if current_tokens + sentence_tokens > max_tokens:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_tokens = sentence_tokens
        else:
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_tokens += sentence_tokens

    # Add remaining chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def analyze_chunks(chunks: list, tokenizer, file_name: str):
    """Analyze and display chunk statistics."""
    print("\n" + "=" * 60)
    print(f"CHUNK ANALYSIS: {file_name}")
    print("=" * 60)

    total_tokens = 0
    chunk_sizes = []

    for i, chunk in enumerate(chunks):
        tokens = tokenizer.encode(chunk)
        token_count = len(tokens)

        total_tokens += token_count
        chunk_sizes.append(token_count)

        # Display first 2 chunks in detail
        if i < 2:
            print(f"\n--- Chunk {i} ---")
            print(f"Tokens: {token_count}")
            print(f"Characters: {len(chunk)}")
            print(f"Preview: {chunk[:150]}...")

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total chunks: {len(chunks)}")
    print(f"Total tokens: {total_tokens}")
    if len(chunks) > 0:
        print(f"Average tokens per chunk: {total_tokens / len(chunks):.1f}")
        print(f"Min tokens: {min(chunk_sizes)}")
        print(f"Max tokens: {max(chunk_sizes)}")

        # Token distribution
        print(f"\nToken distribution:")
        ranges = [(0, 128), (128, 256), (256, 384), (384, 512)]
        for start, end in ranges:
            count = sum(1 for size in chunk_sizes if start <= size < end)
            print(f"  {start}-{end} tokens: {count} chunks")


def save_chunks(chunks: list, output_path: str):
    """Save chunks to file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            f.write(f"{'='*60}\n")
            f.write(f"CHUNK {i}\n")
            f.write(f"{'='*60}\n")
            f.write(chunk)
            f.write("\n\n")

    print(f"\n[OK] Chunks saved to: {output_path}")


def process_document(file_path: str, tokenizer, max_tokens: int = 512):
    """Process a single PDF document."""
    file_name = Path(file_path).name
    print(f"\n[*] Processing: {file_name}")

    # Extract text
    print("   Step 1: Extracting text from PDF...")
    text = extract_text_from_pdf(file_path)

    if not text.strip():
        raise Exception("No text extracted from PDF. It may be scanned/image-based.")

    print(f"   Step 2: Extracted {len(text)} characters")

    # Chunk text
    print(f"   Step 3: Chunking text (max {max_tokens} tokens)...")
    chunks = chunk_text(text, tokenizer, max_tokens)

    return chunks


def main():
    print("=" * 60)
    print("Lightweight PDF Chunking - Batch Processing")
    print("=" * 60)
    print("NOTE: Using PyPDF2 (low memory) instead of Docling")
    print("      Only works with text-based PDFs (not scanned)")
    print()

    # Configuration
    documents_dir = "documents/knowledge"
    max_tokens = 512

    # Find all PDFs
    pdf_files = glob.glob(os.path.join(documents_dir, "*.pdf"))

    if not pdf_files:
        print(f"\n[ERROR] No PDF files found in '{documents_dir}/' folder")
        return

    print(f"Found {len(pdf_files)} PDF document(s) to process")
    print(f"Max tokens per chunk: {max_tokens}")
    print("\nFiles:")
    for file in pdf_files:
        print(f"  - {Path(file).name}")
    print()

    # Initialize tokenizer (reused across all documents)
    print("[*] Initializing tokenizer...")
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    print("[OK] Tokenizer initialized")

    # Process each file
    processed_count = 0
    failed_count = 0

    for file_path in pdf_files:
        file_name = Path(file_path).stem
        print("\n" + "=" * 60)
        print(f"Processing: {Path(file_path).name}")
        print("=" * 60)

        try:
            # Process document
            chunks = process_document(file_path, tokenizer, max_tokens)

            # Analyze chunks
            analyze_chunks(chunks, tokenizer, Path(file_path).name)

            # Save chunks
            output_path = f"outputs/{file_name}_chunks.txt"
            save_chunks(chunks, output_path)

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
    print("ABOUT THIS LIGHTWEIGHT VERSION")
    print("=" * 60)
    print("[+] Uses PyPDF2 (no ML models = low memory)")
    print("[+] Sentence-based chunking with token limits")
    print("[+] Works with text-based PDFs only")
    print("[-] No table extraction or OCR")
    print("[-] No document structure preservation")
    print("\n[INFO] For advanced features, use Docling on a system")
    print("       with more RAM (8GB+ recommended)")


if __name__ == "__main__":
    main()
