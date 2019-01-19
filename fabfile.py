from fabric import task
from fabric import SerialGroup as Group

# The following tasks could be interesting.
# 1. clean
# 2. build
# 3. bootstrap
# 4. deploy

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

def bootstrap_server(c):
    # Run all ubuntu commands non interactively
    c.run('export DEBIAN_FRONTEND=noninteractive')

    # Set the timezone
    c.run('export TZ=Europe/Stockholm')
    c.run('ln -snf /usr/share/zoneinfo/$TX /etc/localtime && echo $TZ > /etc/timezone')

    # Upgrade Ubuntu
    c.run('apt-get update && apt-get --yes upgrade')

    # Install Gitconfig
    c.run('apt-get --yes install git')

    # Install virtualenv
    c.run('apt-get --yes install virtualenv')

    # Reboot
    c.run('reboot')

@task
def bootstrap(ctx):
    # This will update the server
    # Install the needed packages.
    #    python, virutalenv, git
    # Create the ubuntu user
    # Create the application folder structure
    # Daemonize the application

    validate_has_stage(ctx)

    for connection in Group(*ctx.config.hosts):
        bootstrap_server(connection)

@task
def deploy(ctx):
    validate_has_stage(ctx)

    ctx.run("echo Deploying {}".format(ctx.config.stage))
