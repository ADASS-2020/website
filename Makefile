.PHONY: build deploy clean all

PROD_HOST=www.adass2020.es
DEV_HOST=dev.adass2020.es
DEV2_HOST=dev2.adass2020.es


all: build

build: clean
	cd website && lektor build --output-path ../www && cd ..

deploy: build
	rsync -av --delete ./www/ root@${PROD_HOST}:/var/www/html/ --exclude=static/ftp

dev2deploy: build
	rsync -av --delete ./www/ root@${DEV2_HOST}:/var/www/html/ --exclude=static/ftp

devdeploy: build
	rsync -av --delete ./www/ root@${DEV_HOST}:/var/www/html/ --exclude=static/ftp

clean:
	cd website && lektor clean && cd ..
