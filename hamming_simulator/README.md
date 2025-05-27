[https://studio.youtube.com/video/cl4GyYYznHE/edit](https://youtu.be/cl4GyYYznHE)

# Hamming SEC-DED Kod Simülatörü 

Bu proje, 8, 16 ve 32 bitlik veriler için Hamming SEC-DED (Single Error Correcting – Double Error Detecting) algoritmasını kullanan basit bir simülasyon yazılımıdır.

## Projenin Amacı

Yazılım, kullanıcıların:
*   Belirli uzunluktaki (8, 16, 32 bit) bir veri için Hamming SEC-DED kodunu hesaplamasını,
*   Bu veriyi ve üretilen Hamming kodunu simüle edilmiş bir belleğe yazmasını,
*   Bellekteki bir Hamming kodunun herhangi bir bitinde yapay bir hata oluşturmasını,
*   Oluşturulan bu yapay hatanın, sendrom kelimesi yorumlanarak nasıl tespit edildiğini ve hatalı bitin pozisyonunun nasıl bulunduğunu gözlemlemesini sağlar.

## Temel Özellikler

*   **Veri Girişi ve Hamming Kodu Üretimi:** Kullanıcı tarafından girilen 8, 16 veya 32 bitlik binary veri için Hamming SEC-DED kodu hesaplanır ve arayüzde gösterilir.
*   **Belleğe Yazma:** Kullanıcının girdiği veri ve bu veri için üretilen Hamming kodu, simüle edilmiş bellekte belirtilen bir adrese yazılır.
*   **Bellek Görüntüleme:** Simüle edilmiş belleğin içeriği (adres, Hamming kodu ve hata durumu) bir listede gösterilir.
*   **Yapay Hata Oluşturma:** Kullanıcı, bellekteki seçili bir Hamming kodunun istediği bir bitinde (1-indeksli) yapay bir hata (biti tersine çevirme) oluşturabilir. Bu değişiklik belleğe yansıtılır.
*   **Sendrom Hesaplanması ve Hata Teyidi:** Bellekteki (potansiyel olarak hatalı) bir Hamming kodu için:
    *   Sendrom değeri hesaplanır.
    *   Genel parite kontrolü yapılır.
    *   Bu bilgilere dayanarak hata durumu (hata yok, tek bit hata, çift bit hata vb.) ve tek bitlik bir hata varsa hatalı bitin pozisyonu kullanıcıya gösterilir. Bu özellik, yapay olarak oluşturulan hatanın Hamming mekanizmasıyla nasıl bulunduğunu teyit etmeye yöneliktir; otomatik bir düzeltme işlemi yapılmaz.
*   **Hatayı Temizleme:** Bellekte oluşturulmuş yapay bir hata, orijinal (hatasız) Hamming koduna geri döndürülerek temizlenebilir.

## Nasıl Çalıştırılır?

### Gereksinimler

*   **Python 3:** Proje Python 3 ile yazılmıştır. Sisteminizde Python 3'ün kurulu olması gerekmektedir.
*   **Tkinter:** Grafiksel kullanıcı arayüzü (GUI) için Tkinter kütüphanesi kullanılmaktadır. 
    *   Çoğu Python kurulumu Tkinter'ı içerir. 
    *   Eğer macOS kullanıyorsanız ve Python'u Homebrew ile yüklediyseniz, `ModuleNotFoundError: No module named '_tkinter'` hatası alırsanız, aşağıdaki komutlarla Tkinter bağımlılıklarını ve Python için Tkinter bağlamalarını yüklemeniz gerekebilir:
        ```bash
        brew install tcl-tk
        brew install python-tk@<python_versiyonunuz>
        # Örneğin: brew install python-tk@3.13
        ```

### Çalıştırma Adımları

1.  Proje dosyalarını bilgisayarınıza indirin/klonlayın.
2.  Terminalinizi (komut istemi) açın.
3.  Projenin ana dizini altındaki `src` klasörüne gidin:
    ```bash
    cd path/to/hamming_simulator/src
    ```
4.  Aşağıdaki komutla uygulamayı başlatın:
    ```bash
    python3 main.py
    ```

## Proje Dosyaları ve Modüller

*   `src/`
    *   `main.py`: Ana uygulama mantığını ve Tkinter ile oluşturulmuş grafiksel kullanıcı arayüzünü içerir.
    *   `hamming_codec.py`: Hamming SEC-DED kodunun üretilmesi, sendromun hesaplanması ve hataların yorumlanması (tek hata pozisyonu bulma, çift hata tespiti) ile ilgili fonksiyonları barındırır.
    *   `memory_simulator.py`: Verilerin ve Hamming kodlarının saklandığı, hataların eklenebildiği ve okunabildiği simüle edilmiş bellek yapısını yöneten sınıfı içerir.
*   `README.md`: Bu dosya; proje hakkında genel bilgiler ve çalıştırma talimatlarını içerir.
*   `prd.md`: Projenin orijinal ürün gereksinimleri dokümanı (Türkçe). 
