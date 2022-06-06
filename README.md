
[![OS](https://img.shields.io/badge/ubuntu-20.04.4-red?style=flat-square&logo=ubuntu)](https://releases.ubuntu.com/20.04/)
[![Microk8s](https://img.shields.io/badge/microk8s-1.21-red?style=flat-square&logo=canonical)](https://microk8s.io/resources)
[![Kubectl](https://img.shields.io/badge/kubectl-1.21-blue?style=flat-square&logo=kubernetes)](https://kubernetes.io/docs/tasks/tools/)
[![Helm](https://img.shields.io/badge/Helm-blue?style=flat-square&logo=helm)](https://helm.sh/)
# Kullanım

- Helm komutu çalıştırılan yerde [Helm](https://helm.sh) kurulu olmalı.
  - Linux: `sudo snap install helm`
  - Windows: [Releases helm/helm](https://github.com/helm/helm/releases/latest)
- Travelaps helm chart'larını nereden indireceğini tanımla:
  `helm repo add travelaps https://travelaps.github.io/helm-charts/`
- Kurulum parametrelerini değiştirmek için parametreleri dosyaya çıkar:
  `helm show values travelaps/<chart-adı> > values.yaml`
- Parametreleri ayarladıktan sonra kurulumu başlat:
  `helm install <isim> travelaps/<chart-adı> --values values.yaml --timeout 30m`
  
## ElektraWeb

- Erişime açık olması gereken domainler: (sadece kurulum sırasında değil program çalışırken de erişebilmeli, aksi taktirde kapanan programı geri açamayabilir)
  - 4001.hoteladvisor.net
  - ghcr.io
  - security.ubuntu.com
  - tr.archive.ubuntu.com
  - registry.hub.docker.com
  - docker.io
  - *.docker.io
  - docker.com
  - *.docker.com

- Gereksinimler:
    ```bash
    # Öncelikle microk8s, kubectl ve helm kurulu olduğundan emin ol:
    sudo snap install microk8s --classic --channel=1.21/stable && \
      sudo snap install kubectl --classic --channel=1.21/stable  && \
      sudo snap install helm --classic
    ```
    ```bash
    # makinanın dns adreslerini bul
    cat /etc/resolv.conf | grep nameserver | grep -v 127.0.0.53; \
      cat /run/systemd/resolve/resolv.conf | grep nameserver | grep -v 127.0.0.53
    ```
    ```bash 
    # microk8s add-on'ları aktive et. dns olması şart, ingress ve dashboard opsiyonel
    # dns adresi olarak üstte bulunan adresleri virgülle ayırarak yaz
    sudo microk8s enable dns:1.1.1.1,8.8.8.8 dashboard ingress
    
    # Oluşan kubernetes erişim config dosyasını kubectl'nin görebileceği yere dump et
    mkdir .kube
    sudo microk8s config > ~/.kube/config
    
    # Kubernetes çalıştığını doğrula
    kubectl cluster-info
  
    # (Opsiyonel:Longhorn)
    # Çoklu makina kurulumu yapılacaksa longhorn kur
    helm repo add longhorn https://charts.longhorn.io
    helm repo update
    helm install longhorn longhorn/longhorn \
         --namespace longhorn-system \
         --create-namespace \
         --set persistence.reclaimPolicy="Retain" \
         --set csi.kubeletRootDir="/var/snap/microk8s/common/var/lib/kubelet"
    # Longhorn kurulumunun tamamlanmasını bekle
    # watch -n1 "kubectl -n longhorn-system get pod"
  
    # (Opsiyonel:CertManager)
    # Otomatik SSL alımı/yenilemesi için CertManager kur
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    helm install cert-manager jetstack/cert-manager \
         --namespace cert-manager \
         --create-namespace \
         --version v1.7.1 \
         --set installCRDs=true
    # CertManager kurulumunun tamamlanmasını bekle
    # watch -n1 "kubectl -n cert-manager get pod"
    ```

- Elektraweb Sıfır Kurulum:
    ```bash
    # Travelaps kaynağını tanımla
    helm repo add travelaps https://travelaps.github.io/helm-charts/
    
    # Eğer daha önceden tanımlandıysa, güncellenmesi için repo update çalıştır.
    # İlk defa helm repo add ile eklendiyse buna gerek yok.
    helm repo update

    # Parametre dosya şablonunu values.yaml isimli dosyaya indir
    helm show values travelaps/elektraweb > values.yaml

    # Parametreleri nano, vim vs. bir editör ile ayarla
    nano values.yaml

    # Bu parametreler ile kurulumu başlat
    helm install elektraweb travelaps/elektraweb --values values.yaml --timeout 120m

    # (opsiyonel) Kurulumu gözlemlemek için:
    watch -n1 "kubectl get pods -A"
    ```
- Güncelleme / Parametre değiştirme (parametre set ederek):
    ```bash
    # Helm repolarını güncelle
    helm repo update
    
    # Upgrade komutunda --reuse-values diyerek
    # eski parametrelerin üzerine değiştirilecek her bir parametre için
    # --set ya da --set-string kullan.
    # --set param=1000 değeri direk 1000 olarak basar (bu durumda number olur)
    # --set-string=1000 değeri tırnak içinde "1000" olarak basar (bu durumda string olur)
    helm upgrade \
    --set parametreAdi=parametreDegeri \
    --set-string sql.saPassword=123456789 \
    --set sql.memoryLimit=8000 \
    --reuse-values
    elektraweb travelaps/elektraweb
- Güncelleme / Parametre değiştirme (values.yaml export ederek):
    ```bash
    # Helm repolarını güncelle
    helm repo update
    
    # Mevcut kurulumda kullanılan parametreleri dosyaya çıkar:
    helm get values elektraweb > values.yaml

    # Parametreleri değiştir
    nano values.yaml

    # Değişiklikleri uygula
    helm upgrade elektraweb travelaps/elektraweb --values values.yaml --timeout 120m
    ```
- Silme:
    ```bash
    helm uninstall elektraweb
    ```

<br>

#### SSL alımı için örnek ClusterIssuer

```yaml
# Domainler dışarıya açık olacaksa, http01 solver'ı ile otomatik SSL alınabilir.
# http01 yönteminde doğrulama, lets encrypt sunucularından domaine 80 portundan istek atılarak yapılır.
# Eğer domainler dışarıya açık olmayacaksa, o zaman dns solver'ları kullanılmalı.

# Staging
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: ssl@elektraweb.com
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - selector: {}
      http01:
        ingress:
          class: public
---
# Prod
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ssl@elektraweb.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - selector: {}
      http01:
        ingress:
          class: public
```
# Longhorn multipath
  https://longhorn.io/kb/troubleshooting-volume-with-multipath/
  
