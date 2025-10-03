FROM python:3-alpine

ENV NO_I18N=False
ENV SECRET_KEY=randomsecret123!@#
RUN apk add --no-cache gettext-dev

# Install a WSGI server to serve our files, later this should also include daphne to serve ASGI in case is needed with a conditional script based on a build argument
RUN [ -z "$USE_DAPHNE" ] || [ "$USE_DAPHNE" = "True" ] && pip install daphne || pip install gunicorn

COPY ./entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

COPY ./ /app/

# This is at this place to make this instruction not to invalid the previous one 
ARG REQUIREMENTS_BASE_FOLDER=.
ARG STATICFILES_PATH=/app/static/

WORKDIR /app/

# Install your requirements from a requirements.txt file (support for poetry, pipenv should also be included at some point)
RUN pip install -r ${REQUIREMENTS_BASE_FOLDER}/requirements.txt


ENTRYPOINT ["/entrypoint.sh"]