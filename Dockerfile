FROM jupyter/all-spark-notebook
# FROM jupyter/pyspark-notebook
# FROM python:3.7

# RUN pip install --upgrade pip

# ## Install Spark 
# # From https://github.com/jupyter/docker-stacks/blob/master/pyspark-notebook/Dockerfile
# ARG spark_version="3.0.0"
# ARG hadoop_version="3.2"
# ARG spark_checksum="BFE45406C67CC4AE00411AD18CC438F51E7D4B6F14EB61E7BF6B5450897C2E8D3AB020152657C0239F253735C263512FFABF538AC5B9FFFA38B8295736A9C387"
# ARG py4j_version="0.10.9"
# ARG openjdk_version="11"

# ENV APACHE_SPARK_VERSION="${spark_version}" \
#     HADOOP_VERSION="${hadoop_version}"

# RUN apt-get -y update && \
#     apt-get install --no-install-recommends -y \
#     "openjdk-${openjdk_version}-jre-headless" \
#     ca-certificates-java && \
#     rm -rf /var/lib/apt/lists/*

# # Spark installation
# WORKDIR /tmp
# # Using the preferred mirror to download Spark
# # hadolint ignore=SC2046
# RUN wget -q $(wget -qO- https://www.apache.org/dyn/closer.lua/spark/spark-${APACHE_SPARK_VERSION}/spark-${APACHE_SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz\?as_json | \
#     python -c "import sys, json; content=json.load(sys.stdin); print(content['preferred']+content['path_info'])") && \
#     echo "${spark_checksum} *spark-${APACHE_SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" | sha512sum -c - && \
#     tar xzf "spark-${APACHE_SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" -C /usr/local --owner root --group root --no-same-owner && \
#     rm "spark-${APACHE_SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz"

# WORKDIR /usr/local
# RUN ln -s "spark-${APACHE_SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}" spark

# # Configure Spark
# ENV SPARK_HOME=/usr/local/spark
# ENV PYTHONPATH="${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-${py4j_version}-src.zip" \
#     SPARK_OPTS="--driver-java-options=-Xms1024M --driver-java-options=-Xmx4096M --driver-java-options=-Dlog4j.logLevel=info" \
#     PATH=$PATH:$SPARK_HOME/bin


## Back to OpenPredict install
COPY . .

# Install from source code
RUN pip install -e .

# EXPOSE 8808

# ENTRYPOINT [ "openpredict" ]
# CMD [ "start-api" ]