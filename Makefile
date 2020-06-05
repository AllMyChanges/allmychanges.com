CURRENT_VERSION = `cat CURRENT_VERSION`

all:
	@echo "Current version: ${CURRENT_VERSION}"

build_static: # Build static javascript and css files.
	yarn run gulp

get_latest_db:
	scp clupea:/mnt/yandex.disk/backups/mysql/allmychanges/latest.sql.bz2 dumps/

RESTORE_DB = 'latest'
restore_db:
	docker exec -ti mysql.allmychanges.com /dumps/restore.sh ${RESTORE_DB}

backup_dev_db:
	docker exec mysql.allmychanges.com mysqldump  -ppassword allmychanges > dumps/dev.sql

create_postgres:
    # https://hub.docker.com/_/postgres/
    # how to run psql
    # $
	docker exec -it postgres.allmychanges.com postgresadmin -ppassword create allmychanges

drop_postgres:
	docker exec -it postgres.allmychanges.com postgresadmin -ppassword drop allmychanges
	create_postgres

connect_to_postgres:
	docker run -it --net amch --rm postgres \
		sh -c 'exec psql -h postgres.allmychanges.com -p 5432 -U postgres'

create_database:
	docker exec -it mysql.allmychanges.com mysqladmin -ppassword create allmychanges

drop_database:
	docker exec -it mysql.allmychanges.com mysqladmin -ppassword drop allmychanges
	create_database

dbshell:
	docker exec -it mysql.allmychanges.com mysql -ppassword allmychanges

push_to_amch:
	time pip2amch --tag allmychanges.com requirements/production.txt | amch push

build_wheels:
	docker run --rm -v `pwd`:/wheels 40ants/wheel-builder --wheel-dir wheelhouse -r requirements/dev.txt

DEV_TAG = 'allmychanges.com:dev'
build_image:
	docker build ./ -t ${DEV_TAG}
	@echo "Built ${DEV_TAG}"

TAG = "registry.40ants.com:5000/allmychanges.com:${CURRENT_VERSION}"
push_image:
	@echo "Using tag: ${TAG}"
	docker build ./ -t ${TAG}
	docker push ${TAG}
	@echo "Pushed ${TAG}"

update_requirements:
	pip-compile --annotate requirements.in
	pip-compile --annotate requirements-dev.in

SERVER_PORT=80
run_server:
	python ./manage.py runserver 0.0.0.0:${SERVER_PORT}

migrate:
	python ./manage.py migrate
