"""
Excel Style Constants

Centralized styling configuration for Excel databook generation.
Easy to tweak colors, fonts, and formatting.
"""

from typing import Dict, Any


class ExcelStyles:
    """Style constants for Excel formatting"""

    # Colors (RGB tuples, 0-255)
    HEADER_BG = (68, 114, 196)  # Blue header fill
    HEADER_TEXT = (255, 255, 255)  # White text on header
    TABLE_BANDING_LIGHT = (217, 225, 242)  # Light blue table banding
    TABLE_BANDING_DARK = (242, 242, 242)  # Light gray alternate (if needed)
    BACKGROUND = (255, 255, 255)  # White background
    ERROR_RED = (255, 0, 0)  # Red for errors/failures
    SUCCESS_GREEN = (0, 176, 80)  # Green for success/pass
    WARNING_YELLOW = (255, 192, 0)  # Yellow for warnings

    # Fonts
    HEADER_FONT = "Calibri"
    HEADER_SIZE = 11
    HEADER_BOLD = True
    BODY_FONT = "Calibri"
    BODY_SIZE = 10
    BODY_BOLD = False

    # Borders
    BORDER_COLOR = (191, 191, 191)  # Light gray borders
    BORDER_STYLE = "thin"

    # Number formats
    CURRENCY_FORMAT = "$#,##0.00"
    PERCENTAGE_FORMAT = "0.00%"
    DATE_FORMAT = "mm/dd/yyyy"
    INTEGER_FORMAT = "#,##0"
    DECIMAL_FORMAT = "#,##0.00"

    @classmethod
    def get_header_format(cls) -> Dict[str, Any]:
        """Get header cell format dictionary"""
        return {
            "bg_color": cls._rgb_to_hex(cls.HEADER_BG),
            "font_color": cls._rgb_to_hex(cls.HEADER_TEXT),
            "font_name": cls.HEADER_FONT,
            "font_size": cls.HEADER_SIZE,
            "bold": cls.HEADER_BOLD,
            "border": 1,
            "border_color": cls._rgb_to_hex(cls.BORDER_COLOR),
            "align": "left",
            "valign": "vcenter",
        }

    @classmethod
    def get_table_banding_format(cls, is_even: bool = False) -> Dict[str, Any]:
        """Get table banding format (alternating row colors)"""
        bg_color = cls.TABLE_BANDING_LIGHT if is_even else cls.BACKGROUND
        return {
            "bg_color": cls._rgb_to_hex(bg_color),
            "font_name": cls.BODY_FONT,
            "font_size": cls.BODY_SIZE,
            "bold": cls.BODY_BOLD,
            "border": 1,
            "border_color": cls._rgb_to_hex(cls.BORDER_COLOR),
            "align": "left",
            "valign": "top",
        }

    @classmethod
    def get_status_format(cls, status: str) -> Dict[str, Any]:
        """Get format for status cells (PASS/FAIL)"""
        base_format = {
            "font_name": cls.BODY_FONT,
            "font_size": cls.BODY_SIZE,
            "bold": True,
            "border": 1,
            "border_color": cls._rgb_to_hex(cls.BORDER_COLOR),
            "align": "center",
            "valign": "vcenter",
        }

        if status.upper() == "PASS":
            base_format["bg_color"] = cls._rgb_to_hex(cls.SUCCESS_GREEN)
            base_format["font_color"] = cls._rgb_to_hex(cls.HEADER_TEXT)
        elif status.upper() == "FAIL":
            base_format["bg_color"] = cls._rgb_to_hex(cls.ERROR_RED)
            base_format["font_color"] = cls._rgb_to_hex(cls.HEADER_TEXT)
        else:
            base_format["bg_color"] = cls._rgb_to_hex(cls.BACKGROUND)

        return base_format

    @classmethod
    def _rgb_to_hex(cls, rgb: tuple) -> str:
        """Convert RGB tuple to hex color string"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    @classmethod
    def get_currency_format_dict(cls) -> Dict[str, Any]:
        """Get currency format dictionary for xlsxwriter"""
        return {"num_format": cls.CURRENCY_FORMAT}

    @classmethod
    def get_date_format_dict(cls) -> Dict[str, Any]:
        """Get date format dictionary for xlsxwriter"""
        return {"num_format": cls.DATE_FORMAT}

    @classmethod
    def get_percentage_format_dict(cls) -> Dict[str, Any]:
        """Get percentage format dictionary for xlsxwriter"""
        return {"num_format": cls.PERCENTAGE_FORMAT}

