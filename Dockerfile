# app/Dockerfile

# Docker files can only copy from bellow them in the dir structure
# If you are using a cloud build. You should clean up the folder because otherwise wit will send everything even if it's not used

FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*


COPY ./requirements.txt .
RUN pip3 install -r ./requirements.txt

ADD ./components ./components
ADD ./.streamlit ./.streamlit
COPY instructions.md .
COPY app.py . 

WORKDIR /app
# Don't forget to copy anything else the file need like models, etc.
#Changed so it picks up the port from container env variables which is required by cloud run etc
ENTRYPOINT ["sh", "-c", "streamlit run --server.port $PORT ./app.py"] 
#ENTRYPOINT ["streamlit", "run","./example-streamlit.py", "--server.port",${PORT}, "--server.address=0.0.0.0"]
