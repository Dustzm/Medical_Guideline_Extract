# 导入各个prompt模块
from .layout_prompt import build_prompt as build_layout_prompt
from .core_segmentation_prompt import build_prompt as build_core_segmentation_prompt
from .edge_extract_prompt import build_prompt as build_others_prompt
from .core_extract_prompt import build_prompt as build_core_prompt

__all__ = [
    'build_layout_prompt',
    'build_core_segmentation_prompt',
    'build_others_prompt',
    'build_core_prompt'
]