# -*- coding: utf-8 -*-
"""Mô hình dữ liệu: Section (khối lệnh) và Patch (tệp patch)."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Section:
    """Một khối lệnh trong patch.txt.

    body: ánh xạ khóa -> giá trị; giá trị giữ nguyên thụt lề nội dung
          (dòng đầu được cắt thụt lề của tệp, các dòng tiếp theo giữ nguyên).
    """

    type: str
    body: Dict[str, str]
    order: int
    closed: bool = True
    name: Optional[str] = None
    raw: str = ""

    def get(self, key: str, default: str = "") -> str:
        return self.body.get(key, default)


@dataclass
class Patch:
    """Một patch hoàn chỉnh (từ .zip, patch.txt hoặc thư mục)."""

    source: str
    min_engine_ver: Optional[str] = None
    author: Optional[str] = None
    package: Optional[str] = None
    sections: List[Section] = field(default_factory=list)
    # Tài nguyên kèm theo khi nguồn là .zip (tên -> nội dung bytes)
    assets: Dict[str, bytes] = field(default_factory=dict)
    # Thư mục chứa tài nguyên khi nguồn là thư mục / patch.txt
    asset_root: Optional[str] = None
    issues: List[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        base = os.path.basename(self.source)
        for suffix in (".zip", ".txt"):
            if base.lower().endswith(suffix):
                base = base[: -len(suffix)]
                break
        return base

    def section_types(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for s in self.sections:
            counts[s.type] = counts.get(s.type, 0) + 1
        return counts
