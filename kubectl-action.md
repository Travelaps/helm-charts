# Ubuntu Kubernetes Pod Yönetimi Dökümanı

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
NAME                     READY   STATUS    RESTARTS   AGE
nginx-6d9f7d4d5-abc12   1/1     Running   0          2h
redis-74d8c69b7f-xkj34  1/1     Running   1          5h
mysql-84bd9c6c7-vqkw1   1/1     Error     3          10m
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
| Pending    | Pod, bir node'da çalıştırılmaya hazır ancak henüz başlamamış. |
| Running    | Pod, bir node'da başlamış ve en az bir container çalışıyor. |
| ContainerCreating | Pod'un container'ları oluşturuluyor. Bu süreç, image pull, volume mount gibi adımları içerir. |
| Succeeded  | Pod, görevi başarıyla tamamladı ve sona erdi.       |
| Failed     | Pod, görevini tamamlayamadan sona erdi.        |
| CrashLoopBackOff | Pod, tekrar tekrar başlamaya çalışıyor ancak başarısız. |

---

Bu döküman, Kubernetes ortamında podları verimli bir şekilde yönetmenize yardımcı olacaktır. 

## Lisans
Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakabilirsiniz.

