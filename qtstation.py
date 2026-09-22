import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QSurfaceFormat
from OpenGL.GL import (glClearColor, glClear, 
                       glViewport, GL_COLOR_BUFFER_BIT)

class GLWidget(QOpenGLWidget):
    def initializeGL(self):
        # Context is current here. Create shaders, VBOs, textures.
        glClearColor(0.08, 0.20, 0.14, 1.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        # Context is current. Do not call makeCurrent() yourself.
        glClear(GL_COLOR_BUFFER_BIT)

class StationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Station")
        
        # Create the main vertical layout
        main_layout = QVBoxLayout(self)
        
        # Create a horizontal layout for the top buttons
        button_layout = QHBoxLayout()
        
        # Create the buttons matching the image
        self.btn_arm = QPushButton("Arm")
        self.btn_takeoff = QPushButton("TakeOff")
        self.btn_play = QPushButton("Play")
        self.btn_land = QPushButton("Land")
        self.btn_step = QPushButton("Step")
        self.btn_halt = QPushButton("Halt")
        
        # Add buttons to the horizontal layout
        button_layout.addWidget(self.btn_arm)
        button_layout.addWidget(self.btn_takeoff)
        button_layout.addWidget(self.btn_play)
        button_layout.addWidget(self.btn_land)
        button_layout.addWidget(self.btn_step)
        button_layout.addWidget(self.btn_halt)
        
        # Add a stretch to push buttons to the left (optional, remove to space them evenly)
        button_layout.addStretch()
        
        # Add the horizontal button layout to the top of the main layout
        main_layout.addLayout(button_layout)
        
        # Initialize and add your existing GLWidget below the buttons
        self.glWidget = GLWidget()
        main_layout.addWidget(self.glWidget)

if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    
    # Initialize the new main window instead of just GLWidget
    w = StationWindow()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())