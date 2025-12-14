#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <package_name>"
  exit 1
fi


if [ -z "$VIRTUAL_ENV" ]; then
  echo "Warning: No virtual environment activated. Installing globally or to user site."
fi


pip install "$1"
if [ $? -ne 0 ]; then
    echo "Error installing package '$1'. Exiting."
    exit 1
fi


pip freeze > requirements.txt
if [ $? -eq 0 ]; then
    echo "Package '$1' installed and requirements.txt updated."
else
    echo "Error updating requirements.txt."
fi