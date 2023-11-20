# Common issues

## Segmentation failed on local machine

If you encounter a segmentation failure when running the plugin on your local machine, it could be due to insufficient GPU memory. We recommend having a GPU with a memory capacity of 10GB or above for optimal performance.

## Crash when run on server

Here are some possible causes:
1. Did you locate the shared folder on the server at `$HOME/DATA`? See: [Locate the shared folder](https://github.com/hnguyentt/mousechd-napari/blob/master/docs/server_setup.md#locate-the-shared-folder)
2. Is the library path correct? See:[server parameters](https://github.com/hnguyentt/mousechd-napari/blob/master/docs/server_setup.md#on-server)
3. Does the server use Slurm to manage the resource request? If yes, is the slurm command correct? See: [server parameters](https://github.com/hnguyentt/mousechd-napari/blob/master/docs/server_setup.md#on-server)
4. Do you need to load certain modules for running?

