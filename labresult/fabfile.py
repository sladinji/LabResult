from fabric.api import task, run, env, cd

env.hosts=["labresult.fr"]

@task
def update_website():
    with cd("docker_scripts"):
        run("./update_demo")

