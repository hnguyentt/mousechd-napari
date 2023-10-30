import time
import subprocess
import shutil
from tkinter import Widget
from tkinter.ttk import Style
from magicgui import magicgui
from magicgui.events import Event, Signal
import napari
from napari.qt.threading import thread_worker
from napari.utils.notifications import show_info
from qtpy.QtWidgets import QSizePolicy
import numpy as np
import functools
import os, pathlib, re
from typing import List, Union
from typing import Union
import SimpleITK as sitk
import io

from ._constants import *

def plugin_wrapper():
    logo = (pathlib.Path(__file__).parent.joinpath(os.path.join('assets', 'thumbnail.png')))
    DEBUG=False
    def change_handler(*widgets, init=True, debug=DEBUG):
        def decorator_change_handler(handler):
            @functools.wraps(handler)
            def wrapper(*args):
                source = Signal.sender()
                emitter = Signal.current_emitter()
                if debug:
                    # print(f"{emitter}: {source} = {args!r}")
                    print(f"{str(emitter.name).upper()}: {source.name} = {args!r}")
                return handler(*args)
            for widget in widgets:
                widget.changed.connect(wrapper)
                if init:
                    widget.changed(widget.value)
            return wrapper
        return decorator_change_handler

    def get_data(image):
        image = image.data[0] if image.multiscale else image.data
        # enforce dense numpy array in case we are given a dask array etc
        return np.asarray(image)   
    
    @magicgui (
        label_head=dict(widget_type='Label', 
                        label='<h1>Mouse Congenital Heart Diseases</h1>'
                        + '='*51
                        + f'<br><img src="{logo}" width="400" style="vertical-align:middle"><br>@IMOD, Institut Pasteur<br>'
                        +'-'*25
                        ),
        resrc=dict(widget_type='RadioButtons',
                   label=f'<p style="{normalstyle}">Choose a resource to run on:</p>',
                   choices=DEFAULT_CHOICES['resrc_choices'],
                   orientation='horizontal',
                   value=DEFAULTS['resrc_choice']
                   ),
        cache_dir=dict(widget_type='FileEdit',
                       visible=True,
                       label=f'<p style="{normalstyle}">Shared folder with the server:</p>',
                       mode='d'
                       ),
        server_name=dict(widget_type='LineEdit',
                       visible=True,
                       label=f'<p style="{intextstyle}">Server name:</p>',
                       value=DEFAULTS['server']
                       ),
        image=dict(label=f'<p style="{normalstyle}">Input Image</p>'),
        label_task=dict(widget_type="Label",
                        label="<h2>Tasks</h2>",
                        visible=True),
        task_choice=dict(widget_type='RadioButtons',
                         label=f'<p style={normalstyle}>Choose a task</p>',
                         choices=DEFAULT_CHOICES['task_choices'],
                         orientation='horizontal',
                         value=DEFAULTS['task_choice']
                         ),
        label_custom_model=dict(widget_type="Label", 
                                label="<h2>Custom Diagnosis Model</h2>",
                                visible=False),
        diag_model_choice=dict(widget_type='RadioButtons', 
                               label=f'<p style="{normalstyle}">Choose a model type</p>', 
                               choices=DEFAULT_CHOICES["diag_model_choices"], 
                               orientation='horizontal', 
                               value=DEFAULTS['diag_model_choice'],
                               visible=False),
        custom_model_path=dict(widget_type='FileEdit',
                               visible=False,
                               label=f'<p style="{normalstyle}">Custom model path</p>', 
                               mode='d'),
        label_retrain=dict(widget_type="Label", 
                           label='<h2>Images for retraining</h2>',
                           visible=False),
        note_retrain=dict(widget_type="Label",
                          label=f'<i style={notestyle}>Note: If you choose to run on server, <br>OUTDIR must be placed on the shared folder.</i>',
                          visible=False
                          ),
        chd_dir=dict(widget_type='FileEdit',
                     visible=False,
                     label=f'<p style="{normalstyle}">CHD directory</p>',
                     mode='d'),
        norm_dir=dict(widget_type='FileEdit',
                      visible=False,
                      label=f'<p style="{normalstyle}">Normal directory</p>',
                      mode='d'),
        out_dir=dict(widget_type='FileEdit',
                     visible=False,
                     label=f'<p style="{normalstyle}">OUTDIR</p>',
                     mode='d'),
        epochs=dict(widget_type='LineEdit',
                    visible=False,
                    label=f'<p style="{normalstyle}"># epochs</p>',
                    value=DEFAULTS['epochs']
                    ),
        hl=dict(widget_type='Label',
                label='<br>{}<br>'.format('='*55)
                ),
        label_pred=dict(widget_type="Label", 
                        label=f'<p style="color:blue;background-color:#cfe2f3;text-align:center;font-size:25px">{LABEL_PRED}</p>',
                        visible=False),
        pred=dict(widget_type='Label',
                  label="",
                  visible=False),
        chd_prob=dict(widget_type='Label',
                      visible=False),
        norm_prob=dict(widget_type='Label',
                       visible=False),
        call_button='Run Task'
    )

    def plugin(
        viewer: Union[napari.Viewer, None],
        label_head,
        resrc,
        cache_dir,
        server_name,
        image: napari.layers.Image,
        label_task,
        task_choice,
        label_custom_model,
        diag_model_choice,
        custom_model_path,
        label_retrain,
        note_retrain,
        chd_dir,
        norm_dir,
        out_dir,
        epochs,
        hl,
        label_pred,
        pred,
        chd_prob,
        norm_prob
    ) -> None: #List[napari.types.LayerDataTuple]:
        
        viewer.theme = 'dark'
        
        # Check conditions
        is_executable = True
        if resrc == "server":
            if server_name in ['<insert server name here>', ''] :
                is_executable = False
                show_info("Please indicate a server name!")
        else:
            import torch
            if not torch.cuda.is_available():
                is_executable = False
                show_info("There is no GPU available on your local machine. Please use server instead!")
        
        if (task_choice in ["segment", "diagnose"]) & is_executable:
            try:        
                if image.source.path is None:
                    impath = str(pathlib.Path(__file__).parent.joinpath(os.path.join('data', 'sample.nii.gz')))
                else:
                    impath = image.source.path
            
            except AttributeError:
                is_executable = False
                show_info("Please choose a file to predict!")
        else:
            show_info("NOTE: If you choose run on server, DATA and OUTPUT directory must be placed in the share folder!")
        
        if (task_choice in ['diagnose', 'retrain']) & is_executable:
            if diag_model_choice == "retrained":
                if not (os.path.isfile(os.path.join(custom_model_path, "configs.json")) or os.path.isfile(os.path.join(custom_model_path, 'best_model.hdf5'))):
                    is_executable = False
                    show_info("The custom model path does not contain the model configuration or weights!")
                
                
        
        viewer.dims.ndisplay = 3
        viewer.camera.angles = (0,45,0)
        viewer.scale_bar.visible = True
        viewer.scale_bar.unit = "mm"
        
    # Make prettier
    # for w in [plugin.label_head]:
    #     w.native.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

    # Allow some widgets to skrink because their size depends on user input
    # min_width = 30
    # plugin.image.native.setMinimumWidth(min_width)
    # plugin.diag_model_choice.native.setMinimumWidth(min_width)
    # plugin.custom_model_path.native.setMinimumWidth(min_width)
    
    # Interactive
    @change_handler(plugin.task_choice, init=True)
    def _task_choice_change():
        if plugin.task_choice.value == "segment":
            plugin.label_custom_model.visible = False
            plugin.diag_model_choice.visible = False
            plugin.custom_model_path.visible = False
            plugin.label_retrain.visible = False
            plugin.note_retrain.visible = False
            plugin.chd_dir.visible = False
            plugin.norm_dir.visible = False
            plugin.out_dir.visible = False
            plugin.epochs.visible = False
        elif plugin.task_choice.value == 'diagnose':
            plugin.label_custom_model.visible = True
            plugin.diag_model_choice.visible = True
            if plugin.diag_model_choice.value == "retrained":
                plugin.custom_model_path.visible = True
            plugin.label_retrain.visible = False
            plugin.note_retrain.visible = False
            plugin.chd_dir.visible = False
            plugin.norm_dir.visible = False
            plugin.out_dir.visible = False
            plugin.epochs.visible = False
        else:
            plugin.label_custom_model.visible = True
            plugin.diag_model_choice.visible = True
            if plugin.diag_model_choice.value == "retrained":
                plugin.custom_model_path.visible = True
            plugin.label_retrain.visible = True
            plugin.note_retrain.visible = True
            plugin.chd_dir.visible = True
            plugin.norm_dir.visible = True
            plugin.out_dir.visible = True
            plugin.epochs.visible = True
    
    @change_handler(plugin.resrc, init=True)
    def _resrc_choice_change():
        if plugin.resrc.value == "local":
            plugin.cache_dir.visible = False
            plugin.server_name.visible = False
        else:
            show_info('Please indicate a server name and a shared folder with server!')
            plugin.cache_dir.visible = True
            plugin.server_name.visible = True
    
    @change_handler(plugin.diag_model_choice, init=True)
    def _model_choice_change():
        if plugin.diag_model_choice.value == "default":
            plugin.custom_model_path.visible = False
        else:
            plugin.custom_model_path.visible = True

    return plugin