FROM python:3.10.4-slim-bullseye

RUN pip install --upgrade pip

RUN adduser --disabled-password crump
USER crump
WORKDIR /home/crump

COPY --chown=crump:crump requirements.txt requirements.txt
RUN pip install --user -r requirements.txt

ENV PATH="/home/crump/.local/bin:${PATH}"

COPY --chown=crump:crump . .

CMD ["python", "main.py"]