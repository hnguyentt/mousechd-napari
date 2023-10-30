import napari
from magicgui import magic_factory
from napari.layers import Image
from napari.utils.notifications import show_error
from napari.qt.threading import thread_worker
import numpy as np
import os
import pathlib
import pyqtgraph as pg
from qtpy.QtWidgets import (QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QLabel,
                            QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                            QFileDialog, QComboBox, QAbstractItemView, QCheckBox,
                            QHeaderView, QRadioButton, QGridLayout, QLineEdit, QTextEdit)
from qtpy.QtGui import QPixmap, QFont
from qtpy.QtCore import Qt, QSize

# Constants
## Style
header_style = QFont("Helvetica [Cronyx]", 15)
parameter_style = QFont("Helvetica [Cronyx]", 12)
help_style = QFont("Helvetica [Cronyx]", 10)
box_style = "margin:5px; border-style:outset; border-width:1px; border-color:rgb(255, 255, 255); border-radius:10px"
unset_box_style = "border:0px"

resources = ["local", "server"]
tasks = ["segment", "diagnose", "retrain"]

class MouseCHD(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        
        self.setLayout(QVBoxLayout()) # main layout
        
        # Title
        ## Text
        header_container = QWidget()
        header_container.setLayout(QVBoxLayout())
        header_label = QLabel('Mouse Congenital Heart Disease')
        header_label.setFont(QFont("Helvetica [Cronyx]", 18, weight=QFont.Bold))
        header_container.layout().addWidget(header_label, alignment=Qt.AlignCenter)
        ## Logo
        logo_size = QSize(450, 450)
        logo_path = pathlib.Path(__file__).parent.joinpath(os.path.join('assets', 'thumbnail.png'))
        logo = QPixmap(str(logo_path))
        logo = logo.scaled(logo_size, Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        logo_label = QLabel()
        logo_label.setPixmap(logo)
        logo_label.setMinimumWidth(500)
        header_container.layout().addWidget(logo_label, alignment=Qt.AlignCenter)
        ## Credit
        credit_label = QLabel("@IMOD, Institut Pasteur\n" + "-"*35)
        credit_label.setFont(QFont("Helvetica [Cronyx]", 10))
        header_container.layout().addWidget(credit_label, alignment=Qt.AlignLeft)
        
        self.layout().addWidget(header_container, alignment=Qt.AlignCenter)
        
        # Resources
        resrc_container = QWidget()
        resrc_container.setLayout(QVBoxLayout())
        
        resrc_choices_container = QWidget()
        resrc_choices_container.setLayout(QHBoxLayout())
        resrc_choice_label = QLabel("Choose a resource: ")
        resrc_choice_label.setFont(parameter_style)
        resrc_choices_container.layout().addWidget(resrc_choice_label, alignment=Qt.AlignLeft)
        
        resrc_choices = QWidget()
        resrc_choices.setLayout(QHBoxLayout())
        resrc_buttons = [QRadioButton(resource) for resource in resources]
        for button in resrc_buttons:
            button.setFont(parameter_style)
            button.setStyleSheet(unset_box_style)
            button.toggled.connect(lambda _, button=button: self._button_state_setter(button))
            resrc_choices.layout().addWidget(button)
        resrc_choices.setStyleSheet(box_style) 
        resrc_choices_container.layout().addWidget(resrc_choices)
        resrc_container.layout().addWidget(resrc_choices_container)
        
        ## Server
        self.server_container = QWidget()
        self.server_container.setLayout(QVBoxLayout())
        ### Name
        servername_container = QWidget()
        servername_container.setLayout(QHBoxLayout())
        servername_label = QLabel("Server name: ")
        servername_label.setFont(parameter_style)
        self.servername = QLineEdit(self)
        self.servername.setPlaceholderText("<insert server name here>")
        servername_container.layout().addWidget(servername_label)
        servername_container.layout().addWidget(self.servername)
        self.server_container.layout().addWidget(servername_container)
        self.server_container.hide()
        resrc_container.layout().addWidget(self.server_container)
        
        ## Change
        for btn in resrc_buttons:
            btn.toggled.connect(lambda _, btn=btn: self._on_resrc_changed(btn))
        
        resrc_container.layout().addWidget(QLabel("<hr>"))
        
        self.layout().addWidget(resrc_container)
        
        # Input
        input_container = QWidget()
        input_container.setLayout(QHBoxLayout())
        input_label = QLabel("Select input image: ")
        input_label.setFont(parameter_style)
        input_container.layout().addWidget(input_label, alignment=Qt.AlignLeft)
        self._image_layers = QComboBox(self)
        input_container.layout().addWidget(self._image_layers)
        input_container.layout().setSpacing(0)
        self.layout().addWidget(input_container)
        
        # Tasks
        task_container = QWidget()
        task_container.setLayout(QVBoxLayout())
        task_container.layout().addWidget(QLabel("<hr>"))
        
        task_choices_container = QWidget()
        task_choices_container.setLayout(QHBoxLayout())
        task_choice_label = QLabel("Choose a task:")
        task_choice_label.setFont(parameter_style)
        task_choices_container.layout().addWidget(task_choice_label, alignment=Qt.AlignLeft)
        
        task_choices = QWidget()
        task_choices.setLayout(QHBoxLayout())
        task_buttons = [QRadioButton(task) for task in tasks]
        for button in task_buttons:
            button.setFont(parameter_style)
            button.setStyleSheet(unset_box_style)
            button.toggled.connect(lambda _, button=button: self._button_state_setter(button))
            task_choices.layout().addWidget(button)
        task_choices.setStyleSheet(box_style)
        task_choices_container.layout().addWidget(task_choices)
        task_container.layout().addWidget(task_choices_container)
        task_container.layout().addWidget(QLabel("<hr>"))
        self.layout().addWidget(task_container)
        
    
    
    def _button_state_setter(self, button):
        self._button_state = button.text()
        
    
    def _on_resrc_changed(self, btn):
        if (btn.text() == "server") and btn.isChecked():
            self.server_container.show()
        else:
            self.server_container.hide()
        
        
        
        
        
        