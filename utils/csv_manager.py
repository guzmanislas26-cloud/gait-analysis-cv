import csv
import os
from datetime import datetime

# Path to the main CSV data file
CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.csv')

def find_patient_id(nombre, apellido):
    """
    Busca el ID de un paciente en el CSV basado en su nombre y apellido
    """
    try:
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['nombre'].lower() == nombre.lower() and row['apellido'].lower() == apellido.lower():
                    return int(row['id'])
        # Si no se encuentra, retornar None
        return None
    except Exception as e:
        print(f"Error al buscar paciente en CSV: {e}")
        return None

def update_patient_record(patient_info, left_knee_filtered, right_knee_filtered, 
                          timestamps, left_knee_original, right_knee_original, 
                          timestamps_filtered=None):
    """
    Actualiza el registro del paciente en el CSV con los datos de ángulos filtrados y originales.
    """
    try:
        # Si el paciente no tiene ID, buscarlo o crear uno nuevo
        if patient_info["id"] is None:
            new_id = get_next_patient_id()
            patient_info["id"] = new_id
        
        # Convertir listas a cadenas CSV con redondeo a 2 decimales
        timestamps_str = ",".join([f"{t:.2f}" for t in timestamps])
        left_knee_original_str = ",".join([f"{a:.2f}" for a in left_knee_original])
        right_knee_original_str = ",".join([f"{a:.2f}" for a in right_knee_original])
        left_knee_filtered_str = ",".join([f"{a:.2f}" for a in left_knee_filtered])
        right_knee_filtered_str = ",".join([f"{a:.2f}" for a in right_knee_filtered])
        
        # Usar tiempos originales si no se proporcionan tiempos filtrados
        if timestamps_filtered is None:
            timestamps_filtered = timestamps
        
        timestamps_filtered_str = ",".join([f"{t:.2f}" for t in timestamps_filtered])
        
        # Obtener fecha actual para el registro
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Leer el archivo CSV actual
        rows = []
        headers = []
        file_exists = os.path.isfile(CSV_FILE_PATH)
        
        if file_exists:
            with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = next(reader)  # Obtener encabezados
                for row in reader:
                    rows.append(row)
        else:
            # Si el archivo no existe, crear encabezados incluyendo tiempo_suavizado y fecha_actualizado
            headers = ['id', 'nombre', 'apellido', 'estatura', 'tiempo', 
                      'angulo_rodilla_derecha_original', 'angulo_rodilla_izquierda_original',
                      'angulo_rodilla_derecha', 'angulo_rodilla_izquierda', 'tiempo_suavizado',
                      'fecha_creacion', 'fecha_actualizado']
        
        # Añadir 'tiempo_suavizado' a los encabezados si no existe
        if 'tiempo_suavizado' not in headers:
            headers.insert(headers.index('fecha_creacion'), 'tiempo_suavizado')
            
        # Añadir 'fecha_actualizado' a los encabezados si no existe
        if 'fecha_actualizado' not in headers:
            headers.append('fecha_actualizado')
        
        # Comprobar si el paciente ya existe
        patient_exists = False
        fecha_creacion = current_date  # Default value for new patients
        
        for i, row in enumerate(rows):
            if row[0] == str(patient_info["id"]):
                # Verificar longitud de la fila para asegurar compatibilidad con la nueva estructura
                while len(row) < len(headers):
                    if 'fecha_actualizado' in headers and headers[-1] == 'fecha_actualizado':
                        row.append("")  # Añadir fecha_actualizado al final
                    else:
                        row.insert(-1, "")  # Insertar columna vacía en otra posición
                
                # Obtener el índice de tiempo_suavizado y fecha_creacion
                tiempo_suavizado_idx = headers.index('tiempo_suavizado')
                fecha_creacion_idx = headers.index('fecha_creacion')
                fecha_actualizado_idx = headers.index('fecha_actualizado')
                
                # Preservar fecha de creación original
                fecha_creacion = row[fecha_creacion_idx] if row[fecha_creacion_idx] else current_date
                
                # Actualizar registro existente
                row[0] = str(patient_info["id"]) 
                row[1] = patient_info["nombre"]
                row[2] = patient_info["apellido"]
                row[3] = str(patient_info["estatura"])
                row[4] = timestamps_str                 # Tiempos originales
                row[5] = right_knee_original_str        # Ángulos originales rodilla derecha
                row[6] = left_knee_original_str         # Ángulos originales rodilla izquierda
                row[7] = right_knee_filtered_str        # Ángulos filtrados rodilla derecha
                row[8] = left_knee_filtered_str         # Ángulos filtrados rodilla izquierda
                row[tiempo_suavizado_idx] = timestamps_filtered_str  # Tiempos suavizados
                row[fecha_creacion_idx] = fecha_creacion  # Mantener fecha de creación
                row[fecha_actualizado_idx] = current_date  # Actualizar fecha_actualizado
                
                patient_exists = True
                break
        
        # Si el paciente no existe, añadir nuevo registro
        if not patient_exists:
            # Crear una fila con valores vacíos
            new_row = [""] * len(headers)
            
            # Asignar valores a las columnas correctas
            new_row[0] = str(patient_info["id"])
            new_row[1] = patient_info["nombre"]
            new_row[2] = patient_info["apellido"]
            new_row[3] = str(patient_info["estatura"])
            new_row[4] = timestamps_str
            new_row[5] = right_knee_original_str
            new_row[6] = left_knee_original_str
            new_row[7] = right_knee_filtered_str
            new_row[8] = left_knee_filtered_str
            new_row[headers.index('tiempo_suavizado')] = timestamps_filtered_str
            new_row[headers.index('fecha_creacion')] = current_date
            new_row[headers.index('fecha_actualizado')] = current_date
            
            rows.append(new_row)
        
        # Escribir datos actualizados al CSV con configuración adecuada de comillas
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)  # Usar modo QUOTE_MINIMAL
            writer.writerow(headers)
            writer.writerows(rows)
        
        return True
    except Exception as e:
        print(f"Error al actualizar el registro del paciente: {e}")
        return False

