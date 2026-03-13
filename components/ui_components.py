from PyQt6.QtWidgets import QPushButton, QLineEdit
from PyQt6.QtGui import QDoubleValidator

class ModernButton(QPushButton):
    """Modern button with improved visual effects"""
    def __init__(self, text, color="#3498db", hover_color="#2980b9"):
        super().__init__(text)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 15px;
                min-width: 200px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {color};
            }}
        """)

class ModernInput(QLineEdit):
    """Modern text field with improved visual effects"""
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(44, 62, 80, 0.7);
                color: white;
                border: 1px solid #3498db;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 2px solid #2ecc71;
                background-color: rgba(44, 62, 80, 0.9);
            }
            QLineEdit::placeholder {
                color: rgba(189, 195, 199, 0.7);
                font-style: italic;
            }
        """)

def create_number_validator(min_val, max_val, decimals=1):
    """Creates a configured validator for numeric inputs"""
    validator = QDoubleValidator(min_val, max_val, decimals)
    validator.setNotation(QDoubleValidator.Notation.StandardNotation)
    locale = validator.locale()
    locale.setNumberOptions(locale.numberOptions() | locale.NumberOption.RejectGroupSeparator)
    validator.setLocale(locale)
    return validator