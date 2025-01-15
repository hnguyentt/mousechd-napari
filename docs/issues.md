# Common issues

## Segmentation failed on local machine

If you encounter a segmentation failure when running the plugin on your local machine, it could be due to insufficient GPU memory. We recommend having a GPU with a memory capacity of 10GB or above for optimal performance.

## Crash when run on server

Here are some possible causes:
1. Did you locate the shared folder on the server at `$HOME/DATA`? See: [Locate the shared folder](https://github.com/hnguyentt/mousechd-napari/blob/master/docs/server_setup.md#locate-the-shared-folder)
2. Is the library path correct? See:[server parameters](https://github.com/hnguyentt/mousechd-napari/blob/master/docs/server_setup.md#on-server)
3. Does the server use Slurm to manage the resource request? If yes, is the slurm command correct? See: [server parameters](https://github.com/hnguyentt/mousechd-napari/blob/master/docs/server_setup.md#on-server)
4. Do you need to load certain modules for running?

## The task is still running even though I click on `Stop` button

This can be seen when you do the segmentation or retrain on your local machine. It is recommended to restart the application.

## 12243 IOT instruction (core dumped)  napari

Full error:
```
WARNING: Could not load the Qt platform plugin "xcb" in "" even though it was found.
18:39:13 WARNING Could not load the Qt platform plugin "xcb" in "" even though it was found.
WARNING: This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, webgl, xcb.

18:39:13 WARNING This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, webgl, xcb.

[1]    12243 IOT instruction (core dumped)  napari
```

Fix: 
* Ubuntu: `sudo apt-get install libxcb-xinerama0` ([ref](https://github.com/NVlabs/instant-ngp/discussions/300#discussioncomment-3985753))

## Napari plugin in Docker container fail to display 3D

Temporary fix: change to 2D view to run the plugin.

## Napari plugin in Docker container crashes

The docker needs time to setup, please wait untill you see these lines before opening [http://localhost:9876/](http://localhost:9876/) in your browser:

* In case you have GPU:

```
2025-01-15 12:46:35,189  running with pid 9 on Linux Ubuntu 20.04 focal
2025-01-15 12:46:35,192  connected to X11 display :100 with 24 bit colors
2025-01-15 12:46:36.217011: E tensorflow/compiler/xla/stream_executor/cuda/cuda_dnn.cc:9342] Unable to register cuDNN factory: Attempting to register factory for plugin cuDNN when one has already been registered
2025-01-15 12:46:36.217095: E tensorflow/compiler/xla/stream_executor/cuda/cuda_fft.cc:609] Unable to register cuFFT factory: Attempting to register factory for plugin cuFFT when one has already been registered
2025-01-15 12:46:36.217146: E tensorflow/compiler/xla/stream_executor/cuda/cuda_blas.cc:1518] Unable to register cuBLAS factory: Attempting to register factory for plugin cuBLAS when one has already been registered
12:46:38 : WARNING : MainThread : From /opt/conda/lib/python3.9/site-packages/mousechd_napari/_widget.py:128: is_gpu_available (from tensorflow.python.framework.test_util) is deprecated and will be removed in a future version.
Instructions for updating:
Use `tf.config.list_physical_devices('GPU')` instead.
2025-01-15 12:46:39.178862: I tensorflow/core/common_runtime/gpu/gpu_device.cc:1886] Created device /device:GPU:0 with 11601 MB memory:  -> device: 0, name: NVIDIA GeForce RTX 4080, pci bus id: 0000:82:00.0, compute capability: 8.9
WARNING: QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
12:46:39 : WARNING : MainThread : QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
WARNING: QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
12:46:39 : WARNING : MainThread : QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
/root/.MouseCHD/Napari/assets/thumbnail.png
2025-01-15 12:46:40.811886: I tensorflow/core/common_runtime/gpu/gpu_device.cc:1886] Created device /job:localhost/replica:0/task:0/device:GPU:0 with 11601 MB memory:  -> device: 0, name: NVIDIA GeForce RTX 4080, pci bus id: 0000:82:00.0, compute capability: 8.9
```

* In case you don't have GPU:
```
2025-01-15 12:49:50,169  running with pid 9 on Linux Ubuntu 20.04 focal
2025-01-15 12:49:50,171  connected to X11 display :100 with 24 bit colors
2025-01-15 12:49:50.588630: E tensorflow/compiler/xla/stream_executor/cuda/cuda_dnn.cc:9342] Unable to register cuDNN factory: Attempting to register factory for plugin cuDNN when one has already been registered
2025-01-15 12:49:50.588699: E tensorflow/compiler/xla/stream_executor/cuda/cuda_fft.cc:609] Unable to register cuFFT factory: Attempting to register factory for plugin cuFFT when one has already been registered
2025-01-15 12:49:50.588748: E tensorflow/compiler/xla/stream_executor/cuda/cuda_blas.cc:1518] Unable to register cuBLAS factory: Attempting to register factory for plugin cuBLAS when one has already been registered
12:49:53 : WARNING : MainThread : From /opt/conda/lib/python3.9/site-packages/mousechd_napari/_widget.py:128: is_gpu_available (from tensorflow.python.framework.test_util) is deprecated and will be removed in a future version.
Instructions for updating:
Use `tf.config.list_physical_devices('GPU')` instead.
WARNING: QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
12:49:53 : WARNING : MainThread : QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
WARNING: QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
12:49:53 : WARNING : MainThread : QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
/root/.MouseCHD/Napari/assets/thumbnail.png
```

