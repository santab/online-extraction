from __future__ import annotations

from types import ModuleType

from extraction_agent.modalities import docx, excel, image, pdf

REGISTRY: dict[str, ModuleType] = {
    "pdf": pdf,
    "excel": excel,
    "image": image,
    "docx": docx,
}


def get_modality(name: str) -> ModuleType:
    try:
        return REGISTRY[name]
    except KeyError:
        raise ValueError(f"unknown modality {name!r}, known: {sorted(REGISTRY)}") from None
