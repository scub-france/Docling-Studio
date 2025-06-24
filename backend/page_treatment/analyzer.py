#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "transformers>=4.50",
#     "torch",
#     "pillow",
#     "requests",
#     "argparse",
#     "pdf2image",
#     "docling_core",
# ]
# ///

import argparse
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image
from pdf2image import convert_from_bytes
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.document import DocTagsDocument

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.utils import ensure_results_folder, load_pdf_page
from backend.config import MODEL_PATH, MAX_TOKENS, DEFAULT_DPI

def parse_arguments():
    results_dir = ensure_results_folder()

    parser = argparse.ArgumentParser(description='Convert an image or PDF to docling format')
    parser.add_argument('--image', '-i', type=str, required=True,
                        help='Path to local image file, PDF file, or URL')
    parser.add_argument('--prompt', '-p', type=str, default="Convert this page to docling.",
                        help='Prompt for the model')
    parser.add_argument('--output', '-o', type=str, default=str(results_dir / "output.html"),
                        help='Output file path')
    parser.add_argument('--page', type=int, default=1,
                        help='Page number to process for PDF files (starts at 1)')
    parser.add_argument('--dpi', type=int, default=DEFAULT_DPI,
                        help='DPI for PDF rendering')
    parser.add_argument('--start-page', type=int, default=1,
                        help='Start processing PDF from this page number')
    parser.add_argument('--end-page', type=int, default=None,
                        help='Stop processing PDF at this page number')
    return parser.parse_args()

def load_image(image_path, page_num=1, dpi=DEFAULT_DPI):
    if urlparse(image_path).scheme in ['http', 'https']:
        response = requests.get(image_path, stream=True, timeout=10)
        response.raise_for_status()

        if image_path.lower().endswith('.pdf') or response.headers.get('Content-Type') == 'application/pdf':
            print(f"Converting PDF from URL (page {page_num})...")
            pdf_images = convert_from_bytes(response.content, dpi=dpi, first_page=page_num, last_page=page_num)
            if not pdf_images:
                raise Exception(f"Could not extract page {page_num} from PDF")
            return pdf_images[0].convert("RGB")
        else:
            return Image.open(response.raw).convert("RGB")
    else:
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"File not found: {image_path}")

        if image_path.suffix.lower() == '.pdf':
            return load_pdf_page(str(image_path), page_num, dpi).convert("RGB")
        else:
            return Image.open(image_path).convert("RGB")

def process_page(model, processor, args, pil_image, page_num=1):
    results_dir = ensure_results_folder()

    if args.start_page == args.end_page and args.start_page == page_num:
        doctags_path = results_dir / "output.doctags.txt"
        output_path = results_dir / "output.html"
    else:
        doctags_path = results_dir / f"output_page{page_num}.doctags.txt"
        output_path = results_dir / f"output_page{page_num}.html"

    print(f"Processing page {page_num}")

    # Préparer les messages
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": args.prompt}
            ]
        }
    ]

    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)

    device = next(model.parameters()).device
    inputs = processor(text=prompt, images=[pil_image], return_tensors="pt").to(device)

    # Génération
    generated_ids = model.generate(**inputs, max_new_tokens=MAX_TOKENS)
    prompt_length = inputs.input_ids.shape[1]
    trimmed_generated_ids = generated_ids[:, prompt_length:]

    doctags = processor.batch_decode(trimmed_generated_ids, skip_special_tokens=False)[0].lstrip()
    with open(doctags_path, "w", encoding="utf-8") as f:
        f.write(doctags)
    print(f"DocTags saved to {doctags_path}")

    doctags_doc = DocTagsDocument.from_doctags_and_image_pairs([doctags], [pil_image])
    doc = DoclingDocument.load_from_doctags(doctags_doc, document_name=f"Page {page_num}")
    html = doc.export_to_html()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML exported to {output_path}")

    return output_path

def main():
    args = parse_arguments()
    print("Loading model and processor...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AutoModelForVision2Seq.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        _attn_implementation="flash_attention_2" if device.type == "cuda" else "eager"
    ).to(device)
    processor = AutoProcessor.from_pretrained(MODEL_PATH)

    start_page = args.start_page
    end_page = args.end_page or args.page

    for page_num in range(start_page, end_page + 1):
        pil_image = load_image(args.image, page_num=page_num, dpi=args.dpi)
        process_page(model, processor, args, pil_image, page_num)

if __name__ == "__main__":
    main()
