import os
import sys
from pathlib import Path
from zipfile import ZipFile
import requests


RECORD_ID = 17849564  # Zenodo record id containing the atlases archive
ZENODO_URL = f"https://zenodo.org/record/{RECORD_ID}/files/atlases.zip"

# Default destination: package-local `atlases` directory next to this module
DEST_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "atlases"
)


def download_atlases():
    """
    Download atlas archive from Zenodo (RECORD_ID) and extract into
    the package-local `atlases` directory (DEFAULT_DEST_DIR).

    Returns
    -------
    dest_dir : str
        Returns the destination directory (str).
    """
    # Create destination directory if it doesn't exist
    dest_dir = Path(DEST_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Download .zip file from zenodo
    atlases_zip = requests.get(ZENODO_URL, stream=False)
    dest_file = os.path.join(dest_dir, "atlases.zip")
    with open(dest_file, 'wb') as f:
        f.write(atlases_zip.content)
    
    # Extract .zip file
    with ZipFile(dest_file, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)

        
    return dest_dir

def main():
    path = download_atlases()
    print(f"Atlases available at: {path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
