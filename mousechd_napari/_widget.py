import logging
import time
from datetime import datetime
import os, sys
import json
import re
import pathlib
import subprocess

import napari
from napari.layers import Image
from napari.utils.notifications import show_info
from napari.utils.notifications import show_error
from napari.qt.threading import thread_worker
from qtpy.QtWidgets import (QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QLabel,
                            QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
                            QFileDialog, QComboBox, QAbstractItemView, QCheckBox,
                            QRadioButton, QLineEdit, QScrollArea, QDialog, QMessageBox)
from qtpy.QtGui import QPixmap, QFont, QMovie
from qtpy.QtCore import Qt, QSize

import pandas as pd
import numpy as np
import SimpleITK as sitk
from sklearn.model_selection import train_test_split

import torch
import tensorflow as tf

# Fix the problem when installing plugin from Napari hub
#========================================================#
import pkgutil
if pkgutil.find_loader("mousechd") is None:
    os.system(f"{sys.executable} -m pip install mousechd")
#========================================================#

from mousechd.utils.tools import CACHE_DIR, set_logger
from mousechd.classifier.utils import download_clf_models, CLF_DIR
from mousechd.segmentation.utils import download_seg_models
from mousechd.classifier.models import load_MouseCHD_model
from mousechd.datasets.utils import (get_largest_connectivity,
                                     get_translate_values)
from mousechd.datasets.preprocess import x5_df, merge_base_x5_labels


from ._utils import (is_relative_to, 
                     SLURM_CMD,
                     LIB_PATH, 
                     MODULE_LS,
                     EXPORTS,
                     segment_heart,
                     segment_hearts,
                     gen_white2red_colormap,
                     gen_transturbo_colormap,
                     diagnose_heart,
                     preprocess,
                     resample,
                     retrain)
from .assets import download_assets


# Constants
## Style
header_font = QFont("Helvetica [Cronyx]", 15)
parameter_font = QFont("Helvetica [Cronyx]", 12)
help_font = QFont("Helvetica [Cronyx]", 10)
help_style = "color:orange"
box_style = "margin:5px; border-style:outset; border-width:1px; border-color:rgb(255, 255, 255); border-radius:10px"
unset_box_style = "border:0px"
checked_style = "color:green; font:bold; border:0px"
unchecked_style = "color:white; font:normal; border:0px"
run_btn_style = "background-color:rgb(116, 116, 24); font:bold"
stop_btn_style = "background-color:red; font:bold"
run_tsb_btn_style = "background-color:rgb(245,124,0); font:bold"
cache_btn_style = "background-color:red; font:bold"
warning_style = "background-color:yellow"
unwarning_style = "background-color:black"
error_style = "color:red"

diag_header_style = "color:white; font:bold; margin:10px; border-style:outset; border-width:2px; border-color:blue; background-color:blue"
hidestyle = 'style="color:#24292E;font-size:12px;"'
comstyle = 'style="color:gray;background-color:gray;font-size:10px;"'

COLORS = {"CHD": "red", "Normal": "green"}
resources = ["local", "server"]
tasks = ["segment", "diagnose", "retrain"]

issueLink = "<a href=\"https://github.com/hnguyentt/mousechd-napari/issues\"> <font color=green> issues</font> </a>"


# Restore default variables
try:
    default_vars = json.load(open(os.path.join(CACHE_DIR, "Napari", "vars.json"), "r"))
    servername = default_vars.get("servername", "")
    shared_folder = default_vars.get("shared_folder", "")
    lib_path = default_vars.get("lib_path", LIB_PATH)
    slurm_cmd = default_vars.get("slurm_cmd", SLURM_CMD)
    module_ls = default_vars.get("module_ls", MODULE_LS)
    exports = default_vars.get("exports", EXPORTS)
    outdir = default_vars.get("outdir", "")
    if not os.path.isdir(os.path.dirname(outdir)):
        outdir = ""
        
except FileNotFoundError:
    servername = ""
    shared_folder = ""
    lib_path = LIB_PATH
    slurm_cmd = SLURM_CMD
    module_ls = MODULE_LS
    exports = EXPORTS
    outdir = ""
    
    default_vars = {"servername": servername,
                    "shared_folder": shared_folder,
                    "lib_path": lib_path,
                    "slurm_cmd": slurm_cmd,
                    "module_ls": module_ls,
                    "exports": exports,
                    "outdir": outdir}
    os.makedirs(os.path.join(CACHE_DIR, "Napari"), exist_ok=True)
    with open(os.path.join(CACHE_DIR, "Napari", "vars.json"), "w") as f:
        json.dump(default_vars, f, indent=1)
    
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

try:
    tf.test.is_gpu_available()
except:
    tf.config.set_visible_devices([], 'GPU')
 
download_assets()   
        
