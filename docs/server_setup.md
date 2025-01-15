# Setup server

The instructions provided in this tutorial are aimed at establishing a standard SSH connection to a server within the user's network. This setup assumes that you have access to a remote computing server with SSH enabled, allowing you to securely connect and run the necessary software. 

## On your local machine

### Install ssh
SSH is required to access the remote server resource. If you haven't installed `ssh`, follow one of these instructions to install `ssh`:

<details>
<summary><b>Linux</b></summary>

* Open the Terminal
* Type command: `sudo apt-get install openssh-server`
* Enable the ssh service: `sudo systemctl enable ssh`
* Start the ssh service: `sudo systemctl start ssh`

</details>
  
<details>
<summary><b>MacOS</b></summary>
Download and install ***macFUSE*** here: https://osxfuse.github.io/

</details>

<details>
<summary><b>Windows</b></summary>

1. Open **Settings**, select **Apps**, then select **Optional Features**.
2.  Scan the list to see if the OpenSSH is already installed. If not, at the top of the page, select **Add a feature**, then:
    * Find **OpenSSH Client**, then select **Install**
    * Find **OpenSSH Server**, then select **Install**

3. Once setup completes, return to **Apps** and **Optional Features** and confirm OpenSSH is listed.
4.  Open the **Services** desktop app. (Select **Start**, type *services.msc* in the search box, and then select the **Service** app or press <kbd>ENTER</kbd>).
5.  In the details pane, double-click **OpenSSH SSH Server**.
6.  On the **General** tab, from the **Startup type** drop-down menu, select **Automatic**.
7.  To start the service, select **Start**.

> Adapted from: https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse?tabs=gui

</details>

## Setup ssh keygen
This step create the key for server access that does require password.

<details>
<summary><b>Linux and MacOS</b></summary>

1. Open Terminal
2. `mkdir -p /.ssh && chmod 700 ~/.ssh && cd ~/.ssh`
3. Paste the text below, replacing the email used in the example with your email: `ssh-keygen -t rsa -b 4096 -C "your_email@example.com"`. Click <kbd>ENTER</kbd> until finishing.
4. Check if successful by `ls ~\.ssh`. The results should contain these two files: `id_rsa` and `id_rsa.pub`.

</details>

<details>
<summary><b>Windows</b></summary>

1. Open Terminal as Administrator following this instruction: https://learn.microsoft.com/en-us/windows/terminal/faq 
2. `mkdir -p /.ssh && chmod 700 ~/.ssh && cd ~/.ssh`
3. Paste the text below, replacing the email used in the example with your email: `ssh-keygen -t rsa -b 4096 -C "your_email@example.com"`. Click <kbd>ENTER</kbd> until finishing.
4. Check if successful by `ls ~/.ssh`. The results should contain these two files: `id_rsa` and `id_rsa.pub`.

</details>

### Setup ssh configuration
This step allows you to alias the server address for easy access.

1. Open Terminal (On Windows, follow this instruction to run the Terminal as Administrator: https://learn.microsoft.com/en-us/windows/terminal/faq)
2. `cd ~/.ssh`
3. `touch config & chmod 600 ~/.ssh/config`
4. `nano config` then enter these contents in the file config:
    ```
    GSSAPIAuthentication no
    ServerAliveInterval 120
    TCPKeepAlive no

    Host <hostname>
        HostName <host_address>
        User <your_username>
        ForwardAgent yes
        ProxyCommand none
        IdentityFile ~/.ssh/id_rsa
    ```

    Replace the contend inside `<>` with your own information.

5. <kbd>Ctrl</kbd> + <kbd>x</kbd> &rarr; <kbd>y</kbd>

## On server

### Add local ssh keygen to authorized list

1. Copy the content in `~/.ssh/id_rsa.pub`
2. SSH to your server: `ssh <hostname>`, enter the required password.
3. `nano ~/.ssh/authorized_keys`  &rarr; paste the content of `id_rsa.pub` as new line
4. <kbd>Ctrl</kbd> + <kbd>x</kbd> &rarr; <kbd>y</kbd>

After this step, you can access to the server without entering password.

### Install the `mousechd` package

1. SSH to your server: `ssh <hostname>`, enter the password (if required).
2. Download the MouseCHD Apptainer: `wget https://zenodo.org/records/13928753/files/mousechd.sif`

### Locate the shared folder
On the remote server, locate the shared folder at `$HOME/DATA`.

* If the shared folder is remote, mount your shared folder at `$HOME/DATA`
* If your shared folder is on the server, use `mkdir <shared_folder_name> && ln -sf <path/to/shared/folder>/* ~/DATA/<shared_folder_name>`

Congratulations! You've successfully completed the setup to run the plugin on the remote server. Here are some key parameters that require your attention during plugin input:

<table>
    <thead>
        <!-- <tr>
            <th></th>
            <th></th>
        </tr> -->
    </thead>
    <tbody>
        <tr>
            <td rowspan=5><img src=../assets/server_params.png width="1000"></td>
            <td><b>Servername:</b> it is the hostname you placed in your config file.</td>
        </tr>
        <tr>
            <td><b>Apptainer execution command:</b> the command to run apptainer. Default: <i>apptainer exec -B /pasteur --nv mousechd.sif mousechd</i>. <font color=red><i>-B</i></font> to mount volume if necessary, <font color=red><i>--nv</i></font> to run with GPU.</td>
        </tr>
        <tr>
            <td><b>Slurm:</b> your server uses <a href=https://slurm.schedmd.com/documentation.html> <font color=green>Slurm Workload Manager</font> </a>" to request the resource or not. If yes, what is the command? Default: <i>srun -J 'mousechd' -p gpu --qos=gpu --gres=gpu:1</i></td>
        </tr>
        <tr>
            <td><b>Load modules:</b> Do you need to load some modules to run the program? If yes, specify. Default: <i>module load apptainer</i></td>
        </tr>
    </tbody>
</table>

*These paremeters will automatically saved for future use*
