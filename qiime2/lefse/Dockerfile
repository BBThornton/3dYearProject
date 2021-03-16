FROM biobakery/lefse
WORKDIR /lefse
RUN pip install pymongo
ADD lefse_prep.py .
ENV PYTHONPATH=../home/linuxbrew/.linuxbrew/bin
