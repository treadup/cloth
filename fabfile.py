from fabric import task
from fabric import SerialGroup as Group
import time

# The following tasks could be interesting.
# 1. clean
# 2. build
# 3. bootstrap
# 4. deploy

REBOOT_DELAY = 17 # 17 seconds

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

def bootstrap_server(c):
    print("Bootstrapping server")
    # Install Git
    c.run('apt-get --yes install git')

    # Install virtualenv
    c.run('apt-get --yes install virtualenv')

    create_user(c)

def create_application(c):
    pass

@task
def bootstrap(ctx):
    # This will update the server
    # Install the needed packages.
    #    python, virutalenv, git
    # Create the ubuntu user
    # Create the application folder structure
    # Daemonize the application

    validate_has_stage(ctx)

#    for connection in Group(*ctx.config.hosts):
#        upgrade_server(connection)

#    time.sleep(REBOOT_DELAY)

    for connection in Group(*ctx.config.hosts):
        bootstrap_server(connection)

    for connection in Group(*ctx.config.hosts):
        # Here I want to log in as another user.
        create_application(connection)

@task
def deploy(ctx):
    validate_has_stage(ctx)

    ctx.run("echo Deploying {}".format(ctx.config.stage))
