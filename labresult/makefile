egg: 
	./compile_plugins
	@echo "Building $@..."
ifeq ($(EXCLUDE_SOURCE), yes)
	@./bin/python setup.py clean bdist_egg --exclude-source-files
	@echo ""
	@echo "+-----------------------------------------------+"
	@echo "| INFO : SOURCES ARE NOT PRESENT IN CREATED EGG |"
	@echo "+-----------------------------------------------+"
else 
	@./bin/python setup.py clean bdist_egg
	@echo ""
	@echo "+----------------------------------------------+"
	@echo "| WARNING : SOURCES ARE PRESENT IN CREATED EGG |"
	@echo "| ( set EXCLUDE_SOURCE=yes in command line to  |"
	@echo "| remove it, but for now it does not work      |"
	@echo "| without source...)                           |"
	@echo "+----------------------------------------------+"
	@echo "Done."
endif

dockerdemoimage:
	cp ../plugin-lr-*/dist/*.egg dockerdemo/
	cp dist/labresult-0.1-py3.4.egg runcelery.py uwsgi.ini wsgilabresult.py dockerdemo/
	cd dockerdemo && docker build -t dowst/labresultdemo .

dockerimage:
	cp ../plugin-lr-*/dist/*.egg docker/
	cp dist/labresult-0.1-py3.4.egg run.py runcelery.py uwsgi.ini wsgilabresult.py docker/
	cd docker && docker build -t dowst/labresult:0.1 .

# Babel helper
update_catalog:
	./bin/python setup.py extract_messages update_catalog

compile_catalog:
	./bin/python setup.py compile_catalog

