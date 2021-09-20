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
- Güncelleme / Parametre değiştirme:
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
