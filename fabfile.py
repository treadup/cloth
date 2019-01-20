from fabric import task
from fabric import SerialGroup as Group
import time

# The following tasks could be interesting.
# 1. clean
# 2. build
# 3. bootstrap
# 4. deploy

REBOOT_DELAY = 60 # 60 seconds

@task
def test(ctx):
    ctx.config.stage = 'test'
    ctx.config.hosts = ['cloth-web-test']

@task
def prod(ctx):
    ctx.config.stage = 'prod'
    ctx.config.hosts = ['cloth-web-prod']

def validate_has_stage(ctx):
    if not 'stage' in ctx.config or not ctx.config.stage:
        print("Stage not specified")
        exit(1)

@task
def clean(ctx):
    ctx.run('echo Cleaning project')
    with ctx.cd("build/"):
        ctx.run('rm -rf *')

@task
def build(ctx):
    validate_has_stage(ctx)
    ctx.run('echo Building')

def create_user(c):
    print("Creating user")

    # Add the group ubuntu if the group does not already exist
    c.run('getent group ubuntu &>/dev/null || groupadd -r ubuntu')

    # Add the user ubuntu if the user does not aleady exist
    c.run('id -u ubuntu &>/dev/null || useradd --no-log-init -r -g ubuntu ubuntu')

    # Create home folder
    if c.run('test -d /home/ubuntu', warn=True).failed:
        c.run('mkdir -p /home/ubuntu && chown ubuntu:ubuntu /home/ubuntu')

    # Need to copy over some kind of SSH key so that I can log in as ubuntu
    c.run('mkdir -p /home/ubuntu/.ssh/')
    c.run('cp /root/.ssh/authorized_keys /home/ubuntu/.ssh/authorized_keys && chown ubuntu:ubuntu /home/ubuntu/.ssh/authorized_keys')

    # Allow systemd user services when the user is not logged in
    c.run('loginctl enable-linger ubuntu')

def create_cloth_user_service(c):
    c.run('mkdir -p /home/ubuntu/.config/systemd/user/')
    c.run('chown -R ubuntu:ubuntu /home/ubuntu/.config/')
    c.put('cloth-user.service', '/home/ubuntu/.config/systemd/user/cloth.service')
    c.run('chown ubuntu:ubuntu /home/ubuntu/.config/systemd/user/cloth.service')

def upgrade_server(c):
    print("Upgrading server")
    # Run all ubuntu commands non interactively
    c.run('export DEBIAN_FRONTEND=noninteractive')

    # Set the timezone
    c.run('export TZ=Europe/Stockholm')
    c.run('ln -snf /usr/share/zoneinfo/$TX /etc/localtime && echo $TZ > /etc/timezone')

    # Upgrade Ubuntu
    c.run('apt-get update && apt-get --yes upgrade')

    # Reboot
    c.run('reboot')

def install_packages(c):
    # Install Git
    c.run('apt-get --yes install git')

    # Install virtualenv
    c.run('apt-get --yes install virtualenv')

def bootstrap_webserver(c):
    print("Bootstrapping server")

    install_packages(c)

    create_user(c)

    create_cloth_user_service(c)

@task
def bootstrap(ctx):
    validate_has_stage(ctx)

    for connection in Group(*ctx.config.hosts):
        upgrade_server(connection)

    time.sleep(REBOOT_DELAY)

    for connection in Group(*ctx.config.hosts):
        bootstrap_webserver(connection)

def create_application(c):

    # Copy program
    c.put('cloth.py', 'cloth.py')
    c.put('requirements.txt', 'requirements.txt')

    # Create virtual environment
    c.run('rm -rf env')
    c.run('virtualenv -p python3 env')
    c.run('./env/bin/pip3 install -r requirements.txt')

    # Enable service
    c.run('systemctl --user enable cloth')

    # Start service
    c.run('systemctl --user start cloth')


# Connecting to the following url works
# http://45.77.138.227:5000/
# when we are running flask using the following command.
# FLASK_APP=cloth.py ./env/bin/flask run --host=0.0.0.0

# Connecting to the following url works
# http://45.77.138.227:8000/
# when we are running Gunicorn using the following command.
# ./env/bin/gunicorn cloth:app --bind=0.0.0.0:8000

@task
def deploy(ctx):
    validate_has_stage(ctx)

    print("Deploying {}".format(ctx.config.stage))
    for connection in Group(*ctx.config.hosts, user='ubuntu'):
        create_application(connection)
