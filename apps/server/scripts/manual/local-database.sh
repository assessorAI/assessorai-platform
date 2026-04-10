#!/bin/bash

CONTAINER_NAME="assessorai-postgres"
IMAGE_NAME="assessorai-postgres"
VOLUME_NAME="assessorai-postgres-data"

case $1 in
  run)
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
      echo "Container já está rodando."
    elif docker ps -a -q -f name=$CONTAINER_NAME | grep -q .; then
      echo "Iniciando container existente..."
      docker start $CONTAINER_NAME
    else
      echo "Criando e iniciando novo container..."
      docker run --name $CONTAINER_NAME -v $VOLUME_NAME:/var/lib/postgresql/data -p 5432:5432 $IMAGE_NAME
    fi
    ;;
  stop)
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
      echo "Parando container..."
      docker stop $CONTAINER_NAME
    else
      echo "Container não está rodando."
    fi
    ;;
  status)
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
      echo "Rodando"
    else
      echo "Parado"
    fi
    ;;
  *)
    echo "Uso: $0 {run|stop|status}"
    ;;
esac
