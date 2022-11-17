# collector_agent
It can only be used with [MyPlatform](https://github.com/leeyoshinari/MyPlatform.git), and can't be used alone.

## Deploy

1. Clone Repository
    ```shell script
    git clone https://github.com/leeyoshinari/collector_agent.git
    ```

2. Modify `config.conf`. Usually don't need to modify, unless you have special requirements.

3. Package. Using `pyinstaller` to package python code. 
- (1) Enter folder, run:<br>
    ```shell script
    pyinstaller -F server.py -p write_database.py -p common.py -p __init__.py --hidden-import write_database --hidden-import common
    ```
- (2) Copy `config.conf` to the `dist` folder, cmd: `cp config.conf dist/`
- (3) Enter `dist` folder, zip files, cmd: `zip collector_agent.zip server config.conf`
- (4) Upload zip file to [MyPlatform](https://github.com/leeyoshinari/MyPlatform.git)
- (5) Deploy collector_agent
   
NOTE: For Linux Server, the executable file packaged on the server of the CentOS system X86 architecture can only run on the server of the CentOS system X86 architecture; servers of other system and architecture need to be repackaged. <br>

