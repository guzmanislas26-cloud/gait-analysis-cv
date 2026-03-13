import csv
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
                            QLineEdit, QFormLayout, QHBoxLayout, QMessageBox, QStackedWidget, 
                            QFrame, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QDialog)
from PyQt6.QtGui import QIcon, QFont, QDoubleValidator, QPalette, QColor, QPixmap
from PyQt6.QtCore import Qt, QSize
from components.ui_components import ModernButton, ModernInput
from utils.csv_manager import (
    load_patient_table_data, 
    update_patient_info, 
    delete_patient, 
    patient_has_angle_data
)


class ListaPacientesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setStyleSheet("background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1a2a3a, stop:1 #2c3e50);")
        
        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Contenedor para la lista
        list_card = QFrame()
        list_card.setStyleSheet("""
            QFrame {
                background-color: rgba(52, 73, 94, 0.7);
                border-radius: 15px;
            }
        """)
        list_card_layout = QVBoxLayout(list_card)
        
        # Título
        titulo = QLabel("Lista de Pacientes")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white; margin: 20px 0; background-color: transparent;")
        list_card_layout.addWidget(titulo)
        
        # Línea divisora
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: rgba(255,255,255,0.2); margin: 0 30px 20px 30px;")
        list_card_layout.addWidget(divider)
        
        # Tabla de pacientes
        self.tabla_pacientes = QTableWidget()
        self.tabla_pacientes.setColumnCount(6)
        self.tabla_pacientes.setHorizontalHeaderLabels(["ID", "Nombre", "Apellido", "Estatura (cm)", 
                                                        "Fecha de Creación", "Última Actualización"])
        
        # Configurar para selección de filas completas solamente
        self.tabla_pacientes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_pacientes.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_pacientes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Desactivar edición directa
        
        self.tabla_pacientes.setStyleSheet("""
            QTableWidget {
                background-color: rgba(44, 62, 80, 0.7);
                color: white;
                gridline-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
            }
            QHeaderView::section {
                background-color: rgba(41, 128, 185, 0.7);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Ajustar el tamaño de las columnas
        header = self.tabla_pacientes.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        list_card_layout.addWidget(self.tabla_pacientes)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(50, 20, 50, 30)
        button_layout.setSpacing(20)
        
        self.btn_volver = QPushButton()
        self.btn_volver.setText("←")  # Solo el carácter de flecha
        self.btn_volver.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 36px;  /* Flecha más grande */
                padding: 0px 2px 4px 2px;  /* Ajustar padding para centrar la flecha */
                border-radius: 8px;
                border: none;
                min-width: 70px;  /* Aumentado de 48px a 70px */
                min-height: 40px;
                max-width: 70px;  /* Aumentado de 48px a 70px */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self.btn_editar = ModernButton("Editar Paciente", "#f39c12", "#d35400")
        self.btn_borrar = ModernButton("Borrar Paciente", "#e74c3c", "#c0392b")
        self.btn_seleccionar = ModernButton("Seleccionar Paciente", "#2ecc71", "#27ae60")
        self.view_graphs_btn = ModernButton("Ver Gráficas", "#1976D2", "#1565C0")
        
        button_layout.addWidget(self.btn_volver)
        button_layout.addWidget(self.btn_editar)
        button_layout.addWidget(self.btn_borrar)
        button_layout.addWidget(self.btn_seleccionar)
        button_layout.addWidget(self.view_graphs_btn)
        
        list_card_layout.addLayout(button_layout)
        
        # Centrar la tarjeta en la pantalla
        main_layout_wrapper = QHBoxLayout()
        main_layout_wrapper.addStretch(1)
        main_layout_wrapper.addWidget(list_card, 10)
        main_layout_wrapper.addStretch(1)
        
        layout.addLayout(main_layout_wrapper)
        
        # Conectar señales
        self.btn_volver.clicked.connect(self.volver)
        self.btn_editar.clicked.connect(self.editar_paciente)
        self.btn_borrar.clicked.connect(self.borrar_paciente)
        self.btn_seleccionar.clicked.connect(self.seleccionar_paciente)
        self.view_graphs_btn.clicked.connect(self.open_graphs_view)
        
        # Cargar datos
        self.cargar_datos()
        
    def volver(self):
        # Volver a la pantalla principal
        self.main_window.stacked_widget.setCurrentIndex(0)
        
    def seleccionar_paciente(self):
        selected_items = self.tabla_pacientes.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección requerida", "Por favor seleccione un paciente de la lista.")
            return

        # Obtener datos del paciente seleccionado
        row = selected_items[0].row()
        nombre = self.tabla_pacientes.item(row, 1).text()
        apellido = self.tabla_pacientes.item(row, 2).text()
        estatura = self.tabla_pacientes.item(row, 3).text()

        # Cambiar a la pantalla del detector
        self.main_window.show_detect_window(nombre, apellido, estatura)
        
    def editar_paciente(self):
        selected_items = self.tabla_pacientes.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección requerida", "Por favor seleccione un paciente para editar.")
            return
        
        # Obtener fila seleccionada
        row = selected_items[0].row()
        
        # Obtener datos del paciente
        patient_id = self.tabla_pacientes.item(row, 0).text()
        nombre = self.tabla_pacientes.item(row, 1).text()
        apellido = self.tabla_pacientes.item(row, 2).text()
        estatura = self.tabla_pacientes.item(row, 3).text()
        
        # Crear diálogo de edición
        dialog = PacienteEditDialog(self, patient_id, nombre, apellido, estatura)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Actualizar los datos en el archivo CSV
            self.actualizar_paciente(dialog.patient_id, dialog.nombre_input.text(), 
                                    dialog.apellido_input.text(), dialog.estatura_input.text())
            
            # Recargar datos en la tabla
            self.cargar_datos()
    
    def borrar_paciente(self):
        """Elimina un paciente del archivo CSV"""
        selected_items = self.tabla_pacientes.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selección requerida", "Por favor seleccione un paciente para eliminar.")
            return
        
        # Obtener datos del paciente
        row = selected_items[0].row()
        patient_id = self.tabla_pacientes.item(row, 0).text()
        nombre = self.tabla_pacientes.item(row, 1).text()
        apellido = self.tabla_pacientes.item(row, 2).text()
        
        # Confirmar eliminación
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación", 
            f"¿Está seguro que desea eliminar al paciente {nombre} {apellido}?\n\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # Proceder con la eliminación
        success, message = delete_patient(patient_id)
        
        if success:
            # Recargar datos en la tabla
            self.cargar_datos()
            QMessageBox.information(self, "Éxito", f"Paciente {nombre} {apellido} eliminado correctamente.")
        else:
            QMessageBox.warning(self, "Error", message)
    
    def actualizar_paciente(self, patient_id, nombre, apellido, estatura):
        """Actualiza los datos de un paciente"""
        try:
            # Usar la función centralizada
            success = update_patient_info(patient_id, nombre, apellido, estatura)
            
            if success:
                QMessageBox.information(self, "Éxito", f"Paciente con ID {patient_id} actualizado correctamente.")
            else:
                QMessageBox.warning(self, "Error", f"No se encontró el paciente con ID {patient_id}.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar el paciente: {e}")
    
    def cargar_datos(self):
        """Carga los datos de pacientes desde el archivo CSV"""
        try:
            # Usar la función centralizada
            patient_rows = load_patient_table_data()
            
            self.tabla_pacientes.setRowCount(0)
            
            for row_num, row in enumerate(patient_rows):
                self.tabla_pacientes.insertRow(row_num)
                for col, value in enumerate(row):
                    self.tabla_pacientes.setItem(row_num, col, QTableWidgetItem(value))
                    
        except Exception as e:
            print(f"Error al cargar datos en la tabla: {e}")

    def open_graphs_view(self):
        """Abre la vista de gráficas interactivas para el paciente seleccionado"""
        selected_items = self.tabla_pacientes.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "Selección requerida", "Por favor, seleccione un paciente primero.")
            return
        
        # Obtener el ID y nombre del paciente seleccionado
        row = selected_items[0].row()
        patient_id = self.tabla_pacientes.item(row, 0).text()
        nombre = self.tabla_pacientes.item(row, 1).text()
        apellido = self.tabla_pacientes.item(row, 2).text()
        patient_name = f"{nombre} {apellido}"
        
        # Verificar que el paciente tenga datos en el CSV
        if not patient_has_angle_data(patient_id):
            QMessageBox.warning(self, "Sin datos", 
                              f"El paciente {patient_name} no tiene datos de ángulos guardados.\n\n"
                              f"Primero debe realizar una medición para este paciente.")
            return
        
        # Importar la ventana de gráficas interactivas
        try:
            from views.interactive_viewer import InteractiveGraphWindow
            
            # Crear y mostrar la ventana de gráficas
            self.graph_window = InteractiveGraphWindow(
                patient_id=patient_id,
                patient_name=patient_name
            )
            self.graph_window.show()
            
        except Exception as e:
            print(f"Error al abrir ventana de gráficas: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al abrir la ventana de gráficas: {str(e)}")
    
    def verificar_datos_paciente(self, patient_id):
        """Verifica si el paciente tiene datos de ángulos guardados en el CSV"""
        return patient_has_angle_data(patient_id)

class PacienteEditDialog(QDialog):
    """Diálogo para editar los datos de un paciente"""
    def __init__(self, parent=None, patient_id="", nombre="", apellido="", estatura=""):
        super().__init__(parent)
        self.patient_id = patient_id
        
        self.setWindowTitle("Editar Paciente")
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        self.setMinimumWidth(400)
        
        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Título
        titulo = QLabel(f"Editando Paciente ID: {patient_id}")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white; margin-bottom: 20px; background-color: transparent;")
        layout.addWidget(titulo)
        
        # Formulario
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Campo: Nombre
        self.nombre_input = ModernInput()
        self.nombre_input.setText(nombre)
        nombre_label = QLabel("Nombre:")
        nombre_label.setStyleSheet("font-size: 14px; background-color: transparent;")
        form_layout.addRow(nombre_label, self.nombre_input)
        
        # Campo: Apellido
        self.apellido_input = ModernInput()
        self.apellido_input.setText(apellido)
        apellido_label = QLabel("Apellido:")
        apellido_label.setStyleSheet("font-size: 14px; background-color: transparent;")
        form_layout.addRow(apellido_label, self.apellido_input)
        
        # Campo: Estatura
        self.estatura_input = ModernInput()
        self.estatura_input.setText(estatura)
        
        # Configurar validador para estatura
        validator = QDoubleValidator(50.0, 250.0, 1)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        locale = validator.locale()
        locale.setNumberOptions(locale.numberOptions() | locale.NumberOption.RejectGroupSeparator)
        validator.setLocale(locale)
        self.estatura_input.setValidator(validator)
        
        estatura_label = QLabel("Estatura (cm):")
        estatura_label.setStyleSheet("font-size: 14px; background-color: transparent;")
        form_layout.addRow(estatura_label, self.estatura_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)
        button_layout.setSpacing(10)
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_guardar.clicked.connect(self.validar_y_aceptar)
        
        button_layout.addWidget(self.btn_cancelar)
        button_layout.addWidget(self.btn_guardar)
        
        layout.addLayout(button_layout)
    
    def validar_y_aceptar(self):
        # Validar que todos los campos estén completos
        if not self.nombre_input.text() or not self.apellido_input.text() or not self.estatura_input.text():
            QMessageBox.warning(self, "Campos incompletos", "Por favor complete todos los campos.")
            return
        
        # Aceptar el diálogo si todo está correcto
        self.accept()