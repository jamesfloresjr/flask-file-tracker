# flask file tracker

FROM redhat/ubi9-minimal
LABEL maintainer="James Flores <james.flores@ngc.com>"

RUN microdnf upgrade
RUN microdnf install -y python3 python3-pip supervisor
RUN microdnf clean all

# Setup flask application
RUN mkdir -p /deploy/app
COPY app /deploy/app
#RUN pip install -r /deploy/app/requirements.txt

# Setup monitor script
RUN mkdir -p /deploy/monitor
COPY monitor /deploy/monitor

# Setup supervisord
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start processes
CMD ["/usr/bin/supervisord"]