"""
CAMPUSX — Discover People Behind the Work System
Design System: Colors, Typography, Card Styles, and Widget Factory
"""

import os
from pathlib import Path
from typing import Optional, Tuple
import customtkinter as ctk
from PIL import Image

from config import (
    COLOR_DEEP_NAVY,
    COLOR_ACADEMIC_BLUE,
    COLOR_BRIGHT_BLUE,
    COLOR_PURPLE,
    COLOR_CYAN,
    COLOR_SOFT_BG,
    COLOR_WHITE,
    COLOR_DARK_TEXT,
    COLOR_SECONDARY_TEXT,
    COLOR_BORDER,
    COLOR_CARD_BG,
    COLOR_MUTED_BG,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DANGER,
    LOGO_PATH,
    ASSETS_DIR
)

# Set base CustomTkinter appearance
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")
import tkinter as tk

def _resolve_font_family() -> str:
    """Prefer Inter if available on the system, otherwise fallback to Segoe UI / sans-serif."""
    try:
        import tkinter as tk
        from tkinter import font
        root = tk._default_root
        if root is None:
            temp = tk.Tk()
            temp.withdraw()
            families = set(font.families(temp))
            temp.destroy()
        else:
            families = set(font.families(root))
        if "Inter" in families:
            return "Inter"
        if "Segoe UI" in families:
            return "Segoe UI"
    except Exception:
        pass
    return "Segoe UI"


FONT_FAMILY = _resolve_font_family()


class Theme:
    """Central repository of design system styles."""
    # Typography Font Family
    FONT_FAMILY = FONT_FAMILY

    # Palette
    NAVY = COLOR_DEEP_NAVY
    ACADEMIC_BLUE = COLOR_ACADEMIC_BLUE
    BRIGHT_BLUE = COLOR_BRIGHT_BLUE
    PURPLE = COLOR_PURPLE
    CYAN = COLOR_CYAN
    SOFT_BG = COLOR_SOFT_BG
    WHITE = COLOR_WHITE
    DARK_TEXT = COLOR_DARK_TEXT
    SECONDARY_TEXT = COLOR_SECONDARY_TEXT
    BORDER = COLOR_BORDER
    CARD_BG = COLOR_CARD_BG
    MUTED_BG = COLOR_MUTED_BG
    SUCCESS = COLOR_SUCCESS
    WARNING = COLOR_WARNING
    DANGER = COLOR_DANGER

    # Typography
    FONT_HERO = (FONT_FAMILY, 32, "bold")
    FONT_TITLE = (FONT_FAMILY, 22, "bold")
    FONT_SUBTITLE = (FONT_FAMILY, 15, "bold")
    FONT_SECTION = (FONT_FAMILY, 13, "bold")
    FONT_BODY = (FONT_FAMILY, 11)
    FONT_BODY_BOLD = (FONT_FAMILY, 11, "bold")
    FONT_CAPTION = (FONT_FAMILY, 9)
    FONT_TAGLINE = (FONT_FAMILY, 11, "bold")

    # Corner radii
    RADIUS_CARD = 12
    RADIUS_BUTTON = 8
    RADIUS_BADGE = 14
    RADIUS_INPUT = 8


def get_logo_image(size: Tuple[int, int] = (220, 58)) -> Optional[ctk.CTkImage]:
    """Load the official CAMPUSX logo as a CTkImage."""
    if LOGO_PATH.exists():
        try:
            pil_img = Image.open(LOGO_PATH)
            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception:
            return None
    return None


def get_icon_image(size: Tuple[int, int] = (36, 36)) -> Optional[ctk.CTkImage]:
    """Load the CAMPUSX emblem icon."""
    icon_path = ASSETS_DIR / "campusx_icon.png"
    if icon_path.exists():
        try:
            pil_img = Image.open(icon_path)
            return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        except Exception:
            return None
    return None


