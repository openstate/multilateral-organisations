from fabric.api import run, env, cd, sudo

env.use_ssh_config = True
env.hosts = ["Oxygen"]


def deploy():
    with cd('/home/projects/multilaterale-organisaties'):
        run('git pull git@github.com:openstate/multilaterale-organisaties.git')
        sudo('docker exec -it mlo_nodejs_1 gulp')
        run('touch uwsgi-touch-reload')
        #sudo('docker exec mlo_nginx_1 nginx -s reload')