class MouseCHD(QScrollArea):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        
        self.container = QWidget()
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.container.setLayout(QVBoxLayout()) # main layout         
        
        #########
        # TITLE #
        #########
        ## Text
        header_container = QWidget()
        header_container.setLayout(QVBoxLayout())
        header_label = QLabel('Mouse Congenital Heart Disease')
        header_label.setFont(QFont("Helvetica [Cronyx]", 18, weight=QFont.Bold))
        header_container.layout().addWidget(header_label, alignment=Qt.AlignCenter)
        ## Logo
        logo_size = QSize(450, 450)
        logo_path = os.path.join(CACHE_DIR, "Napari", 'assets', 'thumbnail.png')
        print(logo_path)
        logo = QPixmap(str(logo_path))
        logo = logo.scaled(logo_size, Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        logo_label = QLabel()
        logo_label.setPixmap(logo)
        logo_label.setMinimumWidth(500)
        header_container.layout().addWidget(logo_label, alignment=Qt.AlignCenter)
        ## Credit
        credit_container = QWidget()
        credit_container.setLayout(QHBoxLayout())
        credit_label = QLabel("@IMOD, Institut Pasteur\n" + "-"*35)
        credit_label.setFont(QFont("Helvetica [Cronyx]", 10))
        credit_container.layout().addWidget(credit_label)
        link = "<a href=\"https://github.com/hnguyentt/mousechd-napari/blob/master/docs\"> <font color=blue>Quickstart</font></a>"
        tut_label = QLabel(link)
        tut_label.setFont(QFont("Helvetica [Cronyx]", 15))
        tut_label.setOpenExternalLinks(True)
        credit_container.layout().addWidget(tut_label)
        header_container.layout().addWidget(credit_container, alignment=Qt.AlignLeft)
        
        self.container.layout().addWidget(header_container, alignment=Qt.AlignCenter)
        
        
        #############
        # Resources # 
        #############
        resrc_container = QWidget()
        resrc_container.setLayout(QVBoxLayout())
        self.resrc = "local"
        resrc_choices_container, resrc_buttons = self.create_RadioButtons(label="Choose a resource: ",
                                                                          choices=resources,
                                                                          default_idx=0)
        
        resrc_container.layout().addWidget(resrc_choices_container)
        
        ## Server
        self.server_container = QWidget()
        self.server_container.setLayout(QVBoxLayout())
        ### Instruction
        urlLink = "<a href=\"https://github.com/hnguyentt/mousechd-napari/blob/master/docs/server_setup.md\"> <font color=green> server setup tutorial</font> </a>"
        instruction = self.create_help_text(f"To run the plugin with a remote server backend, please follow this instruction: {urlLink}")
        self.server_container.layout().addWidget(instruction)
        ### Name
        self.servername = QLineEdit()
        servername_container = self.create_QLineEdit(att_name="servername",
                                                     label="Server name*: ",
                                                     placeholder="<insert server name here>")
        self.servername.setText(servername)
        self.servername.textChanged.connect(self._unset_servername_warning)
        self.server_container.layout().addWidget(servername_container)
        
        # Lib path
        self.lib_path = QLineEdit()
        libpath_container = self.create_QLineEdit(att_name="lib_path",
                                                  label="Library path",
                                                  default_txt=lib_path)
        self.server_container.layout().addWidget(libpath_container)
        
        self.slurm = QCheckBox("Slurm", self)
        self.slurm_cmd = QLineEdit()
        self.slurm_container = self.create_checkbox(box_name="slurm", txt_name="slurm_cmd", default_txt=slurm_cmd)
        self.slurm.stateChanged.connect(self._on_slurm_changed)
        self.slurm_cmd.hide()
        self.server_container.layout().addWidget(self.slurm_container)
        
        self.module = QCheckBox("Load modules", self)
        self.module_ls = QLineEdit()
        self.module_container = self.create_checkbox(box_name="module", txt_name="module_ls", default_txt=module_ls)
        self.module.stateChanged.connect(self._on_module_changed)
        self.module_ls.hide()
        self.server_container.layout().addWidget(self.module_container)
        
        self.export = QCheckBox("Export flags", self)
        self.export_cmd = QLineEdit()
        self.export_container = self.create_checkbox(box_name="export", txt_name="export_cmd", default_txt=exports)
        self.export.stateChanged.connect(self._on_export_changed)
        self.export_cmd.hide()
        self.server_container.layout().addWidget(self.export_container)
        
        ### Shared folder
        self.shared_folder = QLineEdit()
        folder_container = self.create_folder_browser(label="Shared folder*: ",
                                                      att_name="shared_folder",
                                                      header="Select a Shared Directory between local and remote server")
        self.shared_folder.setText(shared_folder)
        self.shared_folder.textChanged.connect(self._unset_shared_folder_warning)
        self.server_container.layout().addWidget(folder_container)
        self.server_container.hide()
        
        resrc_container.layout().addWidget(self.server_container)
        
        ## Change
        for btn in resrc_buttons:
            btn.toggled.connect(lambda _, btn=btn: self._on_resrc_changed(btn))
        
        resrc_container.layout().addWidget(QLabel("<hr>"))
        
        self.container.layout().addWidget(resrc_container)
        
        ######### 
        # INPUT #
        #########
        input_container = QWidget()
        input_container.setLayout(QHBoxLayout())
        input_label = QLabel("Select input image: ")
        input_label.setFont(parameter_font)
        input_container.layout().addWidget(input_label, alignment=Qt.AlignLeft)
        self._image_layers = QComboBox(self)
        self._image_layers.currentTextChanged.connect(self._unset_input_warning)
        input_container.layout().addWidget(self._image_layers)
        input_container.layout().setSpacing(0)
        self.container.layout().addWidget(input_container)
        
        self.viewer.layers.events.inserted.connect(self._update_combo_boxes)
        self.viewer.layers.events.removed.connect(self._update_combo_boxes)
        
        #########
        # TASKS #
        #########
        task_container = QWidget()
        task_container.setLayout(QVBoxLayout())
        task_container.layout().addWidget(QLabel("<hr>"))
        self.task = tasks[1]
        task_choices_container, task_buttons = self.create_RadioButtons(label="Choose a task: ",
                                                                        choices=tasks,
                                                                        default_idx=1)
        task_container.layout().addWidget(task_choices_container)
        
        # Models
        
        self.model_name = "default"
        self.model_container = QWidget()
        self.model_container.setLayout(QVBoxLayout())
        model_container, model_buttons = self.create_RadioButtons(label="Choose a model type: ",
                                                                  choices=["default", "retrained"],
                                                                  default_idx=0)
        self.model_container.layout().addWidget(model_container)
        
        # Custom model
        self.custom_model_container = QWidget()
        self.custom_model_container.setLayout(QVBoxLayout())
        self.model_path = QLineEdit()
        custom_model_container = self.create_folder_browser(label="Custom model path: ",
                                                            att_name="model_path",
                                                            header="Custome model path")
        self.model_path.textChanged.connect(self._unset_model_path)
        self.custom_model_container.layout().addWidget(custom_model_container)
        self.model_path.textChanged.connect(self._on_model_path_changed)
        help_txt = f"You chose to run on server, the custom model must placed in the shared folder."
        # self.custom_instruct = self.create_help_text(help_txt)
        # self.custom_model_container.layout().addWidget(self.custom_instruct)
        self.model_container.layout().addWidget(self.custom_model_container)
        task_container.layout().addWidget(self.model_container)
        # self.custom_instruct.hide()
        self.custom_model_container.hide()
        
        
        # Retrain
        self.retrain_container = QWidget()
        self.retrain_container.setLayout(QVBoxLayout())
        label = QLabel("Data for retraining")
        label.setFont(header_font)
        self.retrain_container.layout().addWidget(label, alignment=Qt.AlignCenter)
        retrain_help_txt = f"You chose to run on remote server, all following directories must be placed on the shared folder. See {urlLink} for more details."
        self.retrain_instruct = self.create_help_text(retrain_help_txt)
        self.retrain_container.layout().addWidget(self.retrain_instruct)
        self.retrain_instruct.hide()
        self.data_dir = QLineEdit()
        self.outdir = QLineEdit()
        data_dir = self.create_folder_browser(label="Data directory",
                                              att_name="data_dir",
                                              header="Choose data directory")
        self.data_dir.textChanged.connect(self._unset_data_dir_warning)
        w_outdir = self.create_folder_browser(label="Output directory",
                                              att_name="outdir",
                                              header="Choose a Output directory")
        self.outdir.textChanged.connect(self._on_outdir_changed)
        self.retrain_container.layout().addWidget(data_dir)
        self.retrain_container.layout().addWidget(w_outdir)
        self.exp = QLineEdit()
        today = datetime.today().strftime("%Y-%m-%d")
        exp = self.create_QLineEdit(att_name="exp",
                                    label="Experiment name",
                                    default_txt=today)
        self.retrain_container.layout().addWidget(exp)
        self.epochs = QLineEdit()
        epochs = self.create_QLineEdit(att_name="epochs",
                                       label="# epochs",
                                       default_txt="20")
        self.retrain_container.layout().addWidget(epochs)
        
        
        self.pp_resrc = "local"
        self.pp_resrc_container, pp_btns = self.create_RadioButtons(label="Preprocess",
                                                                           choices=["local", "server"],
                                                                           default_idx=0)
        self.pp_resrc_container.hide()
        self.retrain_container.layout().addWidget(self.pp_resrc_container)
        
        task_container.layout().addWidget(self.retrain_container)
        self.retrain_container.hide()
        
        
        # Changes
        for btn in task_buttons:
            btn.toggled.connect(lambda _, btn=btn: self._on_task_changed(btn))
            
        for btn in model_buttons:
            btn.toggled.connect(lambda _, btn=btn: self._on_model_changed(btn))
            
        for btn in pp_btns:
            btn.toggled.connect(lambda _, btn=btn: self._on_preprocess_choice_change(btn))
        
        task_container.layout().addWidget(QLabel("<hr>"))
        self.container.layout().addWidget(task_container)
        
        #######
        # RUN #
        #######
        self.run_btn = QPushButton(self.task.capitalize())
        self.run_btn.setFont(parameter_font)
        self.run_btn.setStyleSheet(run_btn_style)
        self.run_btn.clicked.connect(self.run_task)
        self.container.layout().addWidget(self.run_btn)
        
        # Stop button
        self.stop_btn = QPushButton("Stop: {}".format(self.task.capitalize()))
        self.stop_btn.setFont(parameter_font)
        self.stop_btn.setStyleSheet(stop_btn_style)
        self.stop_btn.clicked.connect(self.stop_task)
        self.container.layout().addWidget(self.stop_btn)
        self.stop_btn.hide()
        
        # Tensorboard
        ## Start
        self.tsb_msg = QLabel()
        self.tsb_msg.setFont(parameter_font)
        self.tsb_msg.setOpenExternalLinks(True)
        self.tsb_msg.setStyleSheet(help_style)
        self.run_tsb_btn = QPushButton("Run Tensorboard")
        self.run_tsb_btn.setFont(parameter_font)
        self.run_tsb_btn.setStyleSheet(run_tsb_btn_style)
        self.run_tsb_btn.clicked.connect(self.run_tsb)
        self.container.layout().addWidget(self.run_tsb_btn)
        self.container.layout().addWidget(self.tsb_msg)
        self.run_tsb_btn.hide()
        self.tsb_msg.hide()
        
        
        ################
        # BUSY MESSAGE #
        ################
        self.busy_container = QWidget()
        self.busy_container.setLayout(QVBoxLayout())
        busy_mouse_path = os.path.join(CACHE_DIR, "Napari", "assets", "busy_mouse.gif")
        busy_mouse = QMovie(str(busy_mouse_path))
        movie_screen = QLabel()
        movie_screen.setMinimumSize(QSize(300,200))
        movie_screen.setAlignment(Qt.AlignCenter)
        busy_mouse.setCacheMode(QMovie.CacheAll)
        busy_mouse.setSpeed(100)
        busy_mouse.setScaledSize(QSize(300,200))
        movie_screen.setMovie(busy_mouse)
        self.busy_container.layout().addWidget(movie_screen)
        
        message = QLabel("I'm on my way! Be patient!")
        message.setFont(parameter_font)
        self.busy_container.layout().addWidget(message, alignment=Qt.AlignCenter)
        
        self.container.layout().addWidget(self.busy_container, alignment=Qt.AlignCenter)
        self.busy_container.hide()
        busy_mouse.start()
        
        #########
        # CACHE #
        #########
        self.cache_btn = QPushButton("Delete Cache")
        self.cache_btn.setFont(parameter_font)
        self.cache_btn.setStyleSheet(cache_btn_style)
        self.cache_btn.clicked.connect(self.delete_cache)
        self.container.layout().addWidget(self.cache_btn)
        
        ########
        # LOGS #
        ########
        self.log_container = QWidget()
        self.log_container.setLayout(QVBoxLayout())
        self.run_log = QLabel()
        self.run_log.setText("============// RUN LOG //============")
        self.run_log.setFont(parameter_font)
        self.run_log.setWordWrap(True)
        self.log_container.layout().addWidget(self.run_log)
        self.error = QLabel()
        self.error.setFont(parameter_font)
        self.error.setStyleSheet(error_style)
        self.error.setOpenExternalLinks(True)
        self.error.setWordWrap(True)
        self.log_container.layout().addWidget(self.error)
        self.container.layout().addWidget(self.log_container)
        self.log_container.hide()
        
        #####################
        # DIAGNOSIS RESULTS #
        #####################
        self.diag_container = QWidget()
        self.diag_container.setLayout(QVBoxLayout())
        self.diag_container.layout().addWidget(QLabel('<hr style="border:5px double #487;">'))
        diag_header = QLabel("Diagnosis Results")
        diag_header.setFont(header_font)
        diag_header.setStyleSheet(diag_header_style)
        self.diag_container.layout().addWidget(diag_header, alignment=Qt.AlignCenter)
        
        self.diag_res = QLabel()
        self.chd_prob = QLabel()
        self.norm_prob = QLabel()
        
        self.diag_container.layout().addWidget(self.diag_res)
        self.diag_container.layout().addWidget(self.chd_prob)
        self.diag_container.layout().addWidget(self.norm_prob)
        
        self.container.layout().addWidget(self.diag_container)
        self.diag_container.hide()
        
        self.container.layout().addStretch(1)
        ######################
        # PROCESS PARAMETERS #
        ######################
        self.workdir = os.path.join(CACHE_DIR, "Napari")
        download_clf_models()
        self.outdir.setText(outdir)
        
        self.model = load_MouseCHD_model(conf_path=os.path.join(CLF_DIR, "configs.json"),
                                         weights_path=os.path.join(CLF_DIR, "best_model.hdf5"))
        
        self.logdir = self.outdir.text()
        if self.logdir != "":
            self.logdir = os.path.join(self.logdir, "LOGS")
            
        self.run_worker = None
        self.log_worker = None
        
        ########
        # LOAD #
        ########
        self._update_combo_boxes()
        
        ################
        # VIEWER SETUP #
        ################
        self.viewer.theme = "dark"
        self.viewer.dims.ndisplay = 3
        self.viewer.camera.angles = (0,45,0)
        self.viewer.scale_bar.visible = True
        self.viewer.scale_bar.unit = "mm"
    
    ################
    # WIDGET UTILS #
    ################
    def create_RadioButtons(self, 
                            label, 
                            choices,
                            default_idx=None):
        w_container = QWidget()
        w_container.setLayout(QHBoxLayout())
        w_label = QLabel(label)
        w_label.setFont(parameter_font)
        w_container.layout().addWidget(w_label, alignment=Qt.AlignLeft)
        
        choice_container = QWidget()
        choice_container.setLayout(QHBoxLayout())
        buttons = [QRadioButton(choice) for choice in choices]
        for btn in buttons:
            btn.setFont(parameter_font)
            btn.setStyleSheet(unset_box_style)
            choice_container.layout().addWidget(btn)
        choice_container.setStyleSheet(box_style)
        
        if default_idx is not None:
            buttons[default_idx].setChecked(True)
            buttons[default_idx].setStyleSheet(checked_style)
        w_container.layout().addWidget(choice_container)
        
        return w_container, buttons
    
    
    def create_help_text(self, label):
        instruction = QLabel(label)
        instruction.setFont(help_font)
        instruction.setStyleSheet(help_style)
        instruction.setOpenExternalLinks(True)
        instruction.setWordWrap(True)
        
        return instruction
    
    
    def create_folder_browser(self, label, att_name, header):
        dir_container = QWidget()
        dir_container.setLayout(QHBoxLayout())
        dir_label = QLabel(label)
        dir_label.setFont(parameter_font)
        dir_container.layout().addWidget(dir_label)
        dir_container.layout().addWidget(getattr(self, att_name))
        dir_button = QPushButton("Browse")
        dir_btn = QPushButton("Browse")
        dir_btn.setFont(parameter_font)
        dir_btn.clicked.connect(lambda _,
                                att_name=att_name,
                                header=header: self._on_dir_btn_clicked(att_name, header))
        dir_container.layout().addWidget(dir_btn)
        
        return dir_container
    
    def create_QLineEdit(self, att_name, label, placeholder=None, default_txt=None):
        w_container = QWidget()
        w_container.setLayout(QHBoxLayout())
        label = QLabel(label)
        label.setFont(parameter_font)
        getattr(self, att_name).setFont(parameter_font)
        if placeholder is not None:
            getattr(self, att_name).setPlaceholderText(placeholder)
        if default_txt is not None:
            getattr(self, att_name).setText(default_txt)
        w_container.layout().addWidget(label)
        w_container.layout().addWidget(getattr(self, att_name))
        
        return w_container
    
    
    def create_checkbox(self, box_name, txt_name, default_txt):
        container = QWidget()
        container.setLayout(QHBoxLayout())
        getattr(self, box_name).setFont(parameter_font)
        container.layout().addWidget(getattr(self, box_name))
        getattr(self, txt_name).setText(default_txt)
        getattr(self, txt_name).setFont(parameter_font)
        container.layout().addWidget(getattr(self, txt_name))
        
        return container    
        
    
    
    ################
    # CHANGE UTILS #
    ################
    def _on_dir_btn_clicked(self, att_name, header):
        dir_name = QFileDialog.getExistingDirectory(self, header)
        if dir_name:
            path = pathlib.Path(dir_name)
            getattr(self, att_name).setText(str(path))
    
    
    def _on_outdir_changed(self):
        self.logdir = self.outdir.text()
        if self.logdir != "":
            self.logdir = os.path.join(self.logdir, "LOGS")
        
        if os.path.isdir(self.logdir):
            self.run_tsb_btn.show()
        else:
            self.run_tsb_btn.hide()
            
    
    def _on_resrc_changed(self, btn):
        if btn.isChecked():
            self.resrc = btn.text()
            btn.setStyleSheet(checked_style)
        else:
            btn.setStyleSheet(unchecked_style)
            
        if (btn.text() == "server") and btn.isChecked():
            if self.shared_folder.text() != "":
                self.outdir.setText(os.path.join(self.shared_folder.text(), "Retrain"))
            self.server_container.show()
            self.retrain_instruct.show()
            # self.custom_instruct.show()
            self.pp_resrc_container.show()
        else:
            self.outdir.setText(outdir)
            self.server_container.hide()
            self.retrain_instruct.hide()
            # self.custom_instruct.hide()
            self.pp_resrc_container.hide()
            
    
    def _on_task_changed(self, btn):
        if btn.isChecked():
            self.task = btn.text()
            self.run_btn.setText(self.task.capitalize())
            btn.setStyleSheet(checked_style)
            if btn.text() == "diagnose":
                self.model_container.show()
                self.retrain_container.hide()
            elif btn.text() == "retrain":
                self.model_container.hide()
                self.retrain_container.show()
            else:
                self.model_container.hide()
                self.retrain_container.hide() 
        else:
            btn.setStyleSheet(unchecked_style) 
        if os.path.isdir(self.logdir):
            self.run_tsb_btn.show()
        else:
            self.run_tsb_btn.hide()
            
                   
    def _on_model_changed(self, btn):
        if btn.isChecked():
            self.model_name = btn.text()
            btn.setStyleSheet(checked_style)
            if (btn.text() == "retrained") and (self.task == "diagnose"):
                self.custom_model_container.show()
            else:
                self.custom_model_container.hide()
                self.model_path.setText("")
        else:
            btn.setStyleSheet(unset_box_style)
    
    
    def _on_preprocess_choice_change(self, btn):
        if btn.isChecked():
            self.pp_resrc = btn.text()
            btn.setStyleSheet(checked_style)
        else:
            btn.setStyleSheet(unset_box_style)
           
    
    def _on_model_path_changed(self):
        if self.model_path.text() == "":
            conf_path = os.path.join(CLF_DIR, "configs.json")
            weights_path = os.path.join(CLF_DIR, "best_model.hdf5")
        else:
            conf_path = os.path.join(self.model_path.text(), "configs.json")
            weights_path = os.path.join(self.model_path.text(), "best_model.hdf5")
        
        self.model = load_MouseCHD_model(conf_path=conf_path,
                                         weights_path=weights_path) 
    
    
    def _unset_servername_warning(self):
        self.servername.setStyleSheet(unwarning_style)
        
    
    def _on_slurm_changed(self):
        if self.slurm.isChecked():
            self.slurm_cmd.show()
        else:
            self.slurm_cmd.hide()
            

    def _on_module_changed(self):
        if self.module.isChecked():
            self.module_ls.show()
        else:
            self.module_ls.hide()
            
            
    def _on_export_changed(self):
        if self.export.isChecked():
            self.export_cmd.show()
        else:
            self.export_cmd.hide()
    
    
    def _unset_shared_folder_warning(self):
        self.outdir.setText(os.path.join(self.shared_folder.text(), "Retrain"))
        self.shared_folder.setStyleSheet(unwarning_style)
        
        if is_relative_to(self.shared_folder.text(), self.model_path.text()):
            self.model_path.setStyleSheet(unwarning_style)
        
    
    def _unset_input_warning(self):
        self._image_layers.setStyleSheet(unwarning_style)
        
    
    def _unset_model_path(self):
        self.model_path.setStyleSheet(unwarning_style)
        
        if is_relative_to(self.shared_folder.text(), self.model_path.text()):
            self.shared_folder.setStyleSheet(unwarning_style)
            
    
    def _unset_data_dir_warning(self):
        folders = [x for x in os.listdir(self.data_dir.text()) if not x.startswith(".")]
        if ("CHD" in folders) and ("Normal" in folders):
            self.data_dir.setStyleSheet(unwarning_style)
        else:
            self.data_dir.setStyleSheet(warning_style)
            show_info("Data directory must contain 2 folders: 'CHD' and 'Normal'")
    
    
    def _update_combo_boxes(self):
        for layer_name in [self._image_layers.itemText(i) for i in range(self._image_layers.count())]:
            layer_name_index = self._image_layers.findText(layer_name)
            self._image_layers.removeItem(layer_name_index)
            
        for layer in [l for l in self.viewer.layers if isinstance(l, napari.layers.Image)]:
            is_image = (not layer.name.startswith("gradcam-")) and (not layer.name.startswith("mask-"))
            if layer.name not in [self._image_layers.itemText(i) for i in range(self._image_layers.count())] and is_image:
                self._image_layers.addItem(layer.name)
                
        
    
            
    #############
    # RUN UTILS #
    #############        
    def update_layers(self, layer):
        
        if "error" in layer.keys():
            self.error.setText(layer["log"])
            self.stop_task()
            
        else: 
            all_layer_names = [x.name for x in self.viewer.layers]
            self.run_log.setText(self.run_log.text() + "\n" + layer["log"])
            self.log_container.show()
            
            if "metadata" in layer.keys():
                if layer["metadata"]["name"] not in all_layer_names:
                    self.viewer.add_image(layer["data"], **layer["metadata"])
            
            if "res" in layer.keys():
                preds = layer["res"]
                categories_map = {0: "Normal", 1: "CHD"}
                class_idx = np.argmax(preds)
                show_info("Prediction: {}({})".format(categories_map[class_idx], preds[class_idx]))
                
                pred_class = categories_map[class_idx]
                prob = preds[class_idx]
                max_length = 100
                if pred_class == "CHD":
                    prob = prob
                else:
                    prob = 1-prob
                    
                chd_length = int(max_length*prob)
                norm_length = max_length - chd_length
                        
                textstyle = "color:white;font-size:15px"
                predstyle = "background-color:{};color:white;font-size:15px".format(COLORS[pred_class])
                heartname = re.sub(r"^gradcam-", "", layer["metadata"]["name"])
                self.diag_res.setText(f'<p style="{textstyle}"><mark style="{predstyle}"> {heartname}:</mark> <mark style="{predstyle}"><b>{pred_class}</b></mark></p>')
                self.chd_prob.setText('<p> <mark {}>Normal</mark><mark {}>CHD ({:.3f}) |</mark><mark {}>{}</mark><mark {}>{}</mark></p>'.format(
                    hidestyle,
                    'style="color:{};font-size:15px"'.format(COLORS["CHD"]),
                    prob,
                    'style="background-color:{};color:{};font-size:10px"'.format(COLORS["CHD"], COLORS["CHD"]),
                    '|'*chd_length,
                    comstyle,
                    '|'*norm_length))
                self.norm_prob.setText('<p> <mark {}>CHD</mark><mark {}>Normal ({:.3f}) |</mark><mark {}>{}</mark><mark {}>{}</mark></p>'.format(
                    hidestyle,
                    'style="color:{};font-size:15px"'.format(COLORS["Normal"]),
                    1-prob,
                    'style="background-color:{};color:{};font-size:10px"'.format(COLORS["Normal"], COLORS["Normal"]),
                    '|'*norm_length,
                    comstyle,
                    '|'*chd_length))
                self.diag_container.show()
                
            if layer["stop_worker"]:
                self.stop_task()
            
            if layer["tsb"]:
                self.run_tsb_btn.show()
            
        self.viewer.camera.angles = (0,45,0)
    
    
    def update_log(self, line):
        self.run_log.setText(self.run_log.text() + line)
        
            
    def run_task(self):
        # Check executable
        self.log_container.hide()
        self.run_log.setText("============// RUN LOG //============")
        self.error.setText("")
        self.diag_container.hide()
        
        is_executable = True
        
        if self.resrc == "local":
            if not torch.cuda.is_available():
                show_info("Local machine does not have GPU, running segmentation on CPU may take time")
                # is_executable = False
                # show_info("Local machine does not have GPU, please use server machine or install corresponding CUDA Toolkit.")
        if self.resrc == "server":
            if  self.servername.text() == "":
                is_executable = False
                self.servername.setStyleSheet(warning_style)
                show_info("Please indicate a server name to run!")
            if self.shared_folder.text() == "":
                is_executable = False
                self.shared_folder.setStyleSheet(warning_style)
                show_info("Please choose a shared folder!")
                
        if self.task in ["segment", "diagnose"]:
            if self._image_layers.currentText() == "":
                is_executable = False
                show_info("Input image is required!")
                self._image_layers.setStyleSheet(warning_style)
                
        if self.task in ["diagnose", "retrain"]:
            if self.model_name == "retrained":
                if self.model_path.text() == "":
                    is_executable = False
                    self.model_path.setStyleSheet(warning_style)
                    show_info("Custom model path is required!")
        
                elif self.resrc == "server":
                    # check if custom model on shared folder
                    if not is_relative_to(self.shared_folder.text(), self.model_path.text()):
                        is_executable = False
                        show_info("Custom model must be located on shared folder!")
                        self.shared_folder.setStyleSheet(warning_style)
                        self.model_path.setStyleSheet(warning_style)
        
        if self.task == "retrain":
            if self.data_dir.text() == "":
                is_executable = False
                self.data_dir.setStyleSheet(warning_style)
                show_info("Data directory is required!")
                
            folders = [x for x in os.listdir(self.data_dir.text()) if not x.startswith(".")]
            if ("CHD" not in folders) | ("Normal" not in folders):
                is_executable = False
                
        # Parameters
        if self.resrc == "local":
            self.workdir = os.path.join(CACHE_DIR, "Napari")
        else:
            self.workdir = os.path.join(self.shared_folder.text(), ".MouseCHD")
        
        if is_executable:
            image = None
            for layer in self.viewer.layers:
                if layer.name == self._image_layers.currentText():
                    image = layer        
            self.run_btn.hide()
            self.stop_btn.show()
            self.cache_btn.hide()
            self.stop_btn.setText("Stop: {}".format(self.task.capitalize()))
            self.run_worker = run_task(task=self.task,
                                       resrc=self.resrc,
                                       workdir=self.workdir,
                                       heart_name=self._image_layers.currentText(),
                                       servername=self.servername.text(),
                                       shared_folder=self.shared_folder.text(),
                                       lib_path=self.lib_path.text(),
                                       slurm=self.slurm.isChecked(),
                                       slurm_cmd=self.slurm_cmd.text(),
                                       module=self.module.isChecked(),
                                       module_ls=self.module_ls.text(),
                                       export=self.export.isChecked(),
                                       flags=self.export_cmd.text(),
                                       image=image,
                                       model=self.model,
                                       pp_resrc=self.pp_resrc,
                                       chd_dir=os.path.join(self.data_dir.text(), "CHD"),
                                       norm_dir=os.path.join(self.data_dir.text(), "Normal"),
                                       outdir=self.outdir.text(),
                                       exp=self.exp.text(),
                                       epochs=int(self.epochs.text()))
            self.run_worker.yielded.connect(self.update_layers)
            self.run_worker.start()
            
            if self.task == "retrain":
                self.log_worker = read_log(os.path.join(self.workdir,"retrain", "retrain.log"))
                self.log_worker.yielded.connect(self.update_log)
                self.log_worker.start()
                
            self.busy_container.show()
        
        
    def stop_task(self):
        
        self.run_worker.quit()
        if self.log_worker is not None:
            self.log_worker.quit()
            
        if self.resrc == "server":
            server_home = subprocess.getoutput(f'ssh {self.servername.text()} pwd')
            out = subprocess.getoutput(f'ssh {self.servername.text()} "ps aux | grep {server_home}/{self.lib_path.text()}"')
            print(out)
            pid = out.split()[1]
            print(out.split())
            print(pid)
            print(subprocess.getoutput(f'ssh {self.servername.text()} "kill -9 {pid}"'))
        self.stop_btn.hide()
        self.run_btn.show()
        self.log_container.show()
        self.busy_container.hide()
        self.cache_btn.show()
        
        
    def run_tsb(self):
        from tensorboard import program
        from subprocess import check_output
        
        self.run_tsb_btn.hide()
        tsb = program.TensorBoard()
        tsb.configure(argv=[None, '--logdir', self.logdir])
        url = tsb.launch()
        self.tsb_msg.setText(f"Tensorflow listening on <a href=\"{url}\"> <font color=green> {url}</font> </a>")
        self.tsb_msg.show()
     
        
    
    def delete_cache(self):
        import shutil
        
        if self.resrc == "server":
            self.workdir = os.path.join(self.shared_folder.text(), ".MouseCHD")
            
        self.log_container.hide()
        self.cache_btn.setEnabled(False)
        msg = "All of the segmentation and processed samples will be deleted. Do you want to continue?"
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(msg)
        msgBox.setWindowTitle("Cache Deletion Donfirmation")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        
        res = msgBox.exec()
        
        if res == QMessageBox.Yes:
            self.run_log.setText("Cache in {} deleted!".format(self.workdir))
            self.log_container.show()
            
            try:
                shutil.rmtree(os.path.join(self.workdir, "HeartSeg"))
            except FileNotFoundError:
                pass
            
            try:
                shutil.rmtree(os.path.join(self.workdir, "processed"))
            except FileNotFoundError:
                pass
            
            try:
                shutil.rmtree(os.path.join(self.workdir, "retrain"))
            except FileNotFoundError:
                pass
            
        self.cache_btn.setEnabled(True)
   

@thread_worker
def read_log(path):
    while not os.path.isfile(path):
        time.sleep(0.1)
        
    log_file = open(path, "r")
    
    log_file.seek(0,2)
    while True:
        line = log_file.readline()
        if not line:
            continue
        
        condition = (bool(re.search(r"^\d+\.", line.strip("\n"))) |
                      line.strip("\n").startswith("Mouse") |
                      bool(re.search(r"^\d+ hearts", line.strip("\n"))))
        if condition:
            yield line
        
        
@thread_worker
def run_task(task,
             resrc,
             workdir,
             heart_name,
             servername,
             shared_folder,
             lib_path=lib_path,
             slurm=False,
             slurm_cmd=slurm_cmd,
             module=False,
             module_ls=module_ls,
             export=False,
             flags=exports,
             image=None,
             model=None,
             pp_resrc="local",
             chd_dir=None,
             norm_dir=None,
             outdir=None,
             exp=None,
             epochs=20,
             ):
    
    layer = {"stop_worker": False, "tsb": False }
    
    try:
        # Save default vars
        default_vars = {"servername": servername,
                        "shared_folder": shared_folder,
                        "lib_path": lib_path,
                        "slurm_cmd": slurm_cmd,
                        "module_ls": module_ls,
                        "exports": exports,
                        "outdir": outdir}
        
        with open(os.path.join(CACHE_DIR, "Napari", "vars.json"), "w") as f:
            json.dump(default_vars, f, indent=1)
                
        if task in ["segment", "diagnose"]:
            assert image is not None, "Image must be specified"
            scale = image.scale
            show_info("Start heart segmentation!")
            seg_start = time.time()
            heart = segment_heart(resrc=resrc,
                                  workdir=workdir,
                                  heart_name=heart_name,
                                  servername=servername,
                                  shared_folder=shared_folder,
                                  lib_path=lib_path,
                                  slurm=slurm,
                                  slurm_cmd=slurm_cmd)
            max_clump = get_largest_connectivity(heart)
            heart[max_clump==0] = 0
            seg_end = time.time()
            metadata = dict(name='mask-{}'.format(heart_name),
                            colormap=gen_white2red_colormap(),
                            opacity=0.4,
                            translate=(0,0,0),
                            scale=scale,
                            blending='translucent_no_depth',
                            contrast_limits=(0,1))
            
            layer["data"] = heart
            layer["metadata"] = metadata
            layer["log"] = "Heart segmentation finished! Segment time: {}".format(
                time.strftime("%Hh%Mm%Ss", time.gmtime(seg_end - seg_start))
            )
            
            if task == "segment":
                layer["stop_worker"] = True
            
            yield layer
            
        if task == "diagnose":
            image.translate = (0,0,0)
            translate_values = get_translate_values(heart, pad=(5,5,5))
            translate_values = [x*y for x, y in zip(translate_values, scale)]
            
            show_info("Start diagnosis")
            clf_start = time.time()
            pred, gradcam = diagnose_heart(model, im=image.data, heart=heart)
            clf_end = time.time()
            
            layer["log"] = "Diagnosis finished! Diagnosis time: {}".format(
                time.strftime("%Hh%Mm%Ss", time.gmtime(clf_end - clf_start))
            )
            layer["res"] = pred
            layer["data"] = gradcam
            metadata = dict(name="gradcam-{}".format(heart_name),
                            colormap=gen_transturbo_colormap(),
                            opacity=0.5,
                            visible=False,
                            translate=translate_values,
                            scale=scale,
                            blending="translucent_no_depth")
            layer["metadata"] = metadata
            layer["stop_worker"] = True
            
            yield layer
            
        if task == "retrain":
            retrain_dir = os.path.join(workdir, "retrain")
            os.makedirs(retrain_dir, exist_ok=True)
            # Metadata
            chd_ls = ["CHD" + os.sep + x for x in os.listdir(chd_dir) if not x.startswith(".")]
            norm_ls = ["Normal" + os.sep + x for x in os.listdir(norm_dir) if not x.startswith(".")]
            meta_df = pd.DataFrame({
                "heart_name": chd_ls + norm_ls,
                "Stage": [None] * (len(chd_ls) + len(norm_ls)),
                "Normal heart": [0]*len(chd_ls) + [1]*len(norm_ls),
                "CHD": [1]*len(chd_ls) + [0]*len(norm_ls)
            })
            meta_df.to_csv(os.path.join(workdir, "retrain", "metadata.csv"), index=False)
            layer["log"] = "Start preprocessing: {} CHD and {} Normal".format(len(chd_ls), len(norm_ls))
            layer["log"] += "\n=> Process CHD:\n"
            yield layer
            
            set_logger(os.path.join(workdir,"retrain", "retrain.log"))
            
            # Preprocessing CHD
            chd_start = time.time()
            preprocess(indir=chd_dir,
                       outdir=os.path.join(retrain_dir, "processed"),
                       pp_resrc=pp_resrc,
                       servername=servername,
                       shared_folder=shared_folder,
                       lib_path=lib_path,
                       slurm=slurm,
                       slurm_cmd=slurm_cmd)
            chd_end = time.time()
            layer["log"] = "Finished! Processing time: {}\n".format(
                time.strftime("%Hh%Mm%Ss", time.gmtime(chd_end - chd_start))
            )
            
            layer["log"] += "\n=> Process Normal:\n"
            yield layer
            
            # Processing Normal
            norm_start = time.time()
            preprocess(indir=norm_dir,
                       outdir=os.path.join(retrain_dir, "processed"),
                       pp_resrc=pp_resrc,
                       servername=servername,
                       shared_folder=shared_folder,
                       lib_path=lib_path,
                       slurm=slurm,
                       slurm_cmd=slurm_cmd)
            norm_end = time.time()
            layer["log"] = "Finished! Processing time: {}\n".format(
                time.strftime("%Hh%Mm%Ss", time.gmtime(norm_end - norm_start))
            )
            layer["log"] += "\n~~ Segment hearts ~~"
            yield layer
            
            # process metafile
            df = pd.read_csv(os.path.join(retrain_dir, "processed", "processed.csv"))
            df["Stage"] = "E18.5"
            df["Normal heart"] = (df["folder"].str.split(os.sep, expand=True)[0] == "Normal") * 1
            df["CHD"] = (df["folder"].str.split(os.sep, expand=True)[0] == "CHD") * 1
            df[["heart_name", "Stage", "Normal heart", "CHD"]].to_csv(os.path.join(retrain_dir, "processed", "metadata.csv"),
                                                                      index=False)
            
            # Segmentation
            seg_start = time.time()
            segment_hearts(resrc=resrc,
                           workdir=workdir,
                           servername=servername,
                           shared_folder=shared_folder,
                           lib_path=lib_path,
                           slurm=slurm,
                           slurm_cmd=slurm_cmd)
            seg_end = time.time()
            layer["log"] = "Finished! Processing time: {}\n".format(
                time.strftime("%Hh%Mm%Ss", time.gmtime(seg_end - seg_start))
            )
            layer["log"] += "\n~~Resample~~\n"
            yield layer
            
            # Resample
            res_start = time.time()
            resample(workdir=workdir,
                     pp_resrc=pp_resrc,
                     servername=servername,
                     shared_folder=shared_folder,
                     lib_path=lib_path,
                     slurm=slurm,
                     slurm_cmd=slurm_cmd)
            res_end = time.time()
            layer["log"] = "Finished! Processing time: {}\n".format(
                time.strftime("%Hh%Mm%Ss", time.gmtime(res_end - res_start))
            )
            yield layer
            
            # Split data
            os.makedirs(os.path.join(retrain_dir, "label"), exist_ok=True)
            res_df = pd.read_csv(os.path.join(retrain_dir, "resampled", "resampled.csv"))
            res_df = res_df[res_df["resampled_size"] != "Error"]
            df = df[df["heart_name"].isin(res_df["heart_name"].tolist())]
            df.reset_index(drop=True, inplace=True)
            df["label"] = (df["CHD"] == 1)*1
            
            layer["log"] = "~~Split data~~\n"
            X_train, X_val, _, _ = train_test_split(df["heart_name"].tolist(),
                                                    df["label"].tolist(),
                                                    test_size=0.2,
                                                    random_state=42)
            train_df = df[df["heart_name"].isin(X_train)][["heart_name", "label"]]
            val_df = df[df["heart_name"].isin(X_val)][["heart_name", "label"]]
            train_df_x5 = x5_df(train_df)
            val_df_x5 = x5_df(val_df)
            merged_train_df = merge_base_x5_labels(df=train_df, df_x5=train_df_x5)
            merged_val_df = merge_base_x5_labels(df=val_df, df_x5=val_df_x5)
            merged_train_df.to_csv(os.path.join(retrain_dir, "label", "train.csv"), index=False)
            merged_val_df.to_csv(os.path.join(retrain_dir, "label", "val.csv"), index=False)
            layer["log"] += "Train: {} CHD ({} resampled), {} Normal ({} resampled)\nVal: {} CHD ({} resampled), {} Normal ({} resampled)\n".format(
                train_df["label"].sum(),
                merged_train_df["label"].sum(),
                (train_df["label"]==0).sum(),
                (merged_train_df["label"]==0).sum(),
                val_df["label"].sum(),
                merged_val_df["label"].sum(),
                (val_df["label"]==0).sum(),
                (merged_val_df["label"]==0).sum(),
                )
            layer["log"] += "\n~~ Retrain ~~"
            os.makedirs(os.path.join(outdir, "LOGS"), exist_ok=True)
            layer["tsb"] = True
            yield layer
            
            train_start = time.time()
            status = retrain(resrc=resrc,
                             retrain_dir=retrain_dir,
                             outdir=outdir,
                             exp=exp,
                             epochs=epochs,
                             servername=servername,
                             shared_folder=shared_folder,
                             lib_path=lib_path,
                             slurm=slurm,
                             slurm_cmd=slurm_cmd,
                             module=module,
                             module_ls=module_ls,
                             export=export,
                             exports=exports)    
                
            train_end = time.time()
            if status == "Error":
                layer["error"] = "Error"
                logpath = os.path.join(workdir, "retrain", "retrain.log")
                layer["log"] = f"An error occured. The error traceback is saved in {logpath}. Please report your problem together with traceback file here: {issueLink}"
            else:
                layer["log"] = "Retraining finished! Running time: {}\n".format(
                    time.strftime("%Hh%Mm%Ss", time.gmtime(train_end - train_start))
                )
            layer["stop_worker"] = True
            yield layer
            
    except Exception as error:
        set_logger(os.path.join(workdir, "mousechd-napari.log"))
        layer["error"] = str(error)
        logpath = os.path.join(workdir, "mousechd-napari.log")
        layer["log"] = f"An error occured. The error traceback is saved in {logpath}. Please report your problem together with traceback file here: {issueLink}"
        logging.exception("=> TRACEBACK: ")
        yield layer
        
        
    
        

            
        

    
    
            
        
        
        
        
        
        
        
        
        
        