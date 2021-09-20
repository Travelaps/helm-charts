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

- Sıfır kurulum:
    ```bash
    # Öncelikle microk8s, kubectl ve helm kurulu olduğundan emin ol:
    sudo snap install microk8s --classic
    sudo snap install kubectl --classic
    sudo snap install helm --classic
    
    # microk8s add-on'ları aktive et. dns olması şart, ingress ve dashboard opsiyonel
    sudo microk8s enable dns dashboard ingress
    
    # Oluşan kubernetes erişim config dosyasını kubectl'nin görebileceği yere dump et
    mkdir .kube
    sudo microk8s config > ~/.kube/config
    
    # Kubernetes çalıştığını doğrula
    kubectl cluster-info
    
    # Travelaps kaynağını tanımla
    helm repo add travelaps https://travelaps.github.io/helm-charts/

    # Parametre dosya şablonunu values.yaml isimli dosyaya indir
    helm show values travelaps/elektraweb > values.yaml

    # Parametreleri ayarla
    nano values.yaml

    # Bu parametreler ile kurulumu başlat
    helm install elektraweb travelaps/elektraweb --values values.yaml --timeout 30m

    # (opsiyonel) Kurulumu gözlemlemek için:
    watch -n1 "kubectl get pods -A"
    ```
- Güncelleme / Parametre değiştirme (parametre set ederek):
    ```bash
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
    # Mevcut kurulumda kullanılan parametreleri dosyaya çıkar:
    helm get values elektraweb > values.yaml

    # Parametreleri değiştir
    nano values.yaml

    # Değişiklikleri uygula
    helm upgrade elektraweb travelaps/elektraweb --values values.yaml --timeout 30m
    ```
- Silme:
    ```bash
    helm uninstall elektraweb
    ```
