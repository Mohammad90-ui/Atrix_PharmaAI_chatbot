
# Pre-compute embeddings script
import sys
import os

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataLoader
from retriever import Retriever

def main():
    print("Loading data...")
    loader = DataLoader(
        excel_path="Pharma_Clinical_Trial_AllDrugs.xlsx",
        docx_path="Pharma_Clinical_Trial_Notes.docx"
    )
    excel_data, doc_chunks, excel_chunks = loader.load_all()
    print(f"Loaded {len(doc_chunks)} doc chunks and {len(excel_chunks)} excel chunks")

    print("Building index...")
    retriever = Retriever()
    retriever.build_index(doc_chunks, excel_chunks)

    output_path = "index.npz"
    print(f"Saving to {output_path}...")
    retriever.save_index(output_path)
    print("Done!")

if __name__ == "__main__":
    main()
