# collector_agent

## Package
Using `pyinstaller` to package python code. After packaging, it can be quickly deployed on other Servers without installing python3.7+ and third-party packages.<br>
Before packaging, you must ensure that the python code can run normally.<br>
- (1) Enter folder, run:<br>
    ```shell
    pyinstaller -F server.py -p write_database.py -p common.py -p __init__.py --hidden-import write_database --hidden-import common
    ```
- (2) Copy `config.conf` to the `dist` folder, cmd: `cp config.conf dist/`
- (3) Enter `dist` folder, zip files, cmd: `zip collector_agent.zip server config.conf`
- (4) Upload zip file to [MyPlatform](https://github.com/leeyoshinari/MyPlatform.git)
- (5) Deploy collector_agent
   
   NOTE: Since it runs on the server to be monitored, the executable file packaged on the server of the CentOS system X86 architecture can only run on the server of the CentOS system X86 architecture; servers of other system and architecture need to be repackaged. <br>

