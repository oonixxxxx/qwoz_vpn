from __future__ import annotations

from io import BytesIO

import qrcode
from aiogram.types import BufferedInputFile


def build_qr_image(data: str, filename: str = "qr.png") -> BufferedInputFile:
    qr = qrcode.QRCode(border=2, box_size=6)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return BufferedInputFile(buffer.getvalue(), filename=filename)
