import statistics
import cv2
import mediapipe as mp
import math
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from scipy.interpolate import make_interp_spline
import os

# Importaciones de PyQt6
from PyQt6.QtWidgets import (
    QLabel, QHBoxLayout, QWidget, 
    QPushButton, QVBoxLayout, QSplitter, QCheckBox,
    QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt

# Importaciones de módulos propios
from utils.csv_manager import find_patient_id, update_patient_record
from views.interactive_viewer import InteractiveGraphWindow

class PoseDetector:
    def __init__(self, label, checkbox1, checkbox2):
        self.checkbox1 = checkbox1
        self.checkbox2 = checkbox2
        self.label = label
        
        # Inicializa estos atributos como None
        self.mp_pose = None
        self.pose = None
        self.cap = None
        
        # Añadir atributos para almacenar los últimos ángulos
        self.last_left_angle = 0
        self.last_right_angle = 0
        
        # Height calibration attributes
        self.last_height_pixels = 0
        self.height_scale_factor = 1.0
        self.calibration_mode = False

        # Store landmarks for sagittal plane detection
        self.last_landmarks = None

    def initialize(self):
        # Inicializa MediaPipe y la cámara solo cuando sea necesario
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.cap = cv2.VideoCapture(0)

    def process_frame(self, frame):
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        
        # Default distance value
        self.current_distance_meters = 0
        is_calibrated = hasattr(self, 'height_scale_factor') and self.height_scale_factor > 0 and not self.calibration_mode

        subject_detected = False

        if results.pose_landmarks:
            subject_detected = True
            self.last_landmarks = results.pose_landmarks.landmark  # Store landmarks for sagittal plane detection
            landmarks = results.pose_landmarks.landmark

            # Calculate height in pixels if in calibration mode
            if self.calibration_mode:
                # Use nose for top of head and midpoint between hips for bottom
                nose = (int(landmarks[self.mp_pose.PoseLandmark.NOSE].x * w),
                       int(landmarks[self.mp_pose.PoseLandmark.NOSE].y * h))
                
                left_hip = (int(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].x * w),
                          int(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y * h))
                
                right_hip = (int(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].x * w),
                           int(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].y * h))
                
                mid_hip = ((left_hip[0] + right_hip[0]) // 2, 
                          (left_hip[1] + right_hip[1]) // 2)
                
                # Calculate height in pixels from top of head to mid-hip
                self.last_height_pixels = self.calculate_distance(nose, mid_hip)
                
                # Draw indicators for calibration mode
                cv2.line(frame, nose, mid_hip, (255, 255, 0), 2)
                cv2.putText(frame, f"Altura: {int(self.last_height_pixels)} px", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.putText(frame, "MODO CALIBRACION", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.putText(frame, "Mantengase quieto", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
               
                # Draw rectangle around the detected body
                x_min = w
                x_max = 0
                y_min = h
                y_max = 0
                
                # Find bounding box of visible landmarks
                for landmark in landmarks:
                    if landmark.visibility > 0.5:
                        x, y = int(landmark.x * w), int(landmark.y * h)
                        x_min = min(x_min, x)
                        x_max = max(x_max, x)
                        y_min = min(y_min, y)
                        y_max = max(y_max, y)
                
                # Draw bounding box if we have valid coordinates
                if x_min < x_max and y_min < y_max:
                    cv2.rectangle(frame, (x_min-10, y_min-10), (x_max+10, y_max+10), 
                                 (0, 255, 0), 2)

            # Get key landmarks for pose analysis
            right_hip = (int(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].x * w),
                        int(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y * h))
            right_knee = (int(landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].x * w),
                        int(landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].y * h))
            right_ankle = (int(landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE].x * w),
                        int(landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE].y * h))
            
            left_hip = (int(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].x * w),
                        int(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].y * h))
            
            left_knee = (int(landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].x * w),
                        int(landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].y * h))
            
            left_ankle = (int(landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE].x * w),
                        int(landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE].y * h))
                        
            right_color_line1 = (0, 0, 255)  # Rojo para líneas de la pierna derecha
            right_color_line2 = (0, 0, 255)
            right_color_point = (0, 0, 255)

            left_color_line1 = (0, 255, 0)  # Verde para líneas de la pierna izquierda
            left_color_line2 = (0, 255, 0)
            left_color_point = (0, 255, 0)

            cv2.line(frame, right_hip, right_knee, right_color_line1, 3)
            cv2.line(frame, right_knee, right_ankle, right_color_line2, 3)
            for point in [right_hip, right_knee, right_ankle]:
                cv2.circle(frame, point, 8, right_color_point, -1)

            cv2.line(frame, left_hip, left_knee, left_color_line1, 3)
            cv2.line(frame, left_knee, left_ankle, left_color_line2, 3)
            for point in [left_hip, left_knee, left_ankle]:
                cv2.circle(frame, point, 8, left_color_point, -1)

            left_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
            right_angle = self.calculate_angle(right_hip, right_knee, right_ankle)

            # Almacenar los últimos ángulos
            self.last_left_angle = left_angle
            self.last_right_angle = right_angle
            
            if self.checkbox1.isChecked():
                self.draw_angle(frame, right_hip, right_knee, right_ankle, right_angle)
                self.draw_angle(frame, left_hip, left_knee, left_ankle, left_angle)

            if self.checkbox2.isChecked():
                cv2.putText(frame, f"Right: {int(right_angle)}", (right_knee[0] - 50, right_knee[1] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(frame, f"Left: {int(left_angle)}", (left_knee[0] - 50, left_knee[1] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            # Calculate distance if calibrated
            if is_calibrated and not self.calibration_mode:
                # Get current height in pixels
                nose = (int(landmarks[self.mp_pose.PoseLandmark.NOSE].x * w),
                       int(landmarks[self.mp_pose.PoseLandmark.NOSE].y * h))
                
                left_hip = (int(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].x * w),
                          int(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y * h))
                
                right_hip = (int(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].x * w),
                           int(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].y * h))
                
                mid_hip = ((left_hip[0] + right_hip[0]) // 2, 
                          (left_hip[1] + right_hip[1]) // 2)
                
                # Calculate current height in pixels
                current_height_pixels = self.calculate_distance(nose, mid_hip)
                
                # Calculate distance based on the change in apparent size
                if current_height_pixels > 0 and self.last_height_pixels > 0:
                    # The ratio of calibration height to current height
                    height_ratio = self.last_height_pixels / current_height_pixels
                    
                    # Get reference height in cm
                    patient_height_cm = float(self.height_scale_factor * self.last_height_pixels)
                    
                    # Estimate distance using simple pinhole camera model: d = (f * h) / p
                    # where d is distance, f is focal length, h is real height, p is pixel height
                    # We don't know exact focal length, but can estimate proportionally
                    self.current_distance_meters = (height_ratio * patient_height_cm) / 100  # Convert cm to meters

        return frame, is_calibrated, self.current_distance_meters, subject_detected
    
    def calculate_distance(self, point1, point2):
        """
        Calculate the Euclidean distance between two points
        """
        x1, y1 = point1
        x2, y2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def calculate_angle(self, hip, knee, ankle):
        """
        Calcula el ángulo de la rodilla utilizando los puntos de la cadera, rodilla y tobillo.
        Un ángulo de 0 grados representa una rodilla flexionada, y 180 grados una pierna extendida.
        :param hip: Coordenadas de la cadera (x, y)
        :param knee: Coordenadas de la rodilla (x, y)
        :param ankle: Coordenadas del tobillo (x, y)
        :return: Ángulo de la rodilla en grados
        """
        # Vector de la cadera a la rodilla
        vector_hip_to_knee = [hip[0] - knee[0], hip[1] - knee[1]]
        
        # Vector de la rodilla al tobillo
        vector_knee_to_ankle = [ankle[0] - knee[0], ankle[1] - knee[1]]
        
        # Producto punto de los vectores
        dot_product = (vector_hip_to_knee[0] * vector_knee_to_ankle[0] +
                       vector_hip_to_knee[1] * vector_knee_to_ankle[1])
        
        # Magnitudes de los vectores
        magnitude_hip_to_knee = math.sqrt(vector_hip_to_knee[0]**2 + vector_hip_to_knee[1]**2)
        magnitude_knee_to_ankle = math.sqrt(vector_knee_to_ankle[0]**2 + vector_knee_to_ankle[1]**2)
        
        # Evitar división por cero
        if magnitude_hip_to_knee == 0 or magnitude_knee_to_ankle == 0:
            return 0

        # Calcular el coseno del ángulo
        cos_angle = dot_product / (magnitude_hip_to_knee * magnitude_knee_to_ankle)
        
        # Asegurar que el valor esté en el rango [-1, 1] para evitar errores numéricos
        cos_angle = max(-1.0, min(1.0, cos_angle))
        
        # Calcular el ángulo en radianes y convertir a grados
        angle_radians = math.acos(cos_angle)
        angle_degrees = math.degrees(angle_radians)
        
        # Invertir el ángulo para que 0 grados sea flexionado y 180 grados sea extendido
        inverted_angle = 180 - angle_degrees
        
        return inverted_angle

    def draw_angle(self, frame, hip, knee, ankle, angle):
        radius = 40
        color = (255, 0, 0)
        thickness = 2

        v1 = np.array([hip[0] - knee[0], hip[1] - knee[1]])
        v2 = np.array([ankle[0] - knee[0], ankle[1] - knee[1]])

        angle1 = math.degrees(math.atan2(v1[1], v1[0]))
        angle2 = math.degrees(math.atan2(v2[1], v2[0]))

        start_angle = min(angle1, angle2)
        end_angle = max(angle1, angle2)

        cv2.ellipse(frame, knee, (radius, radius), 0, start_angle, end_angle, color, thickness)

        cv2.ellipse(frame, knee, (radius, radius), 0, start_angle, end_angle, color, thickness)

    def get_last_angles(self):
        return self.last_left_angle, self.last_right_angle
    
    def get_distance(self):
        """
        Returns the current estimated distance in meters
        """
        if hasattr(self, 'current_distance_meters'):
            return self.current_distance_meters
        return 0
    
    def stop(self):
        if self.cap:
            self.cap.release()

    def is_in_sagittal_plane(self):
        """
        Detects if the person is correctly positioned in the sagittal plane (side view)
        
        Returns:
            bool: True if in sagittal plane, False otherwise
        """
        if not hasattr(self, 'pose') or self.pose is None:
            return False
            
        # Need results from the last frame
        if not hasattr(self, 'last_landmarks') or not self.last_landmarks:
            return False
        
        landmarks = self.last_landmarks
        
        # Check if we have the necessary landmarks with good visibility
        required_landmarks = [
            self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            self.mp_pose.PoseLandmark.LEFT_HIP,
            self.mp_pose.PoseLandmark.RIGHT_HIP
        ]
        
        for landmark in required_landmarks:
            if landmark.value >= len(landmarks) or landmarks[landmark.value].visibility < 0.5:
                return False
        
        # Get coordinates
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # Calculate shoulder and hip alignment in x-axis (should be close in sagittal view)
        shoulder_diff_x = abs(left_shoulder.x - right_shoulder.x)
        hip_diff_x = abs(left_hip.x - right_hip.x)
        
        # Threshold for alignment (adjust based on testing)
        # Lower values = stricter alignment requirement
        alignment_threshold = 0.05  # 5% of image width
        
        is_sagittal = (shoulder_diff_x < alignment_threshold and hip_diff_x < alignment_threshold)
        return is_sagittal

class GraphAngle(QWidget):
    def __init__(self, title="Gráfica de Ángulo", leg_color='blue', parent=None):
        super().__init__(parent)
        
        self.leg_color = leg_color
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.figure.tight_layout(pad=3.0)
        
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        self.ax.set_title(title, pad=20)
        self.ax.set_xlabel("Tiempo (s)")
        self.ax.set_ylabel("Ángulo (°)")
        
        # Set fixed y-axis limits from -30 to 180 degrees
        self.ax.set_ylim([-30, 100])
        
        self.ax.tick_params(axis='both', which='major', labelsize=8)
        
        self.figure.subplots_adjust(
            left=0.15,   
            right=0.95,  
            top=0.85,    
            bottom=0.15  
        )
        
        # Parámetros para filtrado
        self.window_size = 5  # Tamaño de la ventana para el filtro
        self.poly_order = 2   # Orden del polinomio para Savitzky-Golay

    def update_graph(self, x_data, y_data, raw_y_data=None, title="Gráfica de Ángulo"):
        self.ax.clear()
        
        if len(x_data) > 0 and len(y_data) > 0:
            # Primero graficar los puntos de datos originales (semi-transparentes)
            if raw_y_data is not None and len(raw_y_data) == len(x_data):
                self.ax.scatter(x_data, raw_y_data, color=self.leg_color, alpha=0.3, s=15, zorder=1)
            
            # Luego graficar la línea filtrada encima
            self.ax.plot(x_data, y_data, color=self.leg_color, linewidth=2, zorder=2)
        
        self.ax.set_title(title, pad=20)
        self.ax.set_xlabel("Tiempo (s)")
        self.ax.set_ylabel("Ángulo (°)")
        
        # Maintain fixed y-axis limits after clearing - adjusted for the new angle range
        self.ax.set_ylim([-30, 100])
        
        # Añadir cuadrícula para facilitar lectura
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        self.canvas.draw()

class TopInfoBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            background-color: #3c4f6b; 
            border-radius: 10px; 
            padding: 3px;
        """)
        
        # Layout horizontal para los ángulos y la información del paciente
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)  # Espaciado fijo entre elementos
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Alineación vertical centrada
        self.setLayout(layout)
        
        # Back arrow button with larger arrow character
        self.back_button = QPushButton()
        self.back_button.setText("←")  # Just the arrow character
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 36px;  /* Much larger arrow */
                padding: 0px 2px 4px 2px;  /* Adjust padding to center the arrow */
                border-radius: 8px;
                border: none;
                min-width: 48px;
                min-height: 40px;
                max-width: 48px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # Container para la etiqueta de detección (para mantener tamaño fijo)
        detection_container = QFrame()
        detection_container.setFixedWidth(250)  # Ancho fijo para el contenedor
        detection_container_layout = QHBoxLayout(detection_container)
        detection_container_layout.setContentsMargins(0, 0, 0, 0)
        detection_container_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Centrado vertical
        
        # Etiqueta para advertencia de detección
        self.detection_label = QLabel("⚠️ NO SE DETECTA SUJETO ⚠️")
        self.detection_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
            background-color: #e74c3c;
            padding: 5px 12px;
            border-radius: 5px;
            border: 2px solid #c0392b;
        """)
        self.detection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centrado horizontal y vertical
        detection_container_layout.addWidget(self.detection_label)
        
        # Contenedor para ángulo izquierdo
        left_angle_container = QFrame()
        left_angle_container.setFixedWidth(150)
        left_angle_layout = QHBoxLayout(left_angle_container)
        left_angle_layout.setContentsMargins(0, 0, 0, 0)
        left_angle_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Centrado vertical
        
        # Etiqueta para ángulo izquierdo
        self.left_angle_label = QLabel("Ángulo Izq: -°")
        self.left_angle_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        self.left_angle_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Centrado vertical, alineado a la izquierda
        left_angle_layout.addWidget(self.left_angle_label)
        
        # Contenedor para ángulo derecho
        right_angle_container = QFrame()
        right_angle_container.setFixedWidth(150)
        right_angle_layout = QHBoxLayout(right_angle_container)
        right_angle_layout.setContentsMargins(0, 0, 0, 0)
        right_angle_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Centrado vertical
        
        # Etiqueta para ángulo derecho
        self.right_angle_label = QLabel("Ángulo Der: -°")
        self.right_angle_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        self.right_angle_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Centrado vertical, alineado a la izquierda
        right_angle_layout.addWidget(self.right_angle_label)
        
        # Contenedor para distancia
        distance_container = QFrame()
        distance_container.setFixedWidth(180)
        distance_layout = QHBoxLayout(distance_container)
        distance_layout.setContentsMargins(0, 0, 0, 0)
        distance_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Centrado vertical
        
        # Etiqueta para distancia
        self.distance_label = QLabel("Distancia: -")
        self.distance_label.setStyleSheet("""
            color: #2ecc71;
            font-size: 16px;
            font-weight: bold;
        """)
        self.distance_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Centrado vertical, alineado a la izquierda
        distance_layout.addWidget(self.distance_label)
        
        # Contenedor para nombre del paciente
        patient_name_container = QFrame()
        patient_name_container.setFixedWidth(300)  # Más ancho para nombres largos
        patient_name_layout = QHBoxLayout(patient_name_container)
        patient_name_layout.setContentsMargins(0, 0, 0, 0)
        patient_name_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Centrado vertical
        
        # Etiqueta para información del paciente
        self.patient_name_label = QLabel("Nombre: -")
        self.patient_name_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        self.patient_name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Centrado vertical, alineado a la izquierda
        patient_name_layout.addWidget(self.patient_name_label)
        
        # Contenedor para estatura
        patient_height_container = QFrame()
        patient_height_container.setFixedWidth(150)
        patient_height_layout = QHBoxLayout(patient_height_container)
        patient_height_layout.setContentsMargins(0, 0, 0, 0)
        patient_height_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Centrado vertical
        
        # Etiqueta para estatura
        self.patient_height_label = QLabel("Estatura: -")
        self.patient_height_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)
        self.patient_height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Centrado vertical, alineado a la izquierda
        patient_height_layout.addWidget(self.patient_height_label)
        
        # Sagittal plane warning label
        self.sagittal_warning_label = QLabel("Posición: Sin detectar")
        self.sagittal_warning_label.setStyleSheet("""
            color: gray;
            font-size: 14px;
            font-weight: bold;
            background-color: #555555;
            padding: 5px 12px;
            border-radius: 5px;
            border: 2px solid #444444;
        """)
        self.sagittal_warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sagittal_warning_label.setFixedWidth(180)
        
        # Create a container for the sagittal warning (similar to other containers)
        sagittal_container = QFrame()
        sagittal_container.setStyleSheet("background-color: transparent; border: none;")
        sagittal_layout = QHBoxLayout(sagittal_container)
        sagittal_layout.setContentsMargins(5, 0, 5, 0)
        sagittal_layout.addWidget(self.sagittal_warning_label)
        
        # Agregar todos los elementos al layout principal
        layout.addWidget(self.back_button)
        layout.addSpacing(10)
        layout.addWidget(detection_container)
        layout.addWidget(left_angle_container)
        layout.addWidget(right_angle_container)
        layout.addWidget(distance_container)
        layout.addWidget(sagittal_container)  # Add this line
        layout.addStretch(1)  # Espaciador flexible
        layout.addWidget(patient_name_container)
        layout.addWidget(patient_height_container)

    def update_detection_status(self, subject_detected):
        """
        Actualiza el estado de detección de sujeto en la barra superior.
        """
        if subject_detected:
            self.detection_label.setText("✓ SUJETO DETECTADO ✓")
            self.detection_label.setStyleSheet("""
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: #27ae60;
                padding: 5px 12px;
                border-radius: 5px;
                border: 2px solid #219653;
            """)
        else:
            self.detection_label.setText("⚠️ NO SE DETECTA SUJETO ⚠️")
            self.detection_label.setStyleSheet("""
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: #e74c3c;
                padding: 5px 12px;
                border-radius: 5px;
                border: 2px solid #c0392b;
            """)

    def update_angles(self, left_angle, right_angle):
        """
        Actualiza los ángulos en la barra superior.
        """
        self.left_angle_label.setText(f"Ángulo Izq: {int(left_angle)}°")
        self.right_angle_label.setText(f"Ángulo Der: {int(right_angle)}°")
        
    def update_distance(self, distance_meters, is_calibrated=False):
        """
        Updates the distance display in the top info bar
        """
        if is_calibrated:
            self.distance_label.setText(f"Distancia: {distance_meters:.2f} m")
            self.distance_label.setVisible(True)
        else:
            self.distance_label.setVisible(False)

    def update_patient_info(self, nombre, apellido, estatura):
        """
        Actualiza la información del paciente en la barra superior.
        """
        self.patient_name_label.setText(f"Nombre: {nombre} {apellido}")
        self.patient_height_label.setText(f"Estatura: {estatura} cm")

    def update_sagittal_warning(self, is_sagittal):
        """
        Updates the sagittal plane warning label
        
        Args:
            is_sagittal (bool): True if user is correctly in sagittal plane, False otherwise
        """
        if is_sagittal:
            self.sagittal_warning_label.setText("Posición: ✓ De perfil")
            self.sagittal_warning_label.setStyleSheet("""
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: #27ae60;
                padding: 5px 12px;
                border-radius: 5px;
                border: 2px solid #219653;
            """)
        else:
            self.sagittal_warning_label.setText("❌ No de perfil")
            self.sagittal_warning_label.setStyleSheet("""
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: #e74c3c;
                padding: 5px 12px;
                border-radius: 5px;
                border: 2px solid #c0392b;
            """)

class DetectWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Otras inicializaciones existentes...
        
        # Inicializar listas para almacenar datos de tracking
        self.full_time_stamps = []
        self.full_left_knee_angles = []
        self.full_right_knee_angles = []
        self.tracking = False
        
        # Añadir una variable para almacenar el tiempo acumulado
        self.accumulated_time = 0.0
        self.tracking_start_time = None
        
        # Añadir variable para controlar si hay datos sin guardar
        self.unsaved_data = False

        # Agrega esta variable al inicio de la clase
        self.aplicar_filtro = False  # Desactivar filtro

        # Variables para grabación de video
        self.recording_video = False
        self.video_writer = None
        self.video_frames = []  # Para almacenar temporalmente frames si no queremos escribir directamente
        self.video_fps = 30  # FPS para el video guardado

        # Usar exactamente 33.33ms para conseguir 30 FPS exactos
        self.fps = 30
        self.frame_interval = int(1000 / self.fps)  # 33ms

        # Agregar un atributo para almacenar el último frame procesado
        self.latest_processed_frame = None  # Para almacenar el último frame procesado

        self.setWindowTitle("Análisis de la marcha en la rodilla")
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        self.showMaximized()
        
        self.main_window = parent  # Store reference to parent window

        # Layout principal
        main_layout = QVBoxLayout()
        
        # Barra superior con información del paciente y ángulos
        self.top_info_bar = TopInfoBar()
        main_layout.addWidget(self.top_info_bar)
        
        # Connect the back button in the top info bar to return_to_menu method
        self.top_info_bar.back_button.clicked.connect(self.return_to_menu)

        # Layout para video y controles
        content_layout = QHBoxLayout()

        # Video container as a QFrame
        video_container = QFrame()
        video_container.setFrameShape(QFrame.Shape.StyledPanel)
        video_container.setStyleSheet("background-color: #1e2a38;")
        video_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(5, 5, 5, 5)

        # Crear un contenedor para el video que se expandirá para llenar el espacio disponible
        video_display_container = QWidget()
        video_display_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        video_display_layout = QVBoxLayout(video_display_container)
        video_display_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setScaledContents(False)
        
        video_display_layout.addWidget(self.video_label)
        video_layout.addWidget(video_display_container, 1)

        right_layout = QVBoxLayout()

        # Asegúrate de que no se aplique ningún estilo con bordes al contenedor principal
        right_container = QWidget()
        right_container.setLayout(right_layout)
        right_container.setStyleSheet("background-color: transparent; border: none;")  # Sin bordes ni fondo

        timer_layout = QHBoxLayout()
        self.time_label = QLabel("0.0 s")
        self.time_label.setStyleSheet("color: white; font-size: 20px;")
        
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        
        self.button_start = QPushButton("Start")
        self.button_stop = QPushButton("Stop")
        self.button_reset = QPushButton("Reset")
        self.button_save = QPushButton("Guardar")  # New save button
        
        # Estilo modificado con menor altura para los botones
        button_style = """
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-size: 14px; 
                padding: 5px;
                border-radius: 4px;
                min-height: 30px;
                max-height: 30px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        
        # Aplicar el estilo a todos los botones, con el botón Stop en rojo
        self.button_start.setStyleSheet(button_style)
        self.button_stop.setStyleSheet(button_style.replace("#4CAF50", "#F44336").replace("#45a049", "#D32F2F"))
        self.button_reset.setStyleSheet(button_style.replace("#4CAF50", "#FFA500").replace("#45a049", "#FF8C00"))
        self.button_save.setStyleSheet(button_style.replace("#4CAF50", "#2196F3").replace("#45a049", "#1976D2"))
        
        # Actualizar el estilo del botón interactivo para que coincida con los otros
        self.interactive_btn = QPushButton("Ver Gráficas")
        self.interactive_btn.setStyleSheet(button_style.replace("#4CAF50", "#1976D2").replace("#45a049", "#1565C0"))
        self.interactive_btn.clicked.connect(self.open_interactive_view)
        self.interactive_btn.setVisible(False)  # Inicialmente oculto
        
        # También aplicamos el mismo estilo al botón de calibración
        self.calibrate_button = QPushButton("Calibrar")
        self.calibrate_button.setStyleSheet(button_style.replace("#4CAF50", "#9C27B0").replace("#45a049", "#7B1FA2"))
        self.calibrate_button.clicked.connect(self.calibrate_height)

        button_layout.addWidget(self.button_start)
        button_layout.addWidget(self.button_stop)
        button_layout.addWidget(self.button_reset)
        button_layout.addWidget(self.button_save)  # Add save button to layout
        button_layout.addWidget(self.interactive_btn)  # Add interactive button to layout
        
        timer_layout.addWidget(self.time_label)
        timer_layout.addWidget(button_widget)
        
        right_layout.addLayout(timer_layout)

        checkbox_layout = QHBoxLayout()
        self.checkbox1 = QCheckBox("Ver ángulos")
        self.checkbox1.setChecked(True)

        self.checkbox2 = QCheckBox("Ver texto")
        self.checkbox2.setChecked(True)

        checkbox_style = """
            QCheckBox {
                color: white;
                font-size: 14px;
            }
        """
        self.checkbox1.setStyleSheet(checkbox_style)
        self.checkbox2.setStyleSheet(checkbox_style)

        checkbox_layout.addWidget(self.checkbox1)
        checkbox_layout.addWidget(self.checkbox2)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.calibrate_button)  # Add calibrate button

        right_layout.addLayout(checkbox_layout)

        self.graph_left = GraphAngle("Marcha de la Rodilla Izquierda", leg_color='green')
        self.graph_right = GraphAngle("Marcha de la Rodilla Derecha", leg_color='red')
        
        graphs_splitter = QSplitter(Qt.Orientation.Vertical)
        graphs_splitter.addWidget(self.graph_left)
        graphs_splitter.addWidget(self.graph_right)
        graphs_splitter.setSizes([1, 1])
        
        right_layout.addWidget(graphs_splitter)

        content_layout.addWidget(video_container, 7)
        content_layout.addWidget(right_container, 3)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # Inicializar detector de pose y timer de video
        self.pose_detector = PoseDetector(self.video_label, self.checkbox1, self.checkbox2)
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video)

        # Variable para controlar si la cámara está activa
        self.camera_active = False

        # Modify button visibility and connections
        self.button_stop.setVisible(False)
        self.button_reset.setVisible(False)
        self.button_save.setVisible(False)

        self.button_start.clicked.connect(self.start_tracking)
        self.button_stop.clicked.connect(self.stop_tracking)
        self.button_reset.clicked.connect(self.reset_tracking)
        self.button_save.clicked.connect(self.save_tracking_data)  # New save method

        # Añadir una variable para almacenar el tiempo acumulado
        self.accumulated_time = 0.0
        self.tracking_start_time = None

        # Temporizador para retrasar la actualización de las gráficas
        self.graph_update_timer = QTimer()
        self.graph_update_timer.setInterval(400)  # 400 ms = 0.4 segundos
        self.graph_update_timer.timeout.connect(self.update_graphs_with_delay)

        # Listas temporales para acumular datos
        self.temp_time_stamps = []
        self.temp_left_knee_angles = []  # Add this line
        self.temp_right_knee_angles = []  # Add this line

    def hideEvent(self, event):
        # Stop the camera and release resources when the window is hidden
        if self.camera_active:
            self.video_timer.stop()
            if hasattr(self, 'tracking_timer') and self.tracking_timer.isActive():
                self.tracking_timer.stop()
            if hasattr(self, 'graph_update_timer') and self.graph_update_timer.isActive():
                self.graph_update_timer.stop()
            if hasattr(self.pose_detector, 'cap') and self.pose_detector.cap is not None:
                self.pose_detector.stop()
            self.camera_active = False
            print("Camera deactivated due to window hiding")
        
        # Always call the parent class method
        super().hideEvent(event)

    def update_video(self):
        # Capturar frame de video
        ret, frame = self.pose_detector.cap.read()
        if not ret:
            return

        # Procesar frame - invertir horizontalmente para vista de espejo
        frame = cv2.flip(frame, 1)
        processed_frame, is_calibrated, distance, subject_detected = self.pose_detector.process_frame(frame)
        
        # Convertir a RGB para mostrar en QT
        processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        
        # Actualizar el estado de detección
        self.top_info_bar.update_detection_status(subject_detected)
        
        # Update distance in top info bar
        self.top_info_bar.update_distance(distance, is_calibrated)
        
        # Add sagittal plane checking
        is_sagittal = False
        if subject_detected:
            is_sagittal = self.pose_detector.is_in_sagittal_plane()
        self.top_info_bar.update_sagittal_warning(is_sagittal)
        
        # Obtener el tamaño disponible para mostrar el video
        label_size = self.video_label.size()
        
        # Convertir a QImage
        h, w, ch = processed_frame_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(processed_frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Calcular el tamaño escalado manteniendo la relación de aspecto
        if h > 0 and w > 0:
            pixmap = QPixmap.fromImage(qimg)
            
            # Escalar el pixmap para ajustarse al label manteniendo la relación de aspecto
            scaled_pixmap = pixmap.scaled(
                label_size.width(), 
                label_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
        
        # Actualizar ángulos en la barra superior
        left_angle, right_angle = self.pose_detector.get_last_angles()
        self.top_info_bar.update_angles(left_angle, right_angle)

        # Si estamos en modo tracking, guardar frame y datos al mismo tiempo
        if self.tracking:
            self.unsaved_data = True
            
            # Capturar tiempo transcurrido
            elapsed_time = self.accumulated_time + (time.time() - self.tracking_start_time)
            
            # Almacenar datos originales
            self.full_left_knee_angles.append(left_angle)
            self.full_right_knee_angles.append(right_angle)
            self.full_time_stamps.append(elapsed_time)
            
            # Almacenar datos temporales para gráficas
            self.temp_left_knee_angles.append(left_angle)
            self.temp_right_knee_angles.append(right_angle)
            self.temp_time_stamps.append(elapsed_time)

            # Guardar el frame de video si estamos grabando
            if self.recording_video:
                self.video_frames.append(processed_frame.copy())
                
            # Actualizar tiempo con formato minutos:segundos
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            self.time_label.setText(f"{minutes}:{seconds:.1f}")

    def start_tracking(self):
        self.tracking = True
        self.button_start.setVisible(False)
        self.button_stop.setVisible(True)
        self.button_reset.setVisible(False)
        self.button_save.setVisible(False)
        self.interactive_btn.setVisible(False)  # Ocultar botón durante el tracking
        
        # Iniciar la grabación de video
        self.start_video_recording()
        
        # Guardar el tiempo de inicio para cálculos relativos
        self.tracking_start_time = time.time()
        
        # Ya no necesitamos un timer separado para tracking, todo se maneja en update_video
        if hasattr(self, 'tracking_timer') and self.tracking_timer.isActive():
            self.tracking_timer.stop()

    def start_video_recording(self):
        """
        Inicia la grabación de video utilizando la cámara actual
        """
        # Verificar que no estamos ya grabando
        if self.recording_video:
            return
        
        self.recording_video = True
        self.video_frames = []  # Limpiar frames anteriores
        print("Grabación de video iniciada")

    def update_graphs_with_delay(self):
        if not self.full_time_stamps:
            return  # No hay datos para graficar

        # Obtener el tiempo actual (último tiempo registrado)
        current_time = self.full_time_stamps[-1]
        time_window = 5.0  # Ventana de 5 segundos

        # Filtrar los datos para incluir solo los últimos 5 segundos
        filtered_indices = [
            i for i, t in enumerate(self.full_time_stamps) if current_time - t <= time_window
        ]

        # Filtrar los datos usando los índices seleccionados
        filtered_time_stamps = [self.full_time_stamps[i] for i in filtered_indices]
        filtered_left_angles = [self.full_left_knee_angles[i] for i in filtered_indices]
        filtered_right_angles = [self.full_right_knee_angles[i] for i in filtered_indices]

        # Actualizar las gráficas con los datos filtrados
        self.graph_left.update_graph(
            filtered_time_stamps,
            filtered_left_angles,
            raw_y_data=filtered_left_angles,  # Same data as filtered_left_angles
            title="Ángulo Rodilla Izquierda"
        )
        self.graph_right.update_graph(
            filtered_time_stamps,
            filtered_right_angles,
            raw_y_data=filtered_right_angles,  # Mostrar también los datos originales
            title="Ángulo Rodilla Derecha"
        )

    def stop_tracking(self):
        if hasattr(self, 'tracking_timer'):
            self.tracking_timer.stop() 
        self.tracking = False
        
        # Actualizar el tiempo acumulado
        if self.tracking_start_time is not None:
            self.accumulated_time += (time.time() - self.tracking_start_time)
        
        self.button_start.setVisible(True)
        self.button_stop.setVisible(False)
        self.button_reset.setVisible(True)
        self.button_save.setVisible(True)
        
        # Solo mostrar botón de visualización si hay datos para mostrar
        if len(self.full_time_stamps) > 0:
            self.interactive_btn.setVisible(True)

    def save_tracking_data(self):
        """
        Save the tracking data to the CSV file and save recorded video
        """
        if not self.full_time_stamps:
            QMessageBox.warning(self, "Error", "No hay datos para guardar.")
            return False

        try:
            # Get patient info
            patient_info = self.get_current_patient_info()
            
            # Primero guardar el CSV
            # Código existente para guardar datos en CSV...
            
            # Datos a guardar en el CSV (código existente)
            # Aplicar spline smoothing con 300 puntos si tenemos suficientes datos
            if len(self.full_time_stamps) >= 4:  # Need at least 4 points for cubic spline
                # Convertir a arrays de numpy para asegurar compatibilidad
                times_array = np.array(self.full_time_stamps)
                left_angles_array = np.array(self.full_left_knee_angles)
                right_angles_array = np.array(self.full_right_knee_angles)
                
                # Crear 300 puntos de tiempo uniformemente espaciados
                smoothed_times = np.linspace(min(times_array), max(times_array), 300)
                
                # Aplicar interpolación con make_interp_spline (B-spline cúbico)
                left_spline = make_interp_spline(times_array, left_angles_array, k=3)
                right_spline = make_interp_spline(times_array, right_angles_array, k=3)
                
                # Evaluar los splines en los nuevos puntos de tiempo
                smoothed_left_angles = left_spline(smoothed_times).tolist()
                smoothed_right_angles = right_spline(smoothed_times).tolist()
                
                # Datos a guardar en el CSV
                data = {
                    'id': patient_info["id"],
                    'nombre': patient_info["nombre"],
                    'apellido': patient_info["apellido"],
                    'estatura': patient_info["estatura"],
                    'tiempo': self.full_time_stamps,
                    'angulo_rodilla_derecha_original': self.full_right_knee_angles,
                    'angulo_rodilla_izquierda_original': self.full_left_knee_angles,
                    'angulo_rodilla_derecha': smoothed_right_angles,
                    'angulo_rodilla_izquierda': smoothed_left_angles,
                    'tiempo_suavizado': smoothed_times.tolist()
                }
            else:
                # Si no hay suficientes puntos para suavizado, usar los datos originales
                data = {
                    'id': patient_info["id"],
                    'nombre': patient_info["nombre"],
                    'apellido': patient_info["apellido"],
                    'estatura': patient_info["estatura"],
                    'tiempo': self.full_time_stamps,
                    'angulo_rodilla_derecha_original': self.full_right_knee_angles,
                    'angulo_rodilla_izquierda_original': self.full_left_knee_angles,
                    'angulo_rodilla_derecha': self.full_right_knee_angles,
                    'angulo_rodilla_izquierda': self.full_left_knee_angles,
                    'tiempo_suavizado': self.full_time_stamps
                }
            
            csv_success = update_patient_record(
                patient_info,
                data['angulo_rodilla_izquierda'],
                data['angulo_rodilla_derecha'],
                data['tiempo'],
                data['angulo_rodilla_izquierda_original'],
                data['angulo_rodilla_derecha_original'],
                data['tiempo_suavizado']
            )
            
            # Ahora guardar el video si hay frames grabados
            video_success = False
            if self.recording_video and len(self.video_frames) > 0:
                video_success = self.save_recorded_video(patient_info["id"])
            
            if csv_success and video_success:
                self.unsaved_data = False
                QMessageBox.information(self, "Datos guardados", 
                                     "Los datos de seguimiento y el video se han guardado correctamente.")
                return True
            elif csv_success:
                QMessageBox.warning(self, "Error al guardar video", 
                                  "Los datos de seguimiento se han guardado correctamente, pero ocurrió un error al guardar el video.")
                return True
            else:
                QMessageBox.warning(self, "Error al guardar", 
                                  "Ocurrió un error al guardar los datos de seguimiento.")
                return False
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar los datos: {str(e)}")
            print(f"Error al guardar datos: {str(e)}")
            return False

    def save_recorded_video(self, patient_id):
        """
        Guarda el video grabado con las detecciones de MediaPose visibles
        
        Args:
            patient_id: ID del paciente para nombrar el archivo
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            if not self.video_frames:
                print("No hay frames para guardar")
                return False
                
            # Crear directorio base para videos si no existe
            videos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'videos')
            if not os.path.exists(videos_dir):
                os.makedirs(videos_dir)
            
            # Usar solo el ID como nombre de archivo y permitir sobrescribir
            video_filename = os.path.join(videos_dir, f'{patient_id}.mp4')
            
            # Obtener dimensiones del primer frame para el VideoWriter
            height, width, _ = self.video_frames[0].shape
            
            # Calcular los FPS reales basados en el número de frames y el tiempo de grabación
            if self.accumulated_time > 0:
                actual_fps = len(self.video_frames) / self.accumulated_time
            else:
                # Si hay un problema con el tiempo, usar 30 fps como respaldo
                actual_fps = 30.0
            
            print(f"Guardando video con FPS calculado: {actual_fps:.2f} ({len(self.video_frames)} frames / {self.accumulated_time:.2f}s)")
            
            # Crear objeto VideoWriter con códec mp4v y el FPS calculado
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Códec MP4
            video_writer = cv2.VideoWriter(video_filename, fourcc, actual_fps, (width, height))
            
            # Escribir todos los frames al video
            for frame in self.video_frames:
                video_writer.write(frame)
                    
            # Liberar recursos
            video_writer.release()
            
            # Detener la grabación y limpiar frames
            self.recording_video = False
            self.video_frames = []
            
            print(f"Video guardado en: {video_filename} con {actual_fps:.2f} FPS")
            return True
                
        except Exception as e:
            print(f"Error al guardar el video: {str(e)}")
            return False

    def reset_tracking(self):
        """Reset tracking data but keep camera and timers running"""
        self.reset_detector_state(full_reset=False)

    def reinitialize_detector(self):
        """Fully reinitialize detector including camera and timers"""
        self.reset_detector_state(full_reset=True)

    def reset_detector_state(self, full_reset=False):
        """
        Unified method to reset detector state with varying levels of reset
        
        Args:
            full_reset (bool): If True, performs a complete reset including camera and timers
                              If False, only resets tracking data
        """
        # Stop any active timers (only for full reset)
        if full_reset:
            if hasattr(self, 'tracking_timer') and self.tracking_timer.isActive():
                self.tracking_timer.stop()
                
            if hasattr(self, 'graph_update_timer') and self.graph_update_timer.isActive():
                self.graph_update_timer.stop()
            
            # Reset camera connection
            if hasattr(self.pose_detector, 'cap') and self.pose_detector.cap is not None:
                self.pose_detector.stop()
                self.pose_detector.cap = None
            
            # Reinitialize pose detector and camera
            self.pose_detector.initialize()

        # Reset tracking variables
        self.tracking = False
        self.unsaved_data = False
        self.accumulated_time = 0.0
        self.tracking_start_time = None
        
        # Reset video recording state and clear frames
        self.recording_video = False
        self.video_frames = []  # Clear any recorded frames
        
        # Clear all data arrays
        self.full_time_stamps = []
        self.full_left_knee_angles = []
        self.full_right_knee_angles = []
        self.temp_time_stamps = []
        self.temp_left_knee_angles = []
        self.temp_right_knee_angles = []
        
        # Reset time display
        self.time_label.setText("0:0.0")
        
        # Update UI elements
        self.button_start.setVisible(True)
        self.button_stop.setVisible(False)
        self.button_reset.setVisible(False)
        self.button_save.setVisible(False)
        self.interactive_btn.setVisible(False)
        
        # Reset graphs
        self.graph_left.update_graph([], [], title="Ángulo Rodilla Izquierda")
        self.graph_right.update_graph([], [], title="Ángulo Rodilla Derecha")
        
        # Restart timers (only for full reset)
        if full_reset:
            # Restart video timer if needed
            if not self.video_timer.isActive():
                # Usar el intervalo preciso para 30 FPS
                self.video_timer.start(self.frame_interval)
                self.camera_active = True
            
            # Start graph update timer (puede mantener su frecuencia más baja para rendimiento)
            self.graph_update_timer.start(400)
            
            print(f"Detector reinitializado completamente a {self.fps} FPS")
        else:
            print("Datos de tracking y grabación de video reinicializados")

    def closeEvent(self, event):
        if hasattr(self, 'tracking_timer'):
            self.tracking_timer.stop()

        self.tracking = False
        self.start_time = None

    def return_to_menu(self):
        # If we're tracking, ask for confirmation to avoid accidental data loss
        if hasattr(self, 'tracking') and self.tracking:
            reply = QMessageBox.question(
                self, 
                "Confirmar regreso", 
                "¿Estás seguro de regresar al menú principal?\nSe perderán los datos no guardados.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            # Stop tracking if we're going back
            if hasattr(self, 'tracking_timer'):
                self.tracking_timer.stop()
            self.tracking = False
        
        # Deactivate camera before returning to menu
        if self.camera_active:
            self.video_timer.stop()
            if hasattr(self.pose_detector, 'cap') and self.pose_detector.cap is not None:
                self.pose_detector.stop()
            self.camera_active = False
            print("Camera deactivated when returning to menu")
        
        # Return to the main menu (home page is at index 0)
        self.main_window.stacked_widget.setCurrentIndex(0)

    def calibrate_height(self):
        """ 
        Calibrates the system using the patient's height to establish a scale factor.
        """ 
        # Get patient height
        patient_height_text = self.top_info_bar.patient_height_label.text()
        try:
            height_cm = float(patient_height_text.split(": ")[1].split(" ")[0])
        except (IndexError, ValueError):
            QMessageBox.warning(self, "Error de calibración", 
                              "No se pudo obtener la estatura del paciente. Verifique los datos.")
            return
        
        # First time clicking calibrate button - show instructions
        if not hasattr(self.pose_detector, 'calibration_mode') or not self.pose_detector.calibration_mode:
            # Calculate recommended distance based on height
            recommended_distance = height_cm / 100 * 2.5  # About 2.5x body height for good full-body view
            instructions = (
                f"Instrucciones para calibración:\n\n"
                f"1. Colóquese a aproximadamente {recommended_distance:.1f} metros de la cámara\n"
                f"2. Párese de frente a la cámara con los brazos a los lados\n"
                f"3. Asegúrese de que todo su cuerpo sea visible en la imagen\n"
                f"4. Manténgase quieto y en posición erguida\n\n"
                f"Presione 'OK' para iniciar la calibración y espere 5 segundos."
            )
            QMessageBox.information(self, "Calibración", instructions)
            
            # Set calibration mode
            self.pose_detector.calibration_mode = True

            # Start calibration timer - will collect multiple samples over 5 seconds
            self.calibration_samples = []
            self.calibration_timer = QTimer()
            self.calibration_timer.timeout.connect(self.collect_calibration_sample)
            self.calibration_timer.start(500)  # Sample every 500ms
            return  
        
        # Already in calibration mode - finalize calibration
        else:       
            # Calculate median of samples to get a stable height measurement
            if hasattr(self, 'calibration_samples') and self.calibration_samples:
                # Use median of collected samples for stability
                height_pixels = statistics.median(self.calibration_samples)
                
                # Calculate scale factor (cm per pixel)
                if height_pixels > 0:
                    scale_factor = height_cm / height_pixels
                    
                    # Store scale factor
                    self.pose_detector.height_scale_factor = scale_factor
                    self.pose_detector.last_height_pixels = height_pixels
                    
                    # Turn off calibration mode
                    self.pose_detector.calibration_mode = False
                    
                    QMessageBox.information(self, "Calibración exitosa", 
                                          f"Sistema calibrado correctamente.\n\n"
                                          f"• Factor de escala: {scale_factor:.4f} cm/pixel\n"
                                          f"• Distancia óptima: {(height_cm/100 * 2.5):.2f} metros\n\n"
                                          f"Ahora puede ver la distancia en tiempo real en\n"
                                          f"la barra superior.")
                    
                    # Show distance immediately after calibration
                    left_angle, right_angle = self.pose_detector.get_last_angles()
                    distance = self.pose_detector.get_distance()
                    self.top_info_bar.update_distance(distance, True)
                    
                    # Change button text to indicate recalibration is possible
                    self.calibrate_button.setText("Recalibrar")
            else:
                QMessageBox.warning(self, "Error de calibración", 
                                  "No se pudieron recopilar suficientes datos. Intente nuevamente.")
                self.pose_detector.calibration_mode = False

    def collect_calibration_sample(self):
        """Collect height samples during calibration"""
        if hasattr(self.pose_detector, 'last_height_pixels') and self.pose_detector.last_height_pixels > 0:
            self.calibration_samples.append(self.pose_detector.last_height_pixels)
        # After 5 seconds (10 samples at 500ms), auto-finalize calibration
        if len(self.calibration_samples) >= 10:
            self.calibration_timer.stop()
            self.calibrate_height()  # Call again to finalize

    def get_current_patient_info(self):
        """
        Obtiene la información del paciente actual de la barra de información
        """
        patient_name_text = self.top_info_bar.patient_name_label.text()
        patient_height_text = self.top_info_bar.patient_height_label.text()
        
        # Extraer valores
        nombre_completo = patient_name_text.replace("Nombre: ", "")
        if " " in nombre_completo:
            nombre, apellido = nombre_completo.split(" ", 1)
        else:
            nombre, apellido = nombre_completo, ""
        
        estatura = patient_height_text.replace("Estatura: ", "").replace(" cm", "")
        
        # Usar directamente la función importada
        patient_id = find_patient_id(nombre, apellido) or "unknown"
        
        return {
            "id": patient_id,
            "nombre": nombre,
            "apellido": apellido,
            "estatura": estatura
        }

    def open_interactive_view(self):
        """Abre la ventana de visualización interactiva con los datos actuales"""
        # Verificar si hay datos sin guardar
        if self.unsaved_data:
            reply = QMessageBox.warning(
                self, 
                "Datos sin guardar", 
                "Hay datos nuevos que no se han guardado en el CSV. Las gráficas mostrarán los datos anteriores.\n\n¿Desea guardar los datos antes de continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Guardar datos primero
                self.save_tracking_data()
            elif reply == QMessageBox.StandardButton.Cancel:
                # Cancelar la acción
                return
        
        # Obtener info del paciente actual
        patient_info = self.get_current_patient_info()
        

        
        # Crear y mostrar la ventana de visualización
        self.interactive_window = InteractiveGraphWindow(
            patient_id=patient_info["id"],
            patient_name=f"{patient_info['nombre']} {patient_info['apellido']}"
        )
        self.interactive_window.show()

    def set_patient_data(self, nombre, apellido, estatura):
        """
        Updates the patient data in the detector window UI.
        
        Args:
            nombre (str): Patient's first name
            apellido (str): Patient's last name
            estatura (str or float): Patient's height in cm
        """
        # Update the top info bar with patient info
        self.top_info_bar.update_patient_info(nombre, apellido, estatura)
        
        # Start the camera if it's not already active
        if not self.camera_active:
            self.pose_detector.initialize()
            self.video_timer.start(self.frame_interval)  # Exactamente 30 FPS
            self.camera_active = True
        
        # Reset any existing calibration when switching patients
        if hasattr(self.pose_detector, 'calibration_mode'):
            self.pose_detector.calibration_mode = False
        
        # Update the calibrate button text
        self.calibrate_button.setText("Calibrar")
        
        print(f"Datos del paciente actualizados: {nombre} {apellido}, {estatura}cm")

    def reinitialize_detector(self):
        """Reinitializes all components needed for real-time graphs"""
        self.reset_detector_state(full_reset=True)

    def reset_detector_state(self, full_reset=False):
        """
        Unified method to reset detector state with varying levels of reset
        
        Args:
            full_reset (bool): If True, performs a complete reset including camera and timers
                              If False, only resets tracking data
        """
        # Stop any active timers (only for full reset)
        if full_reset:
            if hasattr(self, 'tracking_timer') and self.tracking_timer.isActive():
                self.tracking_timer.stop()
                
            if hasattr(self, 'graph_update_timer') and self.graph_update_timer.isActive():
                self.graph_update_timer.stop()
            
            # Reset camera connection
            if hasattr(self.pose_detector, 'cap') and self.pose_detector.cap is not None:
                self.pose_detector.stop()
                self.pose_detector.cap = None
            
            # Reinitialize pose detector and camera
            self.pose_detector.initialize()

        # Reset tracking variables
        self.tracking = False
        self.unsaved_data = False
        self.accumulated_time = 0.0
        self.tracking_start_time = None
        
        # Reset video recording state and clear frames
        self.recording_video = False
        self.video_frames = []  # Clear any recorded frames
        
        # Clear all data arrays
        self.full_time_stamps = []
        self.full_left_knee_angles = []
        self.full_right_knee_angles = []
        self.temp_time_stamps = []
        self.temp_left_knee_angles = []
        self.temp_right_knee_angles = []
        
        # Reset time display
        self.time_label.setText("0:0.0")
        
        # Update UI elements
        self.button_start.setVisible(True)
        self.button_stop.setVisible(False)
        self.button_reset.setVisible(False)
        self.button_save.setVisible(False)
        self.interactive_btn.setVisible(False)
        
        # Reset graphs
        self.graph_left.update_graph([], [], title="Ángulo Rodilla Izquierda")
        self.graph_right.update_graph([], [], title="Ángulo Rodilla Derecha")
        
        # Restart timers (only for full reset)
        if full_reset:
            # Restart video timer if needed
            if not self.video_timer.isActive():
                self.video_timer.start(self.frame_interval)  # Exactamente 30 FPS
                self.camera_active = True
            
            # Start graph update timer
            self.graph_update_timer.start(400)
            
            print("Detector reinitializado completamente")
        else:
            print("Datos de tracking y grabación de video reinicializados")
