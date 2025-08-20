"""QR code generation for Packster download commands."""

import qrcode
from pathlib import Path
from typing import Optional


def generate_qr_code(data: str, output_path: Optional[Path] = None) -> Path:
    """Generate a QR code containing the download command.
    
    Args:
        data: The download command or URL to encode
        output_path: Optional path to save the QR code image
        
    Returns:
        Path to the generated QR code image
    """
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to file
    if output_path is None:
        output_path = Path("packster-download-qr.png")
    
    img.save(output_path)
    return output_path


def generate_download_qr(download_url: str, file_name: str, output_path: Optional[Path] = None) -> Path:
    """Generate a QR code for the download URL only.
    
    Args:
        download_url: The download URL
        file_name: The name of the file to download
        output_path: Optional path to save the QR code image
        
    Returns:
        Path to the generated QR code image
    """
    # Create a simple QR code with just the URL
    # This makes it much shorter and easier to scan
    qr_data = download_url
    
    return generate_qr_code(qr_data, output_path)
