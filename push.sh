tar -czf apemine.tgz .

scp -i ~/.ssh/<<YOUR_SSH_KEY>> -P <<PORT>> apemine.tgz root@<<SERVER_IP>>:~/

rm apemine.tgz