
[![OS](https://img.shields.io/badge/ubuntu-22.04.4-red?style=flat-square&logo=ubuntu)](https://releases.ubuntu.com/jammy/)
[![Microk8s](https://img.shields.io/badge/microk8s-1.35-red?style=flat-square&logo=canonical)](https://microk8s.io/resources)
[![Kubectl](https://img.shields.io/badge/kubectl-1.35-blue?style=flat-square&logo=kubernetes)](https://kubernetes.io/docs/tasks/tools/)
[![Helm](https://img.shields.io/badge/Helm-blue?style=flat-square&logo=helm)](https://helm.sh/)
[![Istio](https://img.shields.io/badge/Istio-blue?style=flat-square&logo=istio)](https://istio.io/)
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

### Otelden istenecek ag ayari

**"Uygulama domainlerini bu sunucunun sabit yerel IP adresine yonlendirin;
TCP 80 ve 443 portlarini acin."** Yerel DNS kayitlari sunucunun LAN IP'sini
gostermelidir. Internetten erisim de isteniyorsa public DNS modem/firewall'un
public IP'sini gostermeli ve modem **80 -> sunucu:80, 443 -> sunucu:443**
NAT yonlendirmesi yapmalidir. CGNAT arkasinda disaridan erisim icin ayrica
erisebilir public IP veya bir tunel gerekir.

```text
Domain -> sunucunun LAN IP'si:80/443 -> elektraweb-gateway -> uygulama Service'i
Internet -> modem public IP:80/443 -> ayni sunucunun LAN IP'si:80/443
```

Sunucunun LAN IP'sini DHCP rezervasyonu/statik ayarla sabitleyin. Chart varsayilan
olarak **hostNetwork** kullanir: NodePort, MetalLB veya ek bir gateway IP'si
gerektirmez. Tek `elektraweb-gateway` Kubernetes Gateway API kaynagi olusturulur;
Istio bu kaynaktan gateway Deployment ve Service'ini otomatik olusturur.
Tum uygulamalar (opsiyonel dashboard dahil) ayni gateway'i `HTTPRoute` ile kullanir.
Uygulama pod'larina sidecar eklenmez; ambient/ztunnel kurulmaz.

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
    sudo snap install microk8s --classic --channel=1.35/stable && \
      sudo snap install kubectl --classic --channel=1.35/stable  && \
      sudo snap install helm --classic
    ```
    ```bash
    # Kullanıcıyı microk8s grubuna ekle
    sudo mkdir ~/.kube && \
      sudo usermod -a -G microk8s user && \
      sudo chown -R user ~/.kube && \
      newgrp microk8s
    ```    
    ```bash
    # Makinanın dns adreslerini bul
    cat /etc/resolv.conf | grep nameserver | grep -v 127.0.0.53; \
      cat /run/systemd/resolve/resolv.conf | grep nameserver | grep -v 127.0.0.53
    ```
    ```bash 
    # microk8s add-on'ları aktive et. dns olması şart, dashboard opsiyonel
    # dns adresi olarak üstte bulunan adresleri virgülle ayırarak yaz
    microk8s enable rbac dns:1.1.1.1,8.8.8.8 dashboard
    
    # Oluşan kubernetes erişim config dosyasını kubectl'nin görebileceği yere dump et
    microk8s config > ~/.kube/config
    chmod 600 ~/.kube/config
    
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
  
    ```
    ```bash
    # Elektraweb icin gerekli: Kubernetes Gateway API Standard Channel.
    # v1.5.0, HTTPRoute CORS filtresi icin gereklidir; v1.4.0 standard yeterli degildir.
    # Mevcut cloud CRD'lerini yukseltmeden once controller uyumlulugunu kontrol edin.
    kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.0/standard-install.yaml

    # Mesh olmadan Istio: istioctl veya microk8s istio add-on'u gerekmez.
    # Bu surum Kubernetes 1.32-1.36 ile desteklenir; eski 1.27 kurulumunu kullanmayin.
    helm repo add istio https://istio-release.storage.googleapis.com/charts
    helm repo update
    ISTIO_VERSION=1.30.6
    helm upgrade --install istio-base istio/base \
      --version "$ISTIO_VERSION" --namespace istio-system --create-namespace \
      --set defaultRevision=default --wait
    helm upgrade --install istiod istio/istiod \
      --version "$ISTIO_VERSION" --namespace istio-system --wait
    kubectl get gatewayclass istio

    # Uygulama namespace'lerinde istio-injection=enabled / istio.io/rev /
    # istio.io/dataplane-mode=ambient etiketleri kullanmayin.
    # Lokalde eski ingress add-on'u varsa 80/443 portlarini bosaltmak icin:
    # microk8s disable ingress
    # Diger uygulamalar ona bagimliysa kapatmadan once onlarin gecisini planlayin.
    # Ayni sunucuda baska nginx/Apache/gateway de 80/443 dinlememeli.
    ```
    ```bash
    # Otomatik SSL icin cert-manager (Gateway API CRD'lerinden SONRA kurun).
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    helm upgrade --install cert-manager jetstack/cert-manager \
         --namespace cert-manager \
         --create-namespace \
         --set crds.enabled=true \
         --set config.gatewayAPI.enabled=true \
         --wait
    # Bu ayar guncel cert-manager chart'i icindir. Eski kurulumlarda kendi
    # surumunuzun Gateway API etkinlestirme ayarini kullanin.
    # CertManager kurulumunun tamamlanmasını bekle
    # watch -n1 "kubectl -n cert-manager get pod"
    ```
- Diğer node'ları ekle
    ```bash
    microk8s add-node
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

    # Gateway ve yonlendirme durumunu kontrol et (varsayilan namespace: default)
    kubectl get gateways.gateway.networking.k8s.io elektraweb-gateway
    kubectl get httproutes.gateway.networking.k8s.io
    kubectl rollout status deployment/elektraweb-gateway-istio
    kubectl describe gateways.gateway.networking.k8s.io elektraweb-gateway
    # Listener/route durumlarinda Accepted=True ve ResolvedRefs=True beklenir.

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
    ```
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

### Lokal / cloud gateway ayarlari

Lokal varsayilanlar:

```yaml
istio:
  enabled: true
  gateway:
    name: elektraweb-gateway
    hostNetwork: true
    replicas: 1
    nodeSelector: {}
  httpsRedirect: true
```

Cok node'lu lokalde `istio.gateway.nodeSelector.kubernetes.io/hostname` degerini
modemin yonlendirildigi sunucunun `kubectl get nodes` ciktisindaki adina ayarlayin.
Tek sunucuda gerekli degildir. hostNetwork ayni node'un portlarini paylasir;
chart port cakismasini onlemek icin tek replika ve `Recreate` kullanir.
Gateway yenilenirken kisa erisim kesintisi olur. Dusuk portlara baglanabilmek icin
yalnizca gateway container'i UID 0 + `NET_BIND_SERVICE` ile calisir; privileged
mod acilmaz. Sunucunun 15020/15021/15090 yonetim/metric portlarini internete
acmayin, firewall'da sadece gerekli aglardan erisime izin verin.

Cloud/AKS icin ayni chart'in values dosyasinda:

```yaml
istio:
  gateway:
    hostNetwork: false
    serviceType: LoadBalancer
    replicas: 2
    serviceAnnotations:
      service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path: /healthz/ready
      service.beta.kubernetes.io/port_80_health-probe_port: "15021"
      service.beta.kubernetes.io/port_80_health-probe_protocol: http
      service.beta.kubernetes.io/port_443_health-probe_port: "15021"
      service.beta.kubernetes.io/port_443_health-probe_protocol: http
```

Annotation'lar Istio tarafindan uretilen Service'e aktarilir. TLS secret'lari,
Certificate'lar ve Gateway Helm release namespace'inde tutulur. Canli cloud'da
zaten ayni adli Gateway varsa bu chart'i dogrudan ustune kurmayin; once kaynak
sahipligi, mevcut HTTPRoute'lar, IP ve DNS gecisini planlayin. Bu rehber yeni
lokal kurulum icindir; cloud'a otomatik tasima yapmaz.

### TLS sertifikalari

Her aktif servisin `host` ve `tlsSecretName` degerini ayarlayin. HTTPS listener'in
calismasi icin bu secret'in release namespace'inde bulunmasi gerekir. Iki secenek:

- Mevcut sertifikayi `kubectl create secret tls <tlsSecretName> --cert=tls.crt --key=tls.key`
  ile yukleyin (release baska namespace'teyse `-n <namespace>` ekleyin).
- Asagidaki ClusterIssuer'i kurup ilgili serviste `sslClusterIssuer: letsencrypt-prod`
  ayarlayin; chart Certificate olusturur, cert-manager sertifikayi alir ve yeniler.

Ornek uygulama ayarlari (diger aktif servislerin domainlerini de ayarlayin):

```yaml
worker:
  host: api.otel.example.com
  tlsSecretName: nodejs4001-cert
  sslClusterIssuer: letsencrypt-prod
angus:
  host: app.otel.example.com
  tlsSecretName: elektraweb-cert
  sslClusterIssuer: letsencrypt-prod
```

Yalnizca otel icinden erisilen domainlerde HTTP-01 kullanilamaz. Public domain
icin DNS-01 veya kurumun guvenilir CA sertifikasini kullanin. Varsayilan
`elektraweb` gibi kisa host adlari Let's Encrypt sertifikasi alamaz.
DNS yonlendirmesi tek basina guvenilir HTTPS sertifikasi olusturmaz.

#### HTTP-01 ile otomatik SSL icin ornek ClusterIssuer

Bu ornek release'in `default` namespace'ine kuruldugunu varsayar. Farkli bir
namespace/gateway adi kullaniyorsaniz `parentRefs` degerlerini degistirin.
Public DNS ve modem 80/443 yonlendirmeleri dogru olmalidir. cert-manager gecici
bir HTTPRoute ile challenge'i cozer; daha spesifik challenge yolu genel HTTPS
yonlendirmesinden once eslesir. Istio icin DNS-01 zorunlu degildir.

```yaml
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
    - http01:
        gatewayHTTPRoute:
          parentRefs:
          - name: elektraweb-gateway
            namespace: default
            kind: Gateway
            sectionName: http
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
    - http01:
        gatewayHTTPRoute:
          parentRefs:
          - name: elektraweb-gateway
            namespace: default
            kind: Gateway
            sectionName: http
```

Staging sertifikalari tarayicida guvenilir degildir; once staging ile kurulumu
dogrulayin, sonra servislerin `sslClusterIssuer` degerini production issuer'a alin.
DNS-01 alternatifleri: https://cert-manager.io/docs/configuration/acme/dns01/

### Ingress'ten degisen davranislar

Bu degisiklik yalnizca `charts/elektraweb` icindir. Chart artik Ingress veya
VirtualService olusturmaz. CORS ve uygulama timeout'lari HTTPRoute'a tasindi;
HTTPRoute request timeout toplam istek suresidir, nginx read/send idle timeout
ile birebir ayni degildir. `/files` yalnizca fileUploader aktifken yonlendirilir.
Nginx'e ozel gzip, 30 MB body-size limiti, callcenter rate-limit ve reporting
cookie affinity otomatik tasinmadi; bunlara guvenen kurulumlarda gecisten once
uygulama veya Istio policy karsiliklarini planlayin.

Dashboard erisimi varsayilan kapali kalir. Acilirsa ayri gateway olusmaz;
namespace'ler arasi Service erisimi icin dar kapsamli ReferenceGrant ve eski
dashboard'un self-signed HTTPS backend'i icin Istio DestinationRule olusturulur.
Bu backend baglantisinda sertifika dogrulamasi kapali, dis HTTPS baglantisinda
ise normal TLS sertifikasi kullanilir. Dashboard'u internete acmadan once
erisim kisitlamalarini ayrica uygulayin.

Referanslar: [Istio Gateway API](https://istio.io/latest/docs/tasks/traffic-management/ingress/gateway-api/),
[standart CORS filtresi](https://gateway-api.sigs.k8s.io/guides/http-cors/),
[Istio/Kubernetes surum uyumlulugu](https://istio.io/latest/docs/releases/supported-releases/).

### Chart gelistirme kontrolu

Helm ve Python bulunan bir ortamda, repository kokunden:

```bash
python -m pip install -r charts/elektraweb/tests/requirements.txt
python -B -m unittest discover -s charts/elektraweb/tests -v
helm lint charts/elektraweb --kube-version 1.35.0
```

Helm PATH'te degilse `HELM_BIN` ortam degiskenine executable yolunu verin.
# Longhorn multipath
  https://longhorn.io/kb/troubleshooting-volume-with-multipath/
  