def create_card(
    parent,
    fg_color: str = Theme.CARD_BG,
    border_color: str = Theme.BORDER,
    border_width: int = 1,
    corner_radius: int = Theme.RADIUS_CARD,
    **kwargs
) -> ctk.CTkFrame:
    """Create a standardized CAMPUSX rounded card with border."""
    return ctk.CTkFrame(
        parent,
        fg_color=fg_color,
        border_color=border_color,
        border_width=border_width,
        corner_radius=corner_radius,
        **kwargs
    )


def create_primary_button(
    parent,
    text: str,
    command=None,
    width: int = 140,
    height: int = 38,
    **kwargs
) -> ctk.CTkButton:
    """Create a primary button using Academic Blue with smooth hover."""
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        corner_radius=Theme.RADIUS_BUTTON,
        fg_color=Theme.ACADEMIC_BLUE,
        hover_color=Theme.NAVY,
        text_color=Theme.WHITE,
        font=Theme.FONT_BODY_BOLD,
        **kwargs
    )


def create_secondary_button(
    parent,
    text: str,
    command=None,
    width: int = 120,
    height: int = 38,
    **kwargs
) -> ctk.CTkButton:
    """Create an outlined secondary button."""
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        corner_radius=Theme.RADIUS_BUTTON,
        fg_color=Theme.WHITE,
        hover_color=Theme.MUTED_BG,
        text_color=Theme.NAVY,
        border_color=Theme.BORDER,
        border_width=1,
        font=Theme.FONT_BODY_BOLD,
        **kwargs
    )


def create_badge(
    parent,
    text: str,
    bg_color: str = "#EBF4FF",
    text_color: str = Theme.ACADEMIC_BLUE,
    font=Theme.FONT_CAPTION
) -> ctk.CTkLabel:
    """Create a subtle pill badge."""
    return ctk.CTkLabel(
        parent,
        text=f"  {text}  ",
        fg_color=bg_color,
        text_color=text_color,
        corner_radius=Theme.RADIUS_BADGE,
        font=font,
        height=22
    )


def enable_mousewheel(scrollable_widget: tk.Widget):
    """Enable mouse-wheel vertical scrolling for a CTkScrollableFrame.

    This locates the underlying tkinter.Canvas used by CustomTkinter's
    CTkScrollableFrame and binds platform-appropriate mouse-wheel events
    so that scrolling with the wheel works on Windows and Linux.
    """
    # Find the first Canvas in the widget's descendants
    canvas = None
    widgets = list(scrollable_widget.winfo_children())
    while widgets and canvas is None:
        w = widgets.pop(0)
        if isinstance(w, tk.Canvas):
            canvas = w
            break
        widgets.extend(w.winfo_children())

    if canvas is None:
        return

    def _on_mousewheel(event, _canvas=canvas):
        try:
            # Standardize delta: Windows uses multiples of 120, mac may use small values
            delta = 0
            if hasattr(event, 'delta'):
                delta = int(event.delta / 120)
            elif event.num in (4, 5):
                # Linux button-4 (up) / button-5 (down)
                delta = 1 if event.num == 4 else -1
            if delta:
                _canvas.yview_scroll(-1 * delta, "units")
        except Exception:
            pass

    # Bind the handler to the canvas itself
    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Button-4>", _on_mousewheel)
    canvas.bind("<Button-5>", _on_mousewheel)

    # Also bind to all descendant widgets so wheel events over child widgets
    # are forwarded to the canvas (fixes forms with many child widgets).
    all_widgets = [scrollable_widget]
    all_widgets.extend(scrollable_widget.winfo_children())
    idx = 0
    while idx < len(all_widgets):
        w = all_widgets[idx]
        try:
            w.bind("<MouseWheel>", _on_mousewheel)
            w.bind("<Button-4>", _on_mousewheel)
            w.bind("<Button-5>", _on_mousewheel)
        except Exception:
            pass
        children = w.winfo_children()
        if children:
            all_widgets.extend(children)
        idx += 1
