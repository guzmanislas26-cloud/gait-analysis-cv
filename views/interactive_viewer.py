import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                            QPushButton, QTabWidget, QMessageBox, QFileDialog
                            , QDoubleSpinBox, QSplitter, QSlider)
from PyQt6.QtCore import Qt
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl
from matplotlib.ticker import MultipleLocator
from datetime import datetime
import time
from scipy.signal import find_peaks, savgol_filter
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# Import the CSV manager functions
from utils.csv_manager import get_patient_raw_data

class InteractiveGraphWindow(QWidget):
    def __init__(self, parent=None, patient_id=None, patient_name=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.patient_name = patient_name
        
        # Configuración de la ventana
        self.setWindowTitle(f"Visualización de Datos - {patient_name if patient_name else 'Datos'}")
        self.resize(1000, 700)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel(f"Datos del paciente: {patient_name}" if patient_name else "Datos de la sesión actual")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Botones de control
        control_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Actualizar Datos")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 12px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        control_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Exportar Gráficas")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 12px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.export_btn.clicked.connect(self.export_graphs)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Crear widget de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { background-color: #F0F0F0; }
            QTabBar::tab {
                background-color: #E0E0E0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #F0F0F0;
            }
        """)
        main_layout.addWidget(self.tab_widget)
        
        # Variables para almacenar datos
        self.times = []
        self.left_knee_angles = []
        self.right_knee_angles = []
        self.times_filtered = []
        self.left_knee_angles_filtered = []
        self.right_knee_angles_filtered = []
        
        # Cargar datos forzando actualización
        self.load_data(force_reload=True)
        
        # Crear pestañas con gráficas si hay datos
        self.create_tabs()
    
    def load_patient_data(self):
        """Carga los datos del paciente del archivo CSV"""
        try:
            # Cargar datos del CSV para el paciente específico
            patient_data = get_patient_raw_data(self.patient_id)
            
            if not patient_data:
                print(f"No se encontraron datos para el paciente con ID: {self.patient_id}")
                return False
            
            # Tiempos
            self.times = np.array(list(map(float, patient_data['tiempo'].split(','))))
            
            # Ángulos originales
            self.left_knee_angles = np.array(list(map(float, patient_data['angulo_rodilla_izquierda_original'].split(','))))
            self.right_knee_angles = np.array(list(map(float, patient_data['angulo_rodilla_derecha_original'].split(','))))
            
            # Cargar datos filtrados si existen
            if 'tiempo_suavizado' in patient_data and patient_data['tiempo_suavizado']:
                self.times_filtered = np.array(list(map(float, patient_data['tiempo_suavizado'].split(','))))
            else:
                self.times_filtered = self.times
                
            if 'angulo_rodilla_izquierda' in patient_data and patient_data['angulo_rodilla_izquierda']:
                self.left_knee_angles_filtered = np.array(list(map(float, patient_data['angulo_rodilla_izquierda'].split(','))))
            else:
                self.left_knee_angles_filtered = self.left_knee_angles
                
            if 'angulo_rodilla_derecha' in patient_data and patient_data['angulo_rodilla_derecha']:
                self.right_knee_angles_filtered = np.array(list(map(float, patient_data['angulo_rodilla_derecha'].split(','))))
            else:
                self.right_knee_angles_filtered = self.right_knee_angles
            
            return True
            
        except Exception as e:
            print(f"Error al cargar datos del paciente: {str(e)}")
            return False
    
    def load_data(self, force_reload=False):
        """Carga los datos del paciente desde el CSV con opción de forzar recarga"""
        try:
            if not self.load_patient_data():
                QMessageBox.warning(self, "Error", "No se encontraron datos para el paciente.")
                self.times = []
                self.right_knee_angles = []
                self.left_knee_angles = []
                self.times_filtered = []
                self.right_knee_angles_filtered = []
                self.left_knee_angles_filtered = []
                return
            
            # Asegurar que todas las listas tienen la misma longitud
            min_length = min(len(self.times), len(self.right_knee_angles), len(self.left_knee_angles))
            self.times = self.times[:min_length]
            self.right_knee_angles = self.right_knee_angles[:min_length]
            self.left_knee_angles = self.left_knee_angles[:min_length]
            
            min_length_filtered = min(len(self.times_filtered), len(self.right_knee_angles_filtered), len(self.left_knee_angles_filtered))
            self.times_filtered = self.times_filtered[:min_length_filtered]
            self.right_knee_angles_filtered = self.right_knee_angles_filtered[:min_length_filtered]
            self.left_knee_angles_filtered = self.left_knee_angles_filtered[:min_length_filtered]
            
            # Verificar la integridad de los datos cargados
            self.verify_data_integrity()
            
            print(f"Datos cargados: {min_length} puntos")
            print(f"Rango de tiempo: {min(self.times):.2f}s - {max(self.times):.2f}s")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar los datos: {str(e)}")
            print(f"Error detallado en load_data: {e}")
            # Reset data arrays
            self.times = []
            self.right_knee_angles = []
            self.left_knee_angles = []
            self.times_filtered = []
            self.right_knee_angles_filtered = []
            self.left_knee_angles_filtered = []
    
    def refresh_data(self):
        """Recarga los datos y actualiza las gráficas"""
        # Eliminar todas las pestañas actuales
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        # Recargar datos forzosamente
        self.load_data(force_reload=True)
        
        # Recrear las pestañas con los datos nuevos
        self.create_tabs()
        if len(self.times) > 0:
            QMessageBox.information(self, "Actualización", "Datos actualizados correctamente.")
        else:
            QMessageBox.warning(self, "Sin datos", "No se encontraron datos para mostrar.")
    
    def show_no_data_message(self):
        """Muestra un mensaje cuando no hay datos disponibles"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        message = QLabel("No hay datos disponibles para mostrar.\n\nUtilice el botón 'Actualizar Datos' para intentar cargar los datos más recientes.")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("font-size: 14pt; color: #666;")
        
        layout.addStretch()
        layout.addWidget(message)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Sin Datos")
    
    def create_tabs(self):
        """Crea las pestañas de visualización"""
        if len(self.times) == 0:
            self.show_no_data_message()
            return
        
        # Crear pestañas individuales para cada rodilla
        self.create_left_knee_tab()
        self.create_right_knee_tab()
        self.create_comparison_tab()
        self.create_stats_tab()
        self.create_gait_cycles_tab()
        self.create_video_tab()

    def create_left_knee_tab(self):
        """Crea una pestaña específica para la rodilla izquierda"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        fig = Figure(figsize=(8, 5))
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        
        # Graficar ángulo rodilla izquierda
        ax = fig.add_subplot(111)
        ax.plot(self.times_filtered, self.left_knee_angles_filtered, 'g-', linewidth=2)
        ax.set_title('Ángulo Rodilla Izquierda (Datos Filtrados)', fontsize=14)
        ax.set_xlabel('Tiempo (s)', fontsize=12)
        ax.set_ylabel('Ángulo (°)', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Configuración inicial del intervalo en los ejes
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.yaxis.set_major_locator(MultipleLocator(5.0))
        
        fig.tight_layout()
        
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        # Añadir controles de escala
        scale_control = self.create_scale_control(ax, canvas)
        layout.addLayout(scale_control)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Rodilla Izquierda")

    def create_right_knee_tab(self):
        """Crea una pestaña específica para la rodilla derecha"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        fig = Figure(figsize=(8, 5))
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        
        # Graficar ángulo rodilla derecha
        ax = fig.add_subplot(111)
        ax.plot(self.times_filtered, self.right_knee_angles_filtered, 'r-', linewidth=2)
        ax.set_title('Ángulo Rodilla Derecha (Datos Filtrados)', fontsize=14)
        ax.set_xlabel('Tiempo (s)', fontsize=12)
        ax.set_ylabel('Ángulo (°)', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Configuración inicial del intervalo en los ejes
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.yaxis.set_major_locator(MultipleLocator(5.0))
        
        fig.tight_layout()
        
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        # Añadir controles de escala
        scale_control = self.create_scale_control(ax, canvas)
        layout.addLayout(scale_control)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Rodilla Derecha")

    def create_comparison_tab(self):
        """Crea una pestaña con comparación de ángulos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        
        ax = fig.add_subplot(111)
        ax.plot(self.times_filtered, self.left_knee_angles_filtered, 'g-', linewidth=2, label='Rodilla Izquierda')
        ax.plot(self.times_filtered, self.right_knee_angles_filtered, 'r-', linewidth=2, label='Rodilla Derecha')
        ax.set_title('Comparación de Ángulos', fontsize=16)
        ax.set_xlabel('Tiempo (s)', fontsize=12)
        ax.set_ylabel('Ángulo (°)', fontsize=12)
        ax.legend(fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Configuración inicial del intervalo en los ejes
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.yaxis.set_major_locator(MultipleLocator(5.0))
        
        fig.tight_layout()
        
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        # Añadir controles de escala
        scale_control = self.create_scale_control(ax, canvas)
        layout.addLayout(scale_control)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Comparación")

    def create_stats_tab(self):
        """Crea una pestaña con estadísticas básicas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Calcular estadísticas básicas
        left_mean = np.mean(self.left_knee_angles_filtered)
        left_max = np.max(self.left_knee_angles_filtered)
        left_min = np.min(self.left_knee_angles_filtered)
        left_std = np.std(self.left_knee_angles_filtered)
        
        right_mean = np.mean(self.right_knee_angles_filtered)
        right_max = np.max(self.right_knee_angles_filtered)
        right_min = np.min(self.right_knee_angles_filtered)
        right_std = np.std(self.right_knee_angles_filtered)
        
        # Crear figura para estadísticas
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        
        # Crear histogramas
        ax1 = fig.add_subplot(221)
        ax1.hist(self.left_knee_angles_filtered, bins=15, color='green', alpha=0.7)
        ax1.set_title('Distribución - Izquierda', fontsize=12)
        ax1.set_xlabel('Ángulo (°)', fontsize=10)
        ax1.set_ylabel('Frecuencia', fontsize=10)
        ax1.axvline(left_mean, color='blue', linestyle='dashed', linewidth=1)
        
        ax2 = fig.add_subplot(222)
        ax2.hist(self.right_knee_angles_filtered, bins=15, color='red', alpha=0.7)
        ax2.set_title('Distribución - Derecha', fontsize=12)
        ax2.set_xlabel('Ángulo (°)', fontsize=10)
        ax2.set_ylabel('Frecuencia', fontsize=10)
        ax2.axvline(right_mean, color='blue', linestyle='dashed', linewidth=1)
        
        # Crear boxplot
        ax3 = fig.add_subplot(212)
        bp = ax3.boxplot([self.left_knee_angles_filtered, self.right_knee_angles_filtered], labels=['Izquierda', 'Derecha'])
        ax3.set_title('Comparación Estadística', fontsize=14)
        ax3.set_ylabel('Ángulo (°)', fontsize=12)
        
        # Añadir texto con estadísticas
        estadisticas = (
            f"Rodilla Izquierda:\n"
            f"  • Media: {left_mean:.1f}°\n"
            f"  • Máximo: {left_max:.1f}°\n"
            f"  • Mínimo: {left_min:.1f}°\n"
            f"  • Desv. Est.: {left_std:.1f}°\n\n"
            f"Rodilla Derecha:\n"
            f"  • Media: {right_mean:.1f}°\n"
            f"  • Máximo: {right_max:.1f}°\n"
            f"  • Mínimo: {right_min:.1f}°\n"
            f"  • Desv. Est.: {right_std:.1f}°"
        )
        
        # Añadir texto a la figura
        fig.text(0.75, 0.5, estadisticas, fontsize=10,
                bbox=dict(facecolor='lightyellow', alpha=0.8, boxstyle='round,pad=0.5'))
        
        fig.tight_layout(rect=[0, 0, 0.7, 1])  # Ajustar para dejar espacio al texto
        
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Estadísticas")
    
    def create_gait_cycles_tab(self):
        """Crea una pestaña para visualizar y analizar ciclos de marcha"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Crear figura para análisis de ciclos
        fig = Figure(figsize=(8, 8))
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        
        # Crear dos subplots: uno para cada rodilla
        ax1 = fig.add_subplot(211)  # Rodilla izquierda
        ax2 = fig.add_subplot(212)  # Rodilla derecha
        
        # Detectar ciclos de marcha si tenemos suficientes datos
        if len(self.times_filtered) > 10:
            # Usar directamente los datos ya filtrados con spline
            left_smooth = self.left_knee_angles_filtered  # Ya están filtrados con spline
            right_smooth = self.right_knee_angles_filtered  # Ya están filtrados con spline
            
            # Graficar la señal completa de los ángulos
            ax1.plot(self.times_filtered, left_smooth, 'g-', linewidth=1.5, label='Ángulo rodilla izquierda')
            ax2.plot(self.times_filtered, right_smooth, 'r-', linewidth=1.5, label='Ángulo rodilla derecha')
            
            # Detectar picos (máxima flexión) - cada pico representa aproximadamente medio ciclo
            left_peaks, _ = find_peaks(left_smooth, height=max(left_smooth)*0.6, distance=20)
            right_peaks, _ = find_peaks(right_smooth, height=max(right_smooth)*0.6, distance=20)
            
            # Resaltar fases del ciclo en la rodilla izquierda
            for i in range(len(left_peaks)-1):
                cycle_start = self.times_filtered[left_peaks[i]]
                cycle_end = self.times_filtered[left_peaks[i+1]]
                
                # Calcular punto medio aproximado entre picos (para separar fase de apoyo y balanceo)
                mid_idx = (left_peaks[i] + left_peaks[i+1]) // 2
                cycle_mid = self.times_filtered[mid_idx]
                
                # Resaltar fase de apoyo (60% del ciclo) - color verde claro
                ax1.axvspan(cycle_start, cycle_mid, alpha=0.2, color='green', label='Apoyo' if i == 0 else "")
                
                # Resaltar fase de balanceo (40% del ciclo) - color verde más oscuro
                ax1.axvspan(cycle_mid, cycle_end, alpha=0.3, color='darkgreen', label='Balanceo' if i == 0 else "")
            
            # Resaltar fases del ciclo en la rodilla derecha
            for i in range(len(right_peaks)-1):
                cycle_start = self.times_filtered[right_peaks[i]]
                cycle_end = self.times_filtered[right_peaks[i+1]]
                
                # Calcular punto medio aproximado entre picos
                mid_idx = (right_peaks[i] + right_peaks[i+1]) // 2
                cycle_mid = self.times_filtered[mid_idx]
                
                # Resaltar fase de apoyo y balanceo
                ax2.axvspan(cycle_start, cycle_mid, alpha=0.2, color='red', label='Apoyo' if i == 0 else "")
                ax2.axvspan(cycle_mid, cycle_end, alpha=0.3, color='darkred', label='Balanceo' if i == 0 else "")
            
            # Marcar picos detectados
            ax1.plot(np.array(self.times_filtered)[left_peaks], np.array(left_smooth)[left_peaks], "o", color='blue')
            ax2.plot(np.array(self.times_filtered)[right_peaks], np.array(right_smooth)[right_peaks], "o", color='blue')
            
            # Añadir etiquetas a los ejes
            ax1.set_ylabel('Ángulo (°)', fontsize=10)
            ax2.set_xlabel('Tiempo (s)', fontsize=10)
            ax2.set_ylabel('Ángulo (°)', fontsize=10)
            
            # Añadir información de ciclos detectados
            ax1.set_title(f'Ciclos de Marcha - Rodilla Izquierda (Total: {len(left_peaks) // 2} ciclos)', fontsize=12)
            ax2.set_title(f'Ciclos de Marcha - Rodilla Derecha (Total: {len(right_peaks) // 2} ciclos)', fontsize=12)
            
            # Crear leyendas personalizadas
            angle_left = Line2D([0], [0], color='green', linewidth=1.5, label='Ángulo rodilla izquierda')
            angle_right = Line2D([0], [0], color='red', linewidth=1.5, label='Ángulo rodilla derecha')
            l_stance = mpatches.Patch(color='green', alpha=0.2, label='Fase de Apoyo')
            l_swing = mpatches.Patch(color='darkgreen', alpha=0.3, label='Fase de Balanceo')
            r_stance = mpatches.Patch(color='red', alpha=0.2, label='Fase de Apoyo')
            r_swing = mpatches.Patch(color='darkred', alpha=0.3, label='Fase de Balanceo')
            peak_marker = Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=8, label='Pico de flexión')
            
            # Añadir leyendas a las gráficas
            ax1.legend(handles=[angle_left, l_stance, l_swing, peak_marker], loc='upper right')
            ax2.legend(handles=[angle_right, r_stance, r_swing, peak_marker], loc='upper right')
            
        else:
            # No hay suficientes datos para analizar ciclos
            ax1.text(0.5, 0.5, "Datos insuficientes para detección de ciclos", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax1.transAxes)
            ax2.text(0.5, 0.5, "Datos insuficientes para detección de ciclos", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax2.transAxes)
        
        # Añadir grid para mejor visualización
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax2.grid(True, linestyle='--', alpha=0.6)
        
        fig.tight_layout()
        
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Ciclos de Marcha")

    def export_graphs(self):
        """Exporta las gráficas como archivos PNG"""
        try:
            save_dir = QFileDialog.getExistingDirectory(self, "Seleccionar directorio para guardar gráficas")
            if not save_dir:
                return
            
            # Obtener timestamp para los nombres de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Variable para contar gráficas exportadas
            saved_count = 0
            
            # Exportar cada pestaña
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "Sin Datos":
                    continue
                    
                tab = self.tab_widget.widget(i)
                tab_name = self.tab_widget.tabText(i).lower().replace(" ", "_")
                
                # Buscar los canvas en la pestaña
                for j, canvas in enumerate(tab.findChildren(FigureCanvas)):
                    if hasattr(canvas, 'figure'):
                        # Nombre de archivo personalizado
                        patient_name_safe = self.patient_name.replace(' ', '_') if self.patient_name else "paciente"
                        filename = f"{patient_name_safe}_{tab_name}_{j+1}_{timestamp}.png"
                        filepath = os.path.join(save_dir, filename)
                        
                        # Guardar la figura
                        print(f"Guardando {filepath}")
                        canvas.figure.savefig(filepath, dpi=150, bbox_inches='tight')
                        saved_count += 1
            
            if saved_count > 0:
                QMessageBox.information(self, "Exportación Exitosa", 
                                      f"Se han exportado {saved_count} gráficas a:\n{save_dir}")
            else:
                QMessageBox.warning(self, "Sin gráficas", "No se encontraron gráficas para exportar.")
        
        except Exception as e:
            print(f"Error al exportar gráficas: {e}")
            QMessageBox.critical(self, "Error", f"Error al exportar gráficas: {str(e)}")
    
    def create_scale_control(self, ax, canvas):
        """Crea controles para ajustar la escala de los ejes"""
        control_layout = QGridLayout()
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        # Título
        scale_label = QLabel("Control de Escala:")
        scale_label.setStyleSheet("font-weight: bold;")
        control_layout.addWidget(scale_label, 0, 0, 1, 6)
        
        # Control eje X
        control_layout.addWidget(QLabel("Eje X:"), 1, 0)
        
        # Rango para el eje X
        control_layout.addWidget(QLabel("Min:"), 1, 1)
        x_min = QDoubleSpinBox()
        x_min.setRange(0, 100)
        x_min.setValue(ax.get_xlim()[0])  # Toma el valor actual
        x_min.setSingleStep(0.5)
        control_layout.addWidget(x_min, 1, 2)
        
        control_layout.addWidget(QLabel("Max:"), 1, 3)
        x_max = QDoubleSpinBox()
        x_max.setRange(0, 100)
        x_max.setValue(ax.get_xlim()[1])  # Toma el valor actual
        x_max.setSingleStep(0.5)
        control_layout.addWidget(x_max, 1, 4)
        
        # Intervalo para el eje X
        control_layout.addWidget(QLabel("Intervalo:"), 1, 5)
        x_interval = QDoubleSpinBox()
        x_interval.setRange(0.1, 10.0)
        x_interval.setValue(1.0)  # Intervalo predeterminado
        x_interval.setSingleStep(0.1)
        x_interval.setDecimals(1)
        control_layout.addWidget(x_interval, 1, 6)
        
        # Control eje Y
        control_layout.addWidget(QLabel("Eje Y:"), 2, 0)
        
        # Rango para el eje Y
        control_layout.addWidget(QLabel("Min:"), 2, 1)
        y_min = QDoubleSpinBox()
        y_min.setRange(0, 180)
        y_min.setValue(ax.get_ylim()[0])  # Toma el valor actual
        y_min.setSingleStep(5.0)
        control_layout.addWidget(y_min, 2, 2)
        
        control_layout.addWidget(QLabel("Max:"), 2, 3)
        y_max = QDoubleSpinBox()
        y_max.setRange(0, 180)
        y_max.setValue(ax.get_ylim()[1])  # Toma el valor actual
        y_max.setSingleStep(5.0)
        control_layout.addWidget(y_max, 2, 4)
        
        # Intervalo para el eje Y
        control_layout.addWidget(QLabel("Intervalo:"), 2, 5)
        y_interval = QDoubleSpinBox()
        y_interval.setRange(1, 20)
        y_interval.setValue(5.0)  # Intervalo predeterminado de 5 grados
        y_interval.setSingleStep(1.0)
        y_interval.setDecimals(1)
        control_layout.addWidget(y_interval, 2, 6)
        
        # Botón para aplicar cambios
        apply_button = QPushButton("Aplicar Escala")
        apply_button.setStyleSheet("background-color: #4CAF50; color: white;")
        control_layout.addWidget(apply_button, 3, 0, 1, 7)
        
        # Función para actualizar la escala
        def update_scale():
            # Actualizar rangos de los ejes
            ax.set_xlim(x_min.value(), x_max.value())
            ax.set_ylim(y_min.value(), y_max.value())
            
            # Actualizar los intervalos de las marcas en los ejes
            x_step = x_interval.value()
            y_step = y_interval.value()
            
            # Establecer localizadores para las marcas principales
            ax.xaxis.set_major_locator(MultipleLocator(x_step))
            ax.yaxis.set_major_locator(MultipleLocator(y_step))
            
            canvas.draw()
        
        # Conectar eventos
        apply_button.clicked.connect(update_scale)
        
        return control_layout

    def create_video_tab(self):
        """Crea una pestaña para visualizar el video con gráficas sincronizadas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Buscar el video del paciente
        videos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'videos')
        video_path = os.path.join(videos_dir, f'{self.patient_id}.mp4')
        
        # Si no existe, buscar variantes con timestamp
        if not os.path.exists(video_path) and os.path.exists(videos_dir):
            try:
                potential_videos = [f for f in os.listdir(videos_dir) if f.startswith(f'{self.patient_id}_')]
                if potential_videos:
                    # Usar el video más reciente
                    potential_videos.sort(reverse=True)
                    video_path = os.path.join(videos_dir, potential_videos[0])
            except Exception as e:
                print(f"Error al buscar videos: {e}")
        
        if not os.path.exists(video_path):
            # No se encontró video - mostrar mensaje
            message = QLabel("No se encontró ningún video para este paciente.")
            message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message.setStyleSheet("font-size: 14pt; color: #666;")
            layout.addWidget(message)
            self.tab_widget.addTab(tab, "Video y Gráficas")
            return
        
        # Dividir layout en video (izquierda) y gráficas (derecha)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Crear widget para reproductor de video
        video_widget = QWidget()
        video_layout = QVBoxLayout(video_widget)
        
        # Crear reproductor de medios y widget de video
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(50)  # Volumen al 50%
        
        video_widget_display = QVideoWidget()
        self.media_player.setVideoOutput(video_widget_display)
        
        # Establecer fuente del video
        self.media_player.setSource(QUrl.fromLocalFile(video_path))
        
        video_layout.addWidget(video_widget_display)
        
        # Crear controles de video
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶ Play")
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        # Slider para buscar en el video
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                height: 8px;
                background: #f0f0f0;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 18px;
                margin: -2px 0;
                border-radius: 4px;
            }
        """)
        
        # Etiquetas de tiempo
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setStyleSheet("font-family: monospace; min-width: 40px;")
        self.total_time_label = QLabel("0:00")
        self.total_time_label.setStyleSheet("font-family: monospace; min-width: 40px;")
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.current_time_label)
        controls_layout.addWidget(self.seek_slider)
        controls_layout.addWidget(self.total_time_label)
        
        video_layout.addLayout(controls_layout)
        
        # Crear widget para las gráficas
        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        
        fig = Figure(figsize=(8, 8))  # Ajustado para formato lado a lado
        self.video_canvas = FigureCanvas(fig)
        
        # Crear dos subplots para ángulos de rodilla izquierda y derecha (uno encima del otro)
        ax1 = fig.add_subplot(211)  # Subplot superior
        ax2 = fig.add_subplot(212)  # Subplot inferior
        
        # Store references to these axes as instance variables
        self.left_graph = ax1
        self.right_graph = ax2
        
        # Configurar gráficas
        ax1.set_title('Ángulo Rodilla Izquierda')
        ax1.set_ylabel('Ángulo (°)')
        ax1.grid(True, linestyle='--', alpha=0.6)
        
        ax2.set_title('Ángulo Rodilla Derecha')
        ax2.set_xlabel('Tiempo (s)')
        ax2.set_ylabel('Ángulo (°)')
        ax2.grid(True, linestyle='--', alpha=0.6)
        
        # Usar datos filtrados en lugar de datos originales para el video tab
        use_times = self.times_filtered  # Usar datos filtrados
        use_left_angles = self.left_knee_angles_filtered  # Usar datos filtrados
        use_right_angles = self.right_knee_angles_filtered  # Usar datos filtrados
        
        # Para depuración, imprimir el primer y último punto
        if len(use_times) > 0:
            print(f"Primer punto de tiempo: {use_times[0]:.2f}s")
            print(f"Último punto de tiempo: {use_times[-1]:.2f}s")
            print(f"Duración de los datos: {use_times[-1] - use_times[0]:.2f}s")
            
        # Configurar objetos de línea de datos con los datos filtrados
        left_line, = ax1.plot(use_times, use_left_angles, 'g-')
        right_line, = ax2.plot(use_times, use_right_angles, 'r-')
            
        # Verificar que tengamos datos y sean de longitud correcta
        if len(use_times) > 0:
            # Establecer límites de ejes
            max_time = max(use_times)
            min_angle = min(min(use_left_angles), min(use_right_angles))
            max_angle = max(max(use_left_angles), max(use_right_angles))
            
            # Agregar padding a los ángulos
            min_angle = max(0, min_angle - 10)
            max_angle = min(180, max_angle + 10)
            
            ax1.set_xlim(0, max_time)
            ax1.set_ylim(min_angle, max_angle)
            
            ax2.set_xlim(0, max_time)
            ax2.set_ylim(min_angle, max_angle)
            
            # Agregar marcadores de tiempo (líneas verticales) para mostrar posición actual
            self.left_marker = ax1.axvline(x=[0], color='blue', linestyle='-', linewidth=1)
            self.right_marker = ax2.axvline(x=[0], color='blue', linestyle='-', linewidth=1)
        else:
            # No hay datos disponibles
            ax1.text(0.5, 0.5, "No hay datos disponibles", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax1.transAxes)
            ax2.text(0.5, 0.5, "No hay datos disponibles", 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax2.transAxes)
        
        fig.tight_layout()
        graph_layout.addWidget(self.video_canvas)
        
        # Agregar al splitter
        splitter.addWidget(video_widget)
        splitter.addWidget(graph_widget)
        
        # Establecer tamaños iniciales (50% video, 50% gráficas para formato lado a lado)
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter)
        
        # Conectar señales para el reproductor de video
        def update_graph_position(position):
            if not hasattr(self, 'times_filtered') or len(self.times_filtered) == 0:
                return
                
            # Calcular el porcentaje del video reproducido
            video_progress_percentage = position / self.media_player.duration() if self.media_player.duration() > 0 else 0
            video_time_seconds = position / 1000.0  # Convertir de ms a segundos
            
            # Ya no necesitamos el offset de sincronización, simplemente usar el tiempo directamente
            # porque los datos y el video ya están perfectamente sincronizados
            
            # Calcular tiempo objetivo basado en la proporción del video
            min_time = min(self.times_filtered)
            max_time = max(self.times_filtered)
            time_range = max_time - min_time
            
            # Aplicar la misma proporción a los datos
            target_time = min_time + (time_range * video_progress_percentage)
            
            # Encontrar el punto más cercano en los datos
            closest_idx = min(range(len(self.times_filtered)), 
                              key=lambda i: abs(self.times_filtered[i] - target_time))
            
            # Obtener los valores en ese punto
            data_time = self.times_filtered[closest_idx]
            left_angle = self.left_knee_angles_filtered[closest_idx]
            right_angle = self.right_knee_angles_filtered[closest_idx]
            
            # Actualizar las líneas marcadoras
            if hasattr(self, 'left_marker') and hasattr(self, 'right_marker'):
                self.left_marker.set_xdata([data_time])
                self.right_marker.set_xdata([data_time])
                
                # Actualizar texto con tiempo y ángulos
                if hasattr(self, 'time_text'):
                    self.time_text.set_text(f"Tiempo: {data_time:.2f}s | Izq: {left_angle:.1f}° | Der: {right_angle:.1f}°")
                else:
                    # Crear el texto si no existe
                    ax1 = self.video_canvas.figure.axes[0]
                    self.time_text = ax1.text(0.02, 0.95, 
                                            f"Tiempo: {data_time:.2f}s | Izq: {left_angle:.1f}° | Der: {right_angle:.1f}°", 
                                            transform=ax1.transAxes, 
                                            backgroundcolor='white',
                                            bbox=dict(facecolor='white', alpha=0.7))
                
                # Redibujar el canvas con menos frecuencia para mejor rendimiento
                if not hasattr(self, 'last_redraw_time') or time.time() - self.last_redraw_time > 0.1:
                    self.video_canvas.draw_idle()
                    self.last_redraw_time = time.time()
        
        def play_pause_video():
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                self.play_button.setText("▶ Play")
            else:
                self.media_player.play()
                self.play_button.setText("⏸ Pause")
        
        def stop_video():
            self.media_player.stop()
            self.play_button.setText("▶ Play")
        
        def format_duration(duration_ms):
            """Formatear duración en milisegundos al formato MM:SS"""
            if duration_ms <= 0:
                return "0:00"
            seconds = int(duration_ms / 1000)
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes}:{seconds:02d}"
        
        def handle_media_error(error, error_string):
            if error != QMediaPlayer.Error.NoError:
                QMessageBox.warning(self, "Error de reproducción", 
                                  f"Error al reproducir el video: {error_string}")
        
        # Conectar señales del reproductor de medios
        self.media_player.positionChanged.connect(update_graph_position)
        self.media_player.durationChanged.connect(lambda duration: self.seek_slider.setMaximum(duration))
        self.media_player.durationChanged.connect(lambda duration: self.total_time_label.setText(format_duration(duration)))
        self.media_player.errorOccurred.connect(handle_media_error)
        
        # Conectar botones
        self.play_button.clicked.connect(play_pause_video)
        self.stop_button.clicked.connect(stop_video)
        
        # Conectar slider
        def update_slider_position(position):
            # Actualizar slider sin activar la señal valueChanged
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(position)
            self.seek_slider.blockSignals(False)
        
        def seek_video(position):
            self.media_player.setPosition(position)
        
        self.seek_slider.valueChanged.connect(seek_video)
        self.media_player.positionChanged.connect(update_slider_position)
        
        # Agregar tab
        self.tab_widget.addTab(tab, "Video y Gráficas")

    def verify_data_integrity(self):
        """Verifica la integridad de los datos cargados para depuración"""
        if not hasattr(self, 'times_filtered') or len(self.times_filtered) == 0:
            print("No hay datos filtrados para verificar")
            return
            
        print("\n=== VERIFICACIÓN DE DATOS ===")
        print(f"Total de puntos originales: {len(self.times)}")
        print(f"Total de puntos filtrados: {len(self.times_filtered)}")
        print(f"Tiempo original: {min(self.times):.2f}s a {max(self.times):.2f}s")
        print(f"Tiempo filtrado: {min(self.times_filtered):.2f}s a {max(self.times_filtered):.2f}s")
        
        if len(self.times) > 0 and len(self.times_filtered) > 0:
            print("\nComprobación de alineación temporal:")
            
            # Verificar si los tiempos filtrados cubren los mismos intervalos que los originales
            time_range_orig = max(self.times) - min(self.times)
            time_range_filt = max(self.times_filtered) - min(self.times_filtered)
            percentage_diff = abs(time_range_orig - time_range_filt) / time_range_orig * 100
            
            print(f"Diferencia en rango de tiempo: {percentage_diff:.2f}%")
            print(f"Tiempo inicial original: {min(self.times):.2f}s")
            print(f"Tiempo inicial filtrado: {min(self.times_filtered):.2f}s")
            print("=== FIN DE VERIFICACIÓN ===\n")

    def debug_print_data_info(self):
        """Imprime información de depuración sobre los datos cargados"""
        print("\n===== INFORMACIÓN DE DATOS =====")
        
        if hasattr(self, 'times') and len(self.times) > 0:
            print(f"Datos originales: {len(self.times)} puntos")
            print(f"Tiempo original: [{self.times[0]:.2f} - {self.times[-1]:.2f}] segundos")
            
        if hasattr(self, 'times_filtered') and len(self.times_filtered) > 0:
            print(f"Datos filtrados: {len(self.times_filtered)} puntos")
            print(f"Tiempo filtrado: [{self.times_filtered[0]:.2f} - {self.times_filtered[-1]:.2f}] segundos")
        
        if hasattr(self, 'media_player') and self.media_player.duration() > 0:
            print(f"Duración del video: {self.media_player.duration()/1000:.2f} segundos")
        
        print("===============================\n")