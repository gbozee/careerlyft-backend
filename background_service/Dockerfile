FROM python:3.7.2-alpine3.9

COPY ./hello.py /usr/local/bin/hello

RUN echo "* * * * *	   python /usr/local/bin/hello" > /etc/crontabs/root

CMD ["/usr/sbin/crond", "-f", "-d", "0"]
