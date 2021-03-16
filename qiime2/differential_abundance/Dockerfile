FROM qiime2/core:2020.8

WORKDIR /da
RUN pip install pymongo
ADD da.py .
ENV PYTHONPATH=/da
