.PHONY: build deploy clean all

HOST=www.adass2020.es


all: build

build: clean
	cd website && lektor build --output-path ../www && cd ..

deploy: build
	rsync -av --delete ./www/ root@${HOST}:/var/www/html/

clean:
	cd website && lektor clean && cd ..
