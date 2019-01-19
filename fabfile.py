from fabric import task

@task
def test(ctx):
    ctx.config.stage = 'test'

@task
def prod(ctx):
    ctx.config.stage = 'prod'

@task
def clean(ctx):
    ctx.run('echo Cleaning project')
    with ctx.cd("build/"):
        ctx.run('rm -rf *')

@task
def build(ctx):
    ctx.run('echo Building')

@task
def deploy(ctx):
    if not ctx.config.stage:
        print("Stage not specified")
        return

    ctx.run("echo Deploying {}".format(ctx.config.stage))
