FROM ubuntu:14.04.2

MAINTAINER Julien Almarcha <julien.almarcha@gmail.com>

#install dependancies
RUN apt-get update && apt-get install -y python3 python3-dev wget build-essential zlib1g-dev libxt6 libxext6 ghostscript libjpeg-dev python3.4-venv libxslt-dev libxml2-dev

#add additionnal resources
ADD makevenv /labresult/
ADD labresult*.egg /labresult/
ADD run.py /labresult/
ADD wsgilabresult.py /labresult/
ADD uwsgi.ini /labresult/
ADD runcelery.py /labresult/
ADD pcl6-915-linux_x86_64 /usr/bin/pcl6

#set locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

#create virtual env
WORKDIR /labresult
RUN ./makevenv .
RUN ./bin/easy_install labresult-0.1-py3.4.egg
RUN ./bin/easy_install labresult_admin-1.0-py3.4.egg
RUN ./bin/easy_install labresult_demo-1.0-py3.4.egg
RUN ./bin/easy_install labresult_pclparser-1.0-py3.4.egg
RUN ./bin/easy_install labresult_pdfparser-1.0-py3.4.egg

# finally remove dev library after library creation
RUN apt remove -y --purge python3-dev build-essential zlib1g-dev libjpeg-dev libxslt-dev libxml2-dev

#create user labresult
RUN useradd -d /labresult labresult
RUN chown -R labresult:labresult /labresult 
RUN mkdir /var/log/labresult/
RUN chown labresult:labresult /var/log/labresult
USER labresult

#expose wsgi port
EXPOSE 8000

CMD ["/labresult/bin/uwsgi","--ini", "/labresult/uwsgi.ini"]
