#!/bin/bash
# Arrête le service SpeedNote (les données restent, chiffrées, sur le disque).
systemctl --user stop speednote.service
