import sys
import os
import csv
import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
                            QLineEdit, QFormLayout, QHBoxLayout, QMessageBox, QStackedWidget, 
                            QFrame, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QDialog)
from PyQt6.QtGui import QIcon, QFont, QDoubleValidator, QPalette, QColor, QPixmap
from PyQt6.QtCore import Qt, QSize
from components.ui_components import ModernButton, ModernInput
from utils.csv_manager import create_patient, get_next_patient_id

CSV_FILE = "data.csv"
CSV_HEADERS = ["id", "nombre", "apellido", "estatura", "tiempo", 
               "angulo_rodilla_derecha_original", "angulo_rodilla_izquierda_original", 
               "angulo_rodilla_derecha", "angulo_rodilla_izquierda", "fecha_creacion"]

class FormularioWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setStyleSheet("background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1a2a3a, stop:1 #2c3e50);")
        
        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Contenedor para el formulario sin sombra
        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background-color: rgba(52, 73, 94, 0.7);
                border-radius: 15px;
            }
        """)
        form_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        form_card_layout = QVBoxLayout(form_card)
        
        # Título
        titulo = QLabel("Registro de Paciente")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white; margin: 20px 0; background-color: transparent;")
        form_card_layout.addWidget(titulo)
        
        # Línea divisora
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: rgba(255,255,255,0.2); margin: 0 30px 20px 30px;")
        form_card_layout.addWidget(divider)
        
        # Formulario
        form_container = QWidget()
        form_container.setStyleSheet("background-color: transparent;")
        form_layout = QFormLayout(form_container)
        form_layout.setContentsMargins(50, 20, 50, 20)
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Campo: Nombre
        self.nombre_input = ModernInput("Ingrese nombre del paciente")
        nombre_label = QLabel("Nombre:")
        nombre_label.setStyleSheet("font-size: 16px; color: white; background-color: transparent; font-weight: bold;")
        form_layout.addRow(nombre_label, self.nombre_input)
        
        # Campo: Apellido
        self.apellido_input = ModernInput("Ingrese apellido del paciente")
        apellido_label = QLabel("Apellido:")
        apellido_label.setStyleSheet("font-size: 16px; color: white; background-color: transparent; font-weight: bold;")
        form_layout.addRow(apellido_label, self.apellido_input)
        
        # Campo: Estatura
        self.estatura_input = ModernInput("Ej: 170.5")
        
        # Crear y configurar el validador para números
        validator = QDoubleValidator(50.0, 250.0, 1)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        
        # Asegurarse de usar punto como separador decimal
        locale = validator.locale()
        locale.setNumberOptions(locale.numberOptions() | locale.NumberOption.RejectGroupSeparator)
        validator.setLocale(locale)
        
        self.estatura_input.setValidator(validator)
        
        estatura_label = QLabel("Estatura (cm):")
        estatura_label.setStyleSheet("font-size: 16px; color: white; background-color: transparent; font-weight: bold;")
        form_layout.addRow(estatura_label, self.estatura_input)
        
        form_card_layout.addWidget(form_container)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(50, 20, 50, 30)
        button_layout.setSpacing(20)
        
        self.btn_cancelar = ModernButton("Cancelar", "#e74c3c", "#c0392b")
        self.btn_guardar = ModernButton("Comenzar", "#2ecc71", "#27ae60")
        
        button_layout.addWidget(self.btn_cancelar)
        button_layout.addWidget(self.btn_guardar)
        
        form_card_layout.addLayout(button_layout)
        
        # Centrar el formulario en la pantalla
        main_layout_wrapper = QHBoxLayout()
        main_layout_wrapper.addStretch(1)
        main_layout_wrapper.addWidget(form_card, 4)
        main_layout_wrapper.addStretch(1)
        
        layout.addStretch(1)
        layout.addLayout(main_layout_wrapper)
        layout.addStretch(1)
        
        # Conectar señales
        self.btn_cancelar.clicked.connect(self.cancelar)
        self.btn_guardar.clicked.connect(self.submit_form)
    
    def cancelar(self):
        # Volver a la pantalla principal
        self.main_window.stacked_widget.setCurrentIndex(0)
        
    def submit_form(self):
        """Procesa el formulario cuando se hace clic en el botón Guardar"""
        # Validar campos requeridos
        if not self.validate_form():
            return
        
        # Obtener datos del formulario
        nombre = self.nombre_input.text().strip()
        apellido = self.apellido_input.text().strip()
        estatura = self.estatura_input.text().strip()
        
        # Crear paciente usando la función centralizada
        patient_id = create_patient(nombre, apellido, estatura)
        
        if patient_id:
            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", f"Paciente {nombre} {apellido} guardado correctamente.")
            
            # Limpiar formulario
            self.clear_form()
            
            # Actualizar lista de pacientes si es necesario
            if hasattr(self.main_window, 'lista_pacientes_page'):
                self.main_window.lista_pacientes_page.cargar_datos()
                
            # Redirigir a la pantalla del detector
            self.main_window.show_detect_window(nombre, apellido, estatura)
        else:
            QMessageBox.critical(self, "Error", "No se pudo crear el paciente.")
    
    def validate_form(self):
        """Valida los campos del formulario"""
        if not self.nombre_input.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return False
            
        if not self.apellido_input.text().strip():
            QMessageBox.warning(self, "Error", "El apellido es obligatorio")
            return False
            
        try:
            estatura = float(self.estatura_input.text().strip())
            if estatura <= 0 or estatura > 250:
                raise ValueError("Estatura fuera de rango")
        except ValueError:
            QMessageBox.warning(self, "Error", "La estatura debe ser un número válido entre 1 y 250 cm")
            return False
            
        return True
        
    def clear_form(self):
        """Limpia los campos del formulario"""
        self.nombre_input.clear()
        self.apellido_input.clear()
        self.estatura_input.clear()
    
    def obtener_siguiente_id(self):
        """Determina el siguiente ID secuencial"""
        return str(get_next_patient_id())
    
    def agregar_paciente(self):
        """
        Método que se ejecuta al agregar un paciente.
        """
        nombre = "Juan"
        apellido = "Pérez"
        estatura = 175  # Ejemplo de datos
        self.parent().show_detect_window(nombre, apellido, estatura)