def get_next_patient_id():
    """
    Obtiene el siguiente ID disponible para un nuevo paciente
    """
    try:
        max_id = 0
        
        if os.path.isfile(CSV_FILE_PATH):
            with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if row and row[0].isdigit():
                        max_id = max(max_id, int(row[0]))
        
        return max_id + 1
    except Exception as e:
        print(f"Error al obtener el siguiente ID: {e}")
        return 1  # Empezar desde 1 si hay algún error

def get_patient_data(patient_id):
    """
    Obtiene los datos completos de un paciente por su ID
    """
    try:
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['id'] == str(patient_id):
                    # Convertir datos de cadenas CSV a listas
                    tiempo = [float(t) for t in row['tiempo'].strip('"').split(',')] if row['tiempo'] else []
                    angulo_derecha = [float(a) for a in row['angulo_rodilla_derecha'].strip('"').split(',')] if row['angulo_rodilla_derecha'] else []
                    angulo_izquierda = [float(a) for a in row['angulo_rodilla_izquierda'].strip('"').split(',')] if row['angulo_rodilla_izquierda'] else []
                    
                    # También incluir datos originales si existen
                    angulo_derecha_original = []
                    angulo_izquierda_original = []
                    
                    if 'angulo_rodilla_derecha_original' in row and row['angulo_rodilla_derecha_original']:
                        angulo_derecha_original = [float(a) for a in row['angulo_rodilla_derecha_original'].strip('"').split(',')]
                    
                    if 'angulo_rodilla_izquierda_original' in row and row['angulo_rodilla_izquierda_original']:
                        angulo_izquierda_original = [float(a) for a in row['angulo_rodilla_izquierda_original'].strip('"').split(',')]
                    
                    return {
                        'id': int(row['id']),
                        'nombre': row['nombre'],
                        'apellido': row['apellido'],
                        'estatura': float(row['estatura']),
                        'tiempo': tiempo,
                        'angulo_rodilla_derecha': angulo_derecha,
                        'angulo_rodilla_izquierda': angulo_izquierda,
                        'angulo_rodilla_derecha_original': angulo_derecha_original,
                        'angulo_rodilla_izquierda_original': angulo_izquierda_original,
                        'fecha_creacion': row.get('fecha_creacion', ''),
                        'fecha_actualizado': row.get('fecha_actualizado', '')
                    }
        return None
    except Exception as e:
        print(f"Error al obtener datos del paciente: {e}")
        return None

def get_all_patients():
    """
    Obtiene una lista de todos los pacientes (datos básicos)
    """
    patients = []
    try:
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                patients.append({
                    'id': int(row['id']),
                    'nombre': row['nombre'],
                    'apellido': row['apellido'],
                    'estatura': float(row['estatura']),
                    'fecha_creacion': row.get('fecha_creacion', ''),
                    'fecha_actualizado': row.get('fecha_actualizado', '')
                })
        return patients
    except Exception as e:
        print(f"Error al obtener lista de pacientes: {e}")
        return []

