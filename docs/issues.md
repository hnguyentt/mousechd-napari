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

