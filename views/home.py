from PyQt6.QtWidgets import (QVBoxLayout, QWidget, QLabel, QHBoxLayout, QMessageBox, QStackedWidget, 
                            QFrame)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from components.ui_components import ModernButton, ModernInput

# Constantes
CSV_FILE = "data.csv"
CSV_HEADERS = ["id", "nombre", "apellido", "estatura", "angulo_rodilla_derecha", "angulo_rodilla_izquierda", "tiempo", "fecha_creacion"]

class HomeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setStyleSheet("background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1a2a3a, stop:1 #2c3e50);")

        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Contenedor para la tarjeta principal sin sombra
        main_card = QFrame()
        main_card.setStyleSheet("""
            QFrame {
                background-color: rgba(52, 73, 94, 0.7);
                border-radius: 20px;
            }
        """)
        main_card_layout = QVBoxLayout(main_card)
        
        # Título grande
        title_label = QLabel("Detector de Ciclo de la Marcha")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 42, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; margin: 20px 0; background-color: transparent;")
        main_card_layout.addWidget(title_label)

        # Línea divisora
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: rgba(255,255,255,0.2); margin: 0 100px 20px 100px;")
        main_card_layout.addWidget(divider)

        # Subtítulo de bienvenida
        subtitle_label = QLabel("¡Bienvenido! Selecciona una opción para continuar.")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont("Segoe UI", 18))
        subtitle_label.setStyleSheet("color: #ecf0f1; margin-bottom: 40px; background-color: transparent;")
        main_card_layout.addWidget(subtitle_label)

        # Layout para los botones
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(20)

        # Botón: Agregar Usuario
        self.add_button = ModernButton("Agregar Usuario", "#3498db", "#2980b9")

        # Botón: Cargar Usuario
        self.load_button = ModernButton("Cargar Usuario", "#2ecc71", "#27ae60")

        # Botón: Salir
        self.exit_button = ModernButton("Salir", "#e74c3c", "#c0392b")

        # Agregar botones al layout
        button_layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.load_button, alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.exit_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_card_layout.addLayout(button_layout)
        main_card_layout.addSpacing(40)

        # Centrar la tarjeta principal en la pantalla
        main_layout_wrapper = QHBoxLayout()
        main_layout_wrapper.addStretch(1)
        main_layout_wrapper.addWidget(main_card, 3)
        main_layout_wrapper.addStretch(1)
        
        layout.addStretch(1)
        layout.addLayout(main_layout_wrapper, 4)
        layout.addStretch(1)
        
        # Conectar señales
        self.add_button.clicked.connect(self.mostrar_formulario)
        self.load_button.clicked.connect(self.mostrar_lista_pacientes)
        self.exit_button.clicked.connect(self.main_window.close)
    
    def mostrar_formulario(self):
        # Cambiar a la página del formulario
        self.main_window.stacked_widget.setCurrentIndex(1)
        
    def mostrar_lista_pacientes(self):
        # Cambiar a la página de lista de pacientes
        self.main_window.lista_pacientes_page.cargar_datos()  # Refrescar datos
        self.main_window.stacked_widget.setCurrentIndex(2)