web: gunicorn fredagscafeen.wsgi --log-file -
worker: ssh -4 -N -i media/ssh/id_rsa -L 6631:127.0.0.1:6631 remoteprint_relay@fredagscafeen.dk
