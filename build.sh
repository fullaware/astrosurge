docker build . -t fullaware/beryl:latest
docker push fullaware/beryl:latest

helm upgrade beryl ./beryl/ -n beryl --create-namespace
kubectl rollout restart deploy beryl-app -n beryl