FROM python:3.5

MAINTAINER Julien Almarcha <julien.almarcha@gmail.com>

# install dependancies
RUN apt-get update && apt-get install -y python3 python3-dev wget build-essential zlib1g-dev libxt6 libxext6 ghostscript libjpeg-dev python3.4-venv libxslt-dev libxml2-dev

# add additionnal resources
ADD run.py /labresult/
ADD wsgilabresult.py /labresult/
ADD uwsgi.ini /labresult/
ADD runcelery.py /labresult/
ADD pcl6-915-linux_x86_64 /usr/bin/pcl6

# add packages
ADD labresult /labresult/labresult
ADD labresult_admin /labresult/labresult_admin
RUN ls /labresult/labresult_admin
ADD labresult_pclparser /labresult/labresult_pclparser
ADD labresult_allmysms /labresult/labresult_allmysms
ADD labresult_demo /labresult/labresult_demo
ADD labresult_pdfparser /labresult/labresult_pdfparser

# install packages
WORKDIR /labresult
RUN cd labresult && python setup.py install
RUN cd labresult_admin && python setup.py install
RUN cd labresult_pclparser && python setup.py install
RUN cd labresult_allmysms && python setup.py install
RUN cd labresult_demo && python setup.py install
RUN cd labresult_pdfparser && python setup.py install

# finally remove dev library after library creation
RUN apt remove -y --purge python3-dev build-essential zlib1g-dev libjpeg-dev libxslt-dev libxml2-dev

# create user labresult
RUN useradd -d /labresult labresult
RUN chown -R labresult:labresult /labresult 
RUN mkdir /var/log/labresult/
RUN chown labresult:labresult /var/log/labresult
USER labresult

# expose wsgi port
EXPOSE 5000

CMD ["/usr/local/bin/uwsgi","--ini", "/labresult/uwsgi.ini"]
