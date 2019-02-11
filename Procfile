web: gunicorn fredagscafeen.wsgi --log-file -
worker: ssh -o StrictHostKeyChecking=no -4 -N -i media/ssh/id_rsa -L 6631:0.0.0.0:6631 remoteprint_relay@fredagscafeen.dk
