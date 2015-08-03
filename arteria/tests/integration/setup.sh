#!/bin/bash

config_path="/opt/arteria-test/etc"
mkdir -pv $config_path 
cp ../../templates/logger.config $config_path
cp ../../templates/app.config $config_path
chown -R vagrant:vagrant $config_path 
