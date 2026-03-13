from views.pantalla_detector import DetectWindow
from views.form import FormularioWidget
from views.patient_list import ListaPacientesWidget
from views.home import HomeWidget

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QStackedWidget, QMessageBox)
from PyQt6.QtGui import QIcon

# Import CSV manager functions

from utils.csv_manager import (initialize_csv_file)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detector de Ciclo de la Marcha")
        self.setWindowIcon(QIcon("icon.png"))

        # Verificar si existe el archivo CSV, si no, crearlo con los encabezados
        initialize_csv_file()

        # Widget central con stacked widget para cambiar entre "pantallas"
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked Widget para cambiar entre pantallas
        self.stacked_widget = QStackedWidget()
        
        # Crear páginas
        self.home_page = HomeWidget(self)
        self.formulario_page = FormularioWidget(self)
        self.lista_pacientes_page = ListaPacientesWidget(self)
        self.detect_window = DetectWindow(self)

        # Agregar páginas al stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.formulario_page)
        self.stacked_widget.addWidget(self.lista_pacientes_page)
        self.stacked_widget.addWidget(self.detect_window)
        
        main_layout.addWidget(self.stacked_widget)

    def show_detect_window(self, nombre, apellido, estatura):
        self.detect_window.set_patient_data(nombre, apellido, estatura)
        
        # Add this line to reinitialize the detector components
        self.detect_window.reinitialize_detector()
        
        index = self.stacked_widget.indexOf(self.detect_window)
        print(f"Índice de la pantalla del detector: {index}")
        self.stacked_widget.setCurrentWidget(self.detect_window)

    def return_to_menu(self):
        """
        Vuelve a la pantalla principal desde cualquier otra vista
        """
        # Cambiar a la página de inicio (home)
        self.stacked_widget.setCurrentWidget(self.home_page)
        print("Volviendo al menú principal")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplicar estilos globales
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
