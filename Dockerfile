# flask file tracker

FROM python:3-alpine
LABEL maintainer="James Flores <james.flores@ngc.com>"

# Setup flask application
RUN mkdir -p /deploy/app
COPY app /deploy/app
RUN pip install --no-cache-dir -r /deploy/app/requirements.txt

# Setup monitor script
RUN mkdir -p /deploy/monitor
COPY monitor /deploy/monitor

# Setup supervisord
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisord.conf

# Expose port
#EXPOSE 5000

# Start processes
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisord.conf"]
