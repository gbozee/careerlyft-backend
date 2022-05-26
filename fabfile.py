import os
from fabric.api import local, run, cd, env, sudo, settings, lcd
from fabric.decorators import hosts

env.hosts = ["sama@tutor-search.tuteria.com"]
# env.hosts = ["sama@backup.tuteria.com"]

password = os.getenv("PRODUCTION_PASSWORD", "")


# def common_code(code_dir, branch="develop", migrate=False, delete=False):
#     with settings(user="sama", password=password):
#         with cd(code_dir):
#             if not delete:
#                 run("pwd")
#                 run("git pull")
#                 run("git checkout {}".format(branch))
#                 sudo("docker-compose build")
#                 # sudo("docker-compose run cv_profile python manage.py migrate --noinput")
#                 sudo(
#                     "docker-compose  kill authentication payment cvscript cv_profile admin"
#                 )
#                 sudo(
#                     "docker-compose  rm -f authentication payment cvscript cv_profile admin"
#                 )
#                 sudo(
#                     "docker-compose  run admin python manage.py collectstatic --noinput"
#                 )
#                 sudo("docker-compose  run admin python manage.py migrate")
#                 sudo(
#                     "docker-compose  up -d authentication payment cvscript cv_profile admin proxy"
#                 )
#                 sudo("docker-compose run --rm cvscript python manage.py migrate --noinput")
#             if migrate:
#                 sudo(
#                     "docker-compose run --rm authentication python manage.py migrate"
#                 )
#                 sudo(
#                     "docker-compose run --rm cv_profile python manage.py migrate"
#                 )
#                 sudo(
#                     "docker-compose run --rm payment python manage.py migrate")
#                 sudo(
#                     'docker rmi $(docker images --filter "dangling=true" -q --no-trunc)'
#                 )
#             if delete:
#                 sudo('docker system prune -a')
def common_code(code_dir, branch="develop", migrate=False, delete=False):
    with settings(user="sama", password=password):
        with cd(code_dir):
            if not delete:
                run("pwd")
                run("git pull")
                run("git checkout {}".format(branch))
                CONTAINER_CV_PROFILE_NAME='registry.gitlab.com/careerlyft-team/cv-script-microservice/cv_profile'
                CONTAINER_ADMIN_IMAGE='registry.gitlab.com/careerlyft-team/cv-script-microservice/admin-service'
                # run('export CONTAINER_CVSCRIPT_IMAGE=registry.gitlab.com/careerlyft-team/cv-script-microservice/cvscript')
                CONTAINER_AUTHENTICATION_IMAGE='registry.gitlab.com/careerlyft-team/cv-script-microservice/authentication'
                # run('export CONTAINER_CV_PROFILE_NAME=registry.gitlab.com/careerlyft-team/cv-script-microservice/cv_profile')
                # run('export CONTAINER_PAYMENT_IMAGE=registry.gitlab.com/careerlyft-team/cv-script-microservice/payment')
                # run('export CONTAINER_ADMIN_IMAGE=registry.gitlab.com/careerlyft-team/cv-script-microservice/admin-service')
                # run('export #=ONTAINER_PDF_IMAGE: registry.gitlab.com/careerlyft-team/cv-script-microservice/html_to_pdf
                # run('export CONTAINER_BACKGROUND=registry.gitlab.com/careerlyft-team/cv-script-microservice/background')
                # run('export CONTAINER_PROXY=registry.gitlab.com/careerlyft-team/cv-script-microservice/proxy')
                sudo('docker login -u gbozee -p abiola2321 registry.gitlab.com')
                # sudo('docker build -t $CONTAINER_CVSCRIPT_IMAGE -f cvscript-service/Dockerfile cvscript-service')
                # sudo('docker push $CONTAINER_CVSCRIPT_IMAGE:latest')
                sudo('docker build -t {} -f authentication_service/Dockerfile authentication_service'.format(CONTAINER_AUTHENTICATION_IMAGE))
                sudo('docker push {}:latest'.format(CONTAINER_AUTHENTICATION_IMAGE))
                sudo('docker build -t {} -f cv_service/Dockerfile cv_service'.format(CONTAINER_CV_PROFILE_NAME))
                sudo('docker push {}:latest'.format(CONTAINER_CV_PROFILE_NAME))
                # sudo('docker build -t $CONTAINER_PAYMENT_IMAGE -f payment_service/Dockerfile payment_service')
                # sudo('docker push $CONTAINER_PAYMENT_IMAGE:latest')
                sudo('docker build -t {} -f admin_service/Dockerfile admin_service'.format(CONTAINER_ADMIN_IMAGE))
                sudo('docker push {}:latest'.format(CONTAINER_ADMIN_IMAGE))
                # # sudo(docker build -t $CONTAINER_PDF_IMAGE -f html-to-pdf-service/Dockerfile html-to-pdf-service)
                # # sudo(docker push $CONTAINER_PDF_IMAGE:latest)
                # sudo('docker build -t $CONTAINER_BACKGROUND -f background_service/Dockerfile background_service')
                # sudo('docker push $CONTAINER_BACKGROUND:latest')
                sudo('docker system prune -a')


def deploy_current(branch="develop"):
    print("hello World")
    run("pwd")
    code_dir = "/home/sama/careerlyft-ui/cv-script-microservice"
    common_code(code_dir, branch, True, False)


def display_logs(service="payment"):
    with settings(user="sama", password=password):
        code_dir = "/home/sama/careerlyft-ui/cv-script-microservice"
        with cd(code_dir):
            sudo("docker-compose  logs --follow --tail=10 {}".format(service))
            # sudo("docker-compose run authentication python manage.py migrate --noinput")


def delete_dangling():
    code_dir = "/home/sama/careerlyft-ui/cv-script-microservice"
    common_code(code_dir, True)


@hosts("sama@services.careerlyft.com")
def deploy_production():
    code_dir = "/home/sama/careerlyft"
    with settings(user="sama", password=password):
        with cd(code_dir):
            run("git pull")
            sudo("docker login -u gbozee -p abiola2321 registry.gitlab.com")
            sudo("docker-compose pull")
            # sudo(
            #     "docker-compose run cv_profile python manage.py migrate --noinput"
            # )
            sudo(
                "docker-compose  kill authentication payment cvscript cv_profile admin"
            )
            sudo(
                "docker-compose  rm -f authentication payment cvscript cv_profile html_to_pdf admin"
            )
            # sudo(
            #     "docker-compose  run admin python manage.py collectstatic --noinput"
            # )
            # sudo("docker-compose  run admin python manage.py migrate")
            sudo("docker-compose  up -d")
            sudo(
                'docker rmi $(docker images --filter "dangling=true" -q --no-trunc)'
            )


def run_all_test():
    local("pytest authentication_service")
    local("pytest cvscript-service")
    local("pytest cv_service")
    local("pytest payment_service")
