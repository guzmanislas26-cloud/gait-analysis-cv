# Gait Cycle Knee Goniometry System

> Non-invasive, real-time knee angle measurement during the gait cycle using computer vision and pose estimation — developed as a final project in biomedical engineering at Universidad Iberoamericana Puebla.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-Desktop_App-41CD52?logo=qt)](https://www.riverbankcomputing.com/software/pyqt/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Pose-orange)](https://mediapipe.dev)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.7-green?logo=opencv)](https://opencv.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

Desktop application built with **PyQt6** that measures **knee joint angles** in real time during the human gait cycle using a standard webcam and **MediaPipe Pose**. The system detects hip, knee, and ankle landmarks, computes flexion-extension angles via the law of cosines, and displays real-time graphs of both knees.

Designed as an accessible alternative to clinical-grade electrogoniometers for gait analysis in resource-constrained environments.

**Validated with 47 healthy participants**, comparing results against a Biometrics DataLink electrogoniometer:

- **RMSE**: 12.31° (right knee), 10.30° (left knee)
- **Pearson correlation**: 0.78 (right), 0.86 (left)

---

## Key Features

- **Real-time pose detection** — MediaPipe Pose detects hip, knee, and ankle joints at 30 FPS
- **Bilateral knee angle tracking** — simultaneous left and right knee goniometry using the law of cosines
- **Live angle graphs** — real-time Matplotlib plots for both knees with a 5-second sliding window
- **Sagittal plane detection** — warns the user when not positioned in the correct lateral view
- **Patient management** — add, edit, delete, and load patients; data stored in CSV
- **Height calibration** — distance estimation via pinhole camera model
- **Data smoothing** — B-spline interpolation (300 points) for noise reduction
- **Video recording** — saves annotated video of each session per patient
- **Interactive graph viewer** — post-session analysis with zoom, pan, and export
- **Data export** — per-patient CSV with raw and filtered angle data plus timestamps

---

## System Architecture

```
Webcam (30 FPS)
    │
    ▼
MediaPipe Pose ──► Joint Detection (hip, knee, ankle)
    │
    ▼
Angle Computation (law of cosines)
    │
    ├──► Real-time Graphs (Matplotlib)
    ├──► Annotated Video Feed (OpenCV + PyQt6)
    ├──► CSV Data Storage (per patient)
    └──► Video Recording (.mp4)
```

---

## Tech Stack

- **GUI Framework** — PyQt6
- **Pose Estimation** — MediaPipe Pose
- **Video Processing** — OpenCV 4.7
- **Numerical Analysis** — NumPy, SciPy (B-spline interpolation)
- **Data Handling** — Pandas, CSV
- **Visualization** — Matplotlib
- **Language** — Python 3.11

---

## Project Structure

```
gait-analysis-cv/
├── main.py                         # Application entry point (QMainWindow + navigation)
├── components/
│   └── ui_components.py            # Reusable UI widgets (ModernButton, ModernInput)
├── utils/
│   └── csv_manager.py              # Patient CRUD operations and CSV data handling
├── views/
│   ├── home.py                     # Home screen with navigation
│   ├── form.py                     # Patient registration form
│   ├── patient_list.py             # Patient list with table view
│   ├── pantalla_detector.py        # Main detection screen (pose, graphs, recording)
│   └── interactive_viewer.py       # Post-session interactive graph analysis
├── requirements.txt
├── LICENSE
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip
- Webcam (built-in or external USB, 1080p recommended)

### Installation

```bash
git clone https://github.com/guzmanislas26-cloud/gait-analysis-cv.git
cd gait-analysis-cv
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Recommended Conditions

- **Background**: solid color to avoid detection interference
- **Clothing**: fitted, light-colored, no loose garments
- **Lighting**: natural or artificial, no harsh shadows
- **Camera angle**: sagittal plane (side view) for accurate knee angle measurement
- **Hardware**: 8 GB RAM, Intel i5 / Ryzen 5 or better

---

## Methodology

1. **Joint detection** — MediaPipe Pose processes each frame and identifies hip, knee, and ankle landmarks on both legs with ~95% accuracy in optimal conditions.
2. **Angle computation** — Knee flexion-extension angles are calculated using the law of cosines from the three joint coordinates (hip–knee–ankle).
3. **Real-time visualization** — Angles are plotted live on per-knee Matplotlib graphs embedded in the PyQt6 interface.
4. **Signal smoothing** — A cubic B-spline interpolation with 300 uniformly spaced points is applied to reduce noise and improve signal curvature.
5. **Data persistence** — Raw and filtered angle data, timestamps, and patient info are saved to CSV for each session.

---

## Validation Results

The system was tested on **47 clinically healthy participants** (students and faculty from Universidad Iberoamericana Puebla). Signals were compared against a **Biometrics DataLink electrogoniometer** using synchronized measurements under controlled conditions (5m walking path, fixed camera at 4m height).

Post-processing included interpolation to 500 points, Butterworth low-pass filtering, temporal synchronization, and phase offset adjustment.

- **Right knee** — RMSE: 12.31°, Pearson r: 0.78
- **Left knee** — RMSE: 10.30°, Pearson r: 0.86

---

## Limitations

- Accuracy depends on video quality, camera angle, and lighting
- Sagittal plane (side view) positioning is required for reliable measurements
- 3D joint angles are approximated from 2D projections
- Does not replace clinical-grade motion capture systems (e.g., Vicon, Qualisys)
- Performance may degrade with occlusion or loose clothing

---

## Future Work

- [ ] Extend tracking to additional joints (hip, ankle)
- [ ] Optimize performance for lower-spec hardware
- [ ] Conduct clinical studies for use in healthcare environments
- [ ] Export to standardized clinical formats (C3D)
- [ ] Web-based interface for remote clinical upload and reporting

---

## Academic Context

This project was developed as the final project for **Implementación y Evaluación de Proyectos** at **Universidad Iberoamericana Puebla**, Spring 2025.

> **Advisor**: Mtro. Francisco Cantú Hernández
>
> **Visiting professors**: Mtra. Ana Moreno Hernández, Mtra. Rubí Salazar Amador

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Authors

**Luis Humberto Islas Guzmán** — Biomedical Engineering
[GitHub](https://github.com/guzmanislas26-cloud)

**Diego Rodríguez Orozco** — Computer Systems Engineering
