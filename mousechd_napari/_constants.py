import pathlib
import os

HOME = os.path.expanduser('~')
#TODO: Download nnUnet model to $HOME/.mouseCHD/nnUNet/3d_fullres/Task113_MouseHeartImagine/nnUNetTrainerV2__nnUNetPlansv2.1/fold0
COLORS = {"CHD": "red", "Normal": "green"}
normalstyle = "font-size:18px;"
intextstyle = "font-size:18px;background-color:#CD5C5C"
notestyle = "font-size:12px;background-color:#CD5C5C"
LABEL_PRED = "-"* len(" Diagnosis Results ") + "<br>|| Diagnosis Results ||<br>" + "-"* len(" Diagnosis Results ")

DEFAULTS = dict (
    task_choice = 'diagnose',
    resrc_choice = 'local',
    server = '<INSERT SERVER NAME HERE>',
    diag_model_choice = "default",
    diag_model_path = pathlib.Path(__file__).parent.joinpath(os.path.join("assets", "diagnosis")),
    epochs = 10,
)

DEFAULT_CHOICES = dict (
    diag_model_choices = ["default", "retrained"],
    task_choices = ['segment', 'diagnose', 'retrain'],
    resrc_choices = ['local', 'server']
)