def create_patient(nombre, apellido, estatura):
    """
    Crea un nuevo paciente en el CSV
    """
    try:
        # Obtener el siguiente ID disponible
        new_id = get_next_patient_id()
        
        # Crear un registro con datos vacíos para las mediciones
        patient_info = {
            "id": new_id,
            "nombre": nombre,
            "apellido": apellido,
            "estatura": estatura
        }
        
        # Usar la función de actualización con listas vacías
        success = update_patient_record(
            patient_info, 
            [], [], [], [], []
        )
        
        if success:
            return new_id
        return None
    except Exception as e:
        print(f"Error al crear paciente: {e}")
        return None

def delete_patient(patient_id):
    """
    Elimina un paciente del archivo CSV por su ID
    
    Args:
        patient_id (str): ID del paciente a eliminar
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
        str: Nombre completo del paciente eliminado o mensaje de error
    """
    try:
        # Leer todos los datos
        rows = []
        patient_name = ""
        
        with open(CSV_FILE_PATH, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Guardar encabezados
            rows.append(headers)
            
            for row in reader:
                if len(row) > 0 and row[0] == str(patient_id):
                    # Guardar nombre del paciente antes de eliminarlo
                    patient_name = f"{row[1]} {row[2]}"
                else:
                    rows.append(row)
        
        # Verificar que se encontró el paciente
        if not patient_name:
            return False, f"No se encontró el paciente con ID {patient_id}"
        
        # Escribir datos sin el paciente eliminado
        with open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        
        return True, patient_name
        
    except Exception as e:
        return False, f"Error al eliminar el paciente: {str(e)}"

def update_patient_info(patient_id, nombre, apellido, estatura):
    """
    Actualiza la información básica de un paciente sin afectar sus datos de medición
    """
    try:
        # Leer todos los datos
        rows = []
        updated = False
        
        with open(CSV_FILE_PATH, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)
            rows.append(headers)
            
            # Verificar si existe la columna fecha_actualizado
            if 'fecha_actualizado' not in headers:
                headers.append('fecha_actualizado')
                rows[0] = headers
            
            fecha_actualizado_idx = headers.index('fecha_actualizado')
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for row in reader:
                if len(row) > 0 and row[0] == str(patient_id):
                    # Asegurar que la fila tenga la longitud adecuada
                    while len(row) < len(headers):
                        row.append("")
                    
                    # Preservar los demás campos
                    updated_row = row.copy()
                    updated_row[1] = nombre      # Nombre
                    updated_row[2] = apellido    # Apellido
                    updated_row[3] = estatura    # Estatura
                    updated_row[fecha_actualizado_idx] = current_date  # Actualizar fecha
                    rows.append(updated_row)
                    updated = True
                else:
                    rows.append(row)
        
        if not updated:
            return False
            
        # Escribir datos actualizados
        with open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
            
        return True
        
    except Exception as e:
        print(f"Error al actualizar información del paciente: {str(e)}")
        return False

def load_patient_table_data():
    """
    Carga los datos de pacientes formateados para mostrar en una tabla
    
    Returns:
        list: Lista de listas con datos de pacientes [id, nombre, apellido, estatura, fecha_creacion, fecha_actualizado]
    """
    patient_rows = []
    try:
        if not os.path.isfile(CSV_FILE_PATH):
            return []
            
        with open(CSV_FILE_PATH, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Obtener encabezados
            
            fecha_creacion_idx = headers.index('fecha_creacion') if 'fecha_creacion' in headers else -1
            fecha_actualizado_idx = headers.index('fecha_actualizado') if 'fecha_actualizado' in headers else -1
            
            for row in reader:
                if len(row) > 0:  # Asegurar que hay datos en la fila
                    # Obtener datos básicos
                    patient_id = row[0]
                    nombre = row[1] if len(row) > 1 else ""
                    apellido = row[2] if len(row) > 2 else ""
                    estatura = row[3] if len(row) > 3 else ""
                    
                    # Obtener fechas con manejo seguro de índices
                    fecha_creacion = ""
                    if fecha_creacion_idx >= 0 and fecha_creacion_idx < len(row):
                        fecha_creacion = row[fecha_creacion_idx]
                    
                    fecha_actualizado = ""
                    if fecha_actualizado_idx >= 0 and fecha_actualizado_idx < len(row):
                        fecha_actualizado = row[fecha_actualizado_idx]
                    
                    # Formato: [id, nombre, apellido, estatura, fecha_creacion, fecha_actualizado]
                    patient_rows.append([
                        patient_id,
                        nombre,
                        apellido,
                        estatura,
                        fecha_creacion,
                        fecha_actualizado
                    ])
                    
        return patient_rows
        
    except Exception as e:
        print(f"Error al cargar datos de pacientes: {str(e)}")
        return []

def patient_has_angle_data(patient_id):
    """
    Verifica si un paciente tiene datos de ángulos guardados
    
    Args:
        patient_id (str): ID del paciente
        
    Returns:
        bool: True si tiene datos, False en caso contrario
    """
    try:
        if not os.path.isfile(CSV_FILE_PATH):
            return False
            
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Saltar encabezados
            
            for row in reader:
                if row and row[0] == str(patient_id):
                    # Verificar si hay datos en las columnas de ángulos
                    # Columnas 4 y 5 tienen los tiempos y ángulos
                    if len(row) >= 6 and row[4] and row[5]:
                        return True
            
        return False
        
    except Exception as e:
        print(f"Error al verificar datos de ángulos: {str(e)}")
        return False

def initialize_csv_file():
    """
    Creates the CSV file with headers if it doesn't exist.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(CSV_FILE_PATH):
            headers = ['id', 'nombre', 'apellido', 'estatura', 'tiempo', 
                      'angulo_rodilla_derecha_original', 'angulo_rodilla_izquierda_original',
                      'angulo_rodilla_derecha', 'angulo_rodilla_izquierda', 'tiempo_suavizado', 
                      'fecha_creacion', 'fecha_actualizado']
            
            with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
            print(f"Archivo {CSV_FILE_PATH} creado con éxito.")
        return True
    except Exception as e:
        print(f"Error al crear el archivo {CSV_FILE_PATH}: {str(e)}")
        return False

def get_patient_raw_data(patient_id=None):
    """
    Obtiene los datos brutos de un paciente por su ID como diccionario
    """
    try:
        if not os.path.isfile(CSV_FILE_PATH):
            return None
            
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Obtener encabezados
            
            for row in reader:
                if not row:
                    continue
                    
                if patient_id is None or row[0] == str(patient_id):
                    # Limpiar comillas extras en los datos (columnas 4-9)
                    for i in range(4, min(10, len(row))):
                        if i < len(row):
                            row[i] = row[i].replace('"', '')
                    
                    # Convertir row a diccionario usando los headers
                    # Asegurar que ambas listas tengan la misma longitud
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            row_dict[header] = row[i]
                        else:
                            row_dict[header] = ""
                    
                    return row_dict
        
        return None
        
    except Exception as e:
        print(f"Error al obtener datos del paciente: {str(e)}")
        return None

def save_patient_tracking_data(patient_info, data_dict, session_id=None):
    """
    Guarda los datos de seguimiento de un paciente incluyendo datos originales y filtrados.
    """
    try:
        # Generar ID de sesión si no se proporciona
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Preparar la información del paciente
        patient_id = patient_info["id"] 
        nombre = patient_info["nombre"]
        apellido = patient_info["apellido"]
        estatura = patient_info["estatura"]
        
        # Preparar las cadenas de datos con formato
        tiempo_str = ",".join([f"{t:.2f}" for t in data_dict["tiempo"]])
        izq_orig_str = ",".join([f"{a:.2f}" for a in data_dict["angulo_rodilla_izquierda"]])
        der_orig_str = ",".join([f"{a:.2f}" for a in data_dict["angulo_rodilla_derecha"]])
        
        # Agregar datos filtrados si existen
        izq_filt_str = ""
        der_filt_str = ""
        
        if "angulo_rodilla_izquierda_suavizado" in data_dict:
            izq_filt_str = ",".join([f"{a:.2f}" for a in data_dict["angulo_rodilla_izquierda_suavizado"]])
        if "angulo_rodilla_derecha_suavizado" in data_dict:
            der_filt_str = ",".join([f"{a:.2f}" for a in data_dict["angulo_rodilla_derecha_suavizado"]])
            
        # Preparar datos de tiempo_suavizado si existen
        tiempo_suavizado_str = ""
        if "tiempo_suavizado" in data_dict:
            tiempo_suavizado_str = ",".join([f"{t:.2f}" for t in data_dict["tiempo_suavizado"]])
        
        # Obtener fecha actual
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Leer el archivo CSV actual
        rows = []
        headers = []
        file_exists = os.path.isfile(CSV_FILE_PATH)
        
        if file_exists:
            with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = next(reader)  # Obtener encabezados
                for row in reader:
                    rows.append(row)
        else:
            # Si el archivo no existe, crear encabezados
            headers = ['id', 'nombre', 'apellido', 'estatura', 'tiempo', 
                      'angulo_rodilla_derecha_original', 'angulo_rodilla_izquierda_original',
                      'angulo_rodilla_derecha', 'angulo_rodilla_izquierda', 'tiempo_suavizado',
                      'fecha_creacion', 'fecha_actualizado']
        
        # Añadir columnas si no existen
        if 'tiempo_suavizado' not in headers:
            # Insertar antes de fecha_creacion
            if 'fecha_creacion' in headers:
                headers.insert(headers.index('fecha_creacion'), 'tiempo_suavizado')
            else:
                headers.append('tiempo_suavizado')
                
        if 'fecha_actualizado' not in headers:
            headers.append('fecha_actualizado')
            
        fecha_creacion_idx = headers.index('fecha_creacion') if 'fecha_creacion' in headers else -1
        fecha_actualizado_idx = headers.index('fecha_actualizado') if 'fecha_actualizado' in headers else -1
        tiempo_suavizado_idx = headers.index('tiempo_suavizado') if 'tiempo_suavizado' in headers else -1
        
        # Comprobar si el paciente ya existe
        patient_exists = False
        creation_date = current_date  # Default for new patients
        
        for i, row in enumerate(rows):
            if row[0] == str(patient_id):
                # Asegurar que la fila tenga la longitud adecuada
                while len(row) < len(headers):
                    row.append("")
                
                # Preservar la fecha de creación original
                if fecha_creacion_idx >= 0 and fecha_creacion_idx < len(row) and row[fecha_creacion_idx]:
                    creation_date = row[fecha_creacion_idx]
                
                # Actualizar registro existente
                rows[i] = [
                    str(patient_id), 
                    nombre, 
                    apellido, 
                    str(estatura),
                    tiempo_str,
                    der_orig_str,
                    izq_orig_str,
                    der_filt_str if der_filt_str else der_orig_str,
                    izq_filt_str if izq_filt_str else izq_orig_str,
                ]
                
                # Añadir tiempo_suavizado
                if tiempo_suavizado_idx >= 0:
                    # Extender la fila si es necesario
                    while len(rows[i]) <= tiempo_suavizado_idx:
                        rows[i].append("")
                    rows[i][tiempo_suavizado_idx] = tiempo_suavizado_str
                
                # Añadir fecha_creacion
                if fecha_creacion_idx >= 0:
                    while len(rows[i]) <= fecha_creacion_idx:
                        rows[i].append("")
                    rows[i][fecha_creacion_idx] = creation_date
                
                # Añadir fecha_actualizado
                if fecha_actualizado_idx >= 0:
                    while len(rows[i]) <= fecha_actualizado_idx:
                        rows[i].append("")
                    rows[i][fecha_actualizado_idx] = current_date
                
                patient_exists = True
                break
        
        # Si el paciente no existe, añadir nuevo registro
        if not patient_exists:
            new_row = [""] * len(headers)
            new_row[0] = str(patient_id)
            new_row[1] = nombre
            new_row[2] = apellido
            new_row[3] = str(estatura)
            new_row[4] = tiempo_str
            new_row[5] = der_orig_str
            new_row[6] = izq_orig_str
            new_row[7] = der_filt_str if der_filt_str else der_orig_str
            new_row[8] = izq_filt_str if izq_filt_str else izq_orig_str
            
            if tiempo_suavizado_idx >= 0:
                new_row[tiempo_suavizado_idx] = tiempo_suavizado_str
            
            if fecha_creacion_idx >= 0:
                new_row[fecha_creacion_idx] = current_date
                
            if fecha_actualizado_idx >= 0:
                new_row[fecha_actualizado_idx] = current_date
            
            rows.append(new_row)
        
        # Escribir datos actualizados al CSV
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)
        
        return True
    except Exception as e:
        print(f"Error al guardar datos del paciente: {e}")
        return False
