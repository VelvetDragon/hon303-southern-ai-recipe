import argparse, pathlib
from pdfminer.high_level import extract_text

def convert(pdf_path: pathlib.Path, outdir: pathlib.Path):
    outdir.mkdir(parents=True, exist_ok=True)
    txt_path = outdir / (pdf_path.stem + ".txt")
    print(f"Converting {pdf_path.name} → {txt_path.relative_to(pathlib.Path().resolve())}")
    txt_path.write_text(extract_text(pdf_path), encoding="utf-8")
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert OCR PDF to plain text")
    parser.add_argument("pdf", type=pathlib.Path, help="Path to OCR PDF file")
    parser.add_argument("--outdir", type=pathlib.Path, default=pathlib.Path("data/raw/cookbooks"),
                        help="Output directory for .txt (default: data/raw/cookbooks)")
    args = parser.parse_args()
    convert(args.pdf, args.outdir)
