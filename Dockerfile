FROM python:3.11-slim-bullseye

ENV LANG ko_KR.UTF-8
ENV LANGUAGE ko_KR.UTF-8
ENV PYTHONIOENCODING utf-8
RUN ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
RUN echo "alias ll='ls -alF --color=auto'" >> /etc/profile
RUN echo "alias ll='ls -alF --color=auto'" >> /etc/bash.bashrc

RUN apt-get update
# asyncmy 등 인스톨에 필요한 패키지 (wheel 인스톨 등에 사용)
RUN apt-get install gcc -y

# build 관련 (gcc, g++, make 등) 전체 설치 시
#RUN apt-get install build-essential -y

RUN python -m pip install --upgrade pip
WORKDIR /api
VOLUME /api/appconfig

WORKDIR /tmp/pyinst
COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements/fastapi.txt
RUN pip install --no-cache-dir --upgrade -r requirements/redis.txt
RUN pip install --no-cache-dir --upgrade -r requirements/mongodb.txt
RUN pip install --no-cache-dir --upgrade -r requirements/requirements.txt
RUN python find_controller.py
RUN pyinstaller --clean --distpath /api ./main.spec

WORKDIR /api
RUN rm -rf /tmp/pyinst

ENTRYPOINT [""]
CMD ["./main"]