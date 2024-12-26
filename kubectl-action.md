# Ubuntu Kubernetes Yönetimi Dökümanı

Bu dökümanda Ubuntu kümesinde podları listeleme, toplu olarak yeniden başlatma ve pod durumlarının anlamları üzerine temel bilgiler verilecektir. 

## 1. Microk8s komutları
ElektraWeb uygulaması microk8s içerisinde çalışmaktadır, öncelikle microk8s uygulamasının çalışma durumu kontrol edilmelidir:
```bash
sudo microk8s status
```
Kontrol sonrası "microk8s not running" uyarısı alınıyorsa, aşağıdaki komut çalıştırılarak microk8s yeniden başlatılır:
```bash
sudo microk8s start
```
## 2. Microk8s içerisinde ElektraWeb Podlarını Listeleme
Kubernetes kümesindeki podları listelemek için aşağıdaki komut kullanılır:
```bash
kubectl get pods
```
Belirli bir namespace için podları listelemek isterseniz:
```bash
kubectl get pods -n default
```
Bu komut, default namespace'deki podları listeleyecektir. 

### Pod Listesi Çıktısı Örneği:
```
NAME                                        READY   STATUS    RESTARTS        AGE
pos-ng11-5f6fd7db8d-58w6l                   1/1     Running   8 (4h41m ago)   528d
einvoice-integrator-875586df-cgcd6          1/1     Running   1 (4h41m ago)   15d
file-uploader-dc7c7cbc7-xp4zp               1/1     Running   8 (4h41m ago)   528d
sql-7fc77f8cd4-z4lwr                        1/1     Running   1 (4h41m ago)   7d6h
nodejs-http-74b894d659-dlnwt                1/1     Running   1 (4h41m ago)   19d
nodejs-http-74b894d659-vckx2                1/1     Running   1 (4h41m ago)   7h6m
action-script                               1/1     Running   7 (4h41m ago)   525d
nodejs-ingenico-74c84d69fc-5wzst            1/1     Running   1 (4h41m ago)   19d
rabbit-5bb478698b-zcss4                     1/1     Running   0               4h37m
reportingcore-7984754499-69jn6              1/1     Running   1 (4h41m ago)   19d
redis-5c49b5d47f-w98st                      1/1     Running   0               4h36m
nodejs-worker-elektraweb-5f8866f568-ghpwf   1/1     Running   0               4h32m
nodejs-worker-elektraweb-5f8866f568-gkzdp   1/1     Running   0               4h32m
angus-7fff4db88-p42k4                       1/1     Running   6 (4h41m ago)   293d
nodejs-worker-elektraweb-5f8866f568-mztqp   1/1     Running   0               4h32m
nodejs-worker-elektraweb-5f8866f568-9lbw8   1/1     Running   0               4h32m
```

## 3. Podları Toplu Yeniden Başlatma
Tüm deployment'ları toplu olarak yeniden başlatmak için aşağıdaki komut kullanılır:

```bash
kubectl rollout restart deployment -n default
```
Belirli bir deployment için:
```bash
kubectl rollout restart deployment nodejs-worker
```

## 4. Pod Durumlarının Anlamları

| Durum      | Anlamı                                      |
|------------|----------------------------------------------|
| Pending    | Pod, bir node'da çalıştırılmaya hazır ancak henüz başlamamış, bir süre sonra running durumuna geçmesi beklenir. |
| Running    | Pod, bir node'da başlamış ve en az bir container çalışıyor. |
| ContainerCreating | Pod'un container'ları oluşturuluyor. Bu süreç, image pull, volume mount gibi adımları içerir. |
| Failed     | Pod, çalışmayı durdurdu.        |
| CrashLoopBackOff | Pod, tekrar tekrar başlamaya çalışıyor ancak başarısız. |

---

Bu döküman, Kubernetes ortamında podları verimli bir şekilde yönetmenize yardımcı olacaktır. 

## Lisans
Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakabilirsiniz.

