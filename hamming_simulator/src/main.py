import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from hamming_codec import (
    generate_hamming_code,
    check_and_correct_hamming_code,
    get_num_hamming_parities,
    get_hamming_parity_positions,
    calculate_syndrome_and_overall_parity_check
)
from memory_simulator import MemorySimulator

class HammingApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Basit Hamming SEC-DED Simülatörü")
        self.root.geometry("680x800")

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.memory = MemorySimulator(size=16)
        self.selected_data_length = tk.IntVar(value=8)
        self.current_input_data_bits = [] # Kullanıcının girdiği veri
        self.current_generated_hc = []    # Üretilen HC (belleğe yazılmadan önce)
        
        self.selected_memory_address = tk.IntVar(value=-1) # Listboxtan seçilen adres

        self.create_widgets()
        self.update_memory_listbox()

    def create_widgets(self):
        # Ana kaydırılabilir alan için Canvas ve Scrollbar
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Asıl içeriği tutacak çerçeve (bu Canvas'ın içine girecek)
        self.main_scrollable_frame = ttk.Frame(canvas, padding="10")
        
        # main_scrollable_frame'i Canvas'a ekle
        canvas.create_window((0, 0), window=self.main_scrollable_frame, anchor="nw")

        # main_scrollable_frame'in boyutu değiştikçe Canvas'ın scrollregion'ını güncelle
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.main_scrollable_frame.bind("<Configure>", on_frame_configure)

        # --- Şimdi tüm widget'lar main_frame yerine self.main_scrollable_frame içine eklenecek ---
        main_frame = self.main_scrollable_frame # Kolay erişim için referans

        # 1. Veri Girişi ve Kodlama
        input_labelframe = ttk.LabelFrame(main_frame, text="1. Veri Girişi ve Hamming Kodu Üretimi", padding="10")
        input_labelframe.pack(fill=tk.X, pady=5)

        ttk.Label(input_labelframe, text="Veri (Binary):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.data_entry = ttk.Entry(input_labelframe, width=35)
        self.data_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        length_frame = ttk.Frame(input_labelframe)
        length_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(length_frame, text="Uzunluk:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Radiobutton(length_frame, text="8-bit", variable=self.selected_data_length, value=8, command=self._update_entry_placeholder).pack(side=tk.LEFT)
        ttk.Radiobutton(length_frame, text="16-bit", variable=self.selected_data_length, value=16, command=self._update_entry_placeholder).pack(side=tk.LEFT)
        ttk.Radiobutton(length_frame, text="32-bit", variable=self.selected_data_length, value=32, command=self._update_entry_placeholder).pack(side=tk.LEFT)

        self.generate_hc_button = ttk.Button(input_labelframe, text="Hamming Kodu Üret", command=self._process_generate_code)
        self.generate_hc_button.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Label(input_labelframe, text="Üretilen HC:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.generated_hc_display = ttk.Label(input_labelframe, text="-", font=("Courier", 10), wraplength=450)
        self.generated_hc_display.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)

        # 2. Belleğe Yazma
        write_mem_labelframe = ttk.LabelFrame(main_frame, text="2. Belleğe Yaz", padding="10")
        write_mem_labelframe.pack(fill=tk.X, pady=5)

        ttk.Label(write_mem_labelframe, text="Bellek Adresi (0-{}):".format(self.memory.size - 1)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.write_address_entry = ttk.Entry(write_mem_labelframe, width=5)
        self.write_address_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.write_to_memory_button = ttk.Button(write_mem_labelframe, text="Belleğe Yaz", command=self._process_write_to_memory, state=tk.DISABLED)
        self.write_to_memory_button.grid(row=0, column=2, padx=10, pady=5)

        # 3. Bellek Görüntüleme ve Seçim
        mem_display_labelframe = ttk.LabelFrame(main_frame, text="3. Bellek İçeriği", padding="10")
        mem_display_labelframe.pack(fill=tk.X, pady=5)
        
        self.memory_listbox = tk.Listbox(mem_display_labelframe, height=8, exportselection=False, font=("Courier", 10))
        self.memory_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        mem_scrollbar = ttk.Scrollbar(mem_display_labelframe, orient=tk.VERTICAL, command=self.memory_listbox.yview)
        self.memory_listbox.config(yscrollcommand=mem_scrollbar.set)
        mem_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.memory_listbox.bind("<<ListboxSelect>>", self._on_memory_select)

        # 4. Hata Oluşturma ve Sendrom Analizi
        error_sim_labelframe = ttk.LabelFrame(main_frame, text="4. Hata Oluşturma ve Sendrom Analizi (Seçili Adres İçin)", padding="10")
        error_sim_labelframe.pack(fill=tk.X, pady=5)

        ttk.Label(error_sim_labelframe, text="Seçili Adres:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.selected_addr_display = ttk.Label(error_sim_labelframe, text="-")
        self.selected_addr_display.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(error_sim_labelframe, text="Orijinal Veri:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.orig_data_display = ttk.Label(error_sim_labelframe, text="-", font=("Courier", 10), wraplength=400)
        self.orig_data_display.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(error_sim_labelframe, text="Orijinal HC:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.orig_hc_display = ttk.Label(error_sim_labelframe, text="-", font=("Courier", 10), wraplength=400)
        self.orig_hc_display.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(error_sim_labelframe, text="Mevcut HC (Bellekteki):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.current_hc_in_mem_display = ttk.Label(error_sim_labelframe, text="-", font=("Courier", 10), wraplength=400)
        self.current_hc_in_mem_display.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(error_sim_labelframe, text="Hata Biti Pozisyonu (Mevcut HC'de, 1-indeksli):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.error_bit_entry = ttk.Entry(error_sim_labelframe, width=5)
        self.error_bit_entry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        self.introduce_error_button = ttk.Button(error_sim_labelframe, text="Hata Oluştur (Bellekte Değiştir)", command=self._process_introduce_error, state=tk.DISABLED)
        self.introduce_error_button.grid(row=4, column=2, padx=5, pady=5, sticky=tk.EW)
        self.clear_error_button = ttk.Button(error_sim_labelframe, text="Hatayı Temizle (Orj. HC'ye Dön)", command=self._process_clear_error, state=tk.DISABLED)
        self.clear_error_button.grid(row=4, column=3, padx=5, pady=5, sticky=tk.EW)

        self.analyze_syndrome_button = ttk.Button(error_sim_labelframe, text="Sendrom Hesapla ve Hatalı Biti Göster", command=self._process_analyze_syndrome, state=tk.DISABLED)
        self.analyze_syndrome_button.grid(row=5, column=0, columnspan=4, pady=10)

        ttk.Label(error_sim_labelframe, text="Sendrom Sonucu:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        self.syndrome_result_display = ttk.Label(error_sim_labelframe, text="-", font=("Courier", 10), foreground="blue")
        self.syndrome_result_display.grid(row=6, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)

        # 5. Durum Mesajları
        status_labelframe = ttk.LabelFrame(main_frame, text="Durum Mesajları", padding="10")
        status_labelframe.pack(fill=tk.X, pady=5)
        self.status_label = ttk.Label(status_labelframe, text="Simülatör hazır.", wraplength=600)
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        self._update_entry_placeholder() # İlk placeholder

    def _update_status(self, message, is_error=False):
        self.status_label.config(text=message, foreground="red" if is_error else "black")

    def _update_entry_placeholder(self):
        length = self.selected_data_length.get()
        self.data_entry.delete(0, tk.END)
        self.data_entry.insert(0, f"Örn: {'01' * (length // 2)}")
        self._update_status(f"Veri uzunluğu {length}-bit olarak seçildi.")

    def _process_generate_code(self):
        raw_data = self.data_entry.get().strip()
        selected_len = self.selected_data_length.get()
        if not all(c in '01' for c in raw_data) or len(raw_data) != selected_len:
            messagebox.showerror("Giriş Hatası", f"Lütfen {selected_len}-bit binary veri girin (sadece 0 ve 1).")
            self._update_status(f"{selected_len}-bit binary veri bekliyorum.", is_error=True)
            return
        
        self.current_input_data_bits = [int(bit) for bit in raw_data]
        try:
            self.current_generated_hc = generate_hamming_code(self.current_input_data_bits)
            hc_str = ''.join(map(str, self.current_generated_hc))
            self.generated_hc_display.config(text=hc_str)
            self.write_to_memory_button.config(state=tk.NORMAL)
            self._update_status(f"{selected_len}-bit veri için Hamming kodu üretildi: {hc_str}")
            # Otomatik adres öner
            next_free = self._find_next_free_memory_address()
            if next_free is not None:
                self.write_address_entry.delete(0, tk.END)
                self.write_address_entry.insert(0, str(next_free))
        except ValueError as e:
            messagebox.showerror("Kod Üretme Hatası", str(e))
            self._update_status(f"Kod üretme hatası: {e}", is_error=True)
            self.generated_hc_display.config(text="-")
            self.write_to_memory_button.config(state=tk.DISABLED)

    def _find_next_free_memory_address(self):
        for i, cell in enumerate(self.memory.memory_array):
            if cell is None or cell['data'] is None:
                return i
        return None

    def _process_write_to_memory(self):
        if not self.current_input_data_bits or not self.current_generated_hc:
            messagebox.showerror("Hata", "Önce Hamming kodu üretmelisiniz.")
            self._update_status("Önce Hamming kodu üretin.", is_error=True)
            return
        try:
            address = int(self.write_address_entry.get())
            if not (0 <= address < self.memory.size):
                messagebox.showerror("Adres Hatası", f"Bellek adresi 0 ile {self.memory.size - 1} arasında olmalıdır.")
                self._update_status("Geçersiz bellek adresi.", is_error=True)
                return
            
            self.memory.write_to_memory(address, self.current_input_data_bits, self.current_generated_hc)
            self._update_status(f"Veri ve HC adrese yazıldı: {address}")
            self.update_memory_listbox()
            self.write_to_memory_button.config(state=tk.DISABLED) # Tekrar üretmeden yazmayı engelle
            self.generated_hc_display.config(text="-") # Üretilen kodu temizle
            self.current_input_data_bits = []
            self.current_generated_hc = []
             # Otomatik olarak bir sonraki boş adresi öner
            next_free = self._find_next_free_memory_address()
            if next_free is not None:
                self.write_address_entry.delete(0, tk.END)
                self.write_address_entry.insert(0, str(next_free))
            else:
                 self.write_address_entry.delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Adres Hatası", "Geçerli bir bellek adresi (sayı) giriniz.")
            self._update_status("Geçerli bir bellek adresi (sayı) giriniz.", is_error=True)

    def update_memory_listbox(self):
        self.memory_listbox.delete(0, tk.END)
        snapshot = self.memory.get_memory_snapshot()
        for i, cell in enumerate(snapshot):
            if cell and cell['data'] is not None:
                hc_summary = ''.join(map(str,cell['hamming_code'][:20])) + ("..." if len(cell['hamming_code']) > 20 else "")
                error_marker = " (Hatalı!)" if cell.get('error_info') else ""
                self.memory_listbox.insert(tk.END, f"Adr {i:02d}: HC= {hc_summary}{error_marker}")
            else:
                self.memory_listbox.insert(tk.END, f"Adr {i:02d}: -Boş-")
        self._clear_selection_details()

    def _clear_selection_details(self):
        self.selected_addr_display.config(text="-")
        self.orig_data_display.config(text="-")
        self.orig_hc_display.config(text="-")
        self.current_hc_in_mem_display.config(text="-")
        self.error_bit_entry.delete(0, tk.END)
        self.syndrome_result_display.config(text="-")
        self.introduce_error_button.config(state=tk.DISABLED)
        self.clear_error_button.config(state=tk.DISABLED)
        self.analyze_syndrome_button.config(state=tk.DISABLED)
        self.selected_memory_address.set(-1)

    def _on_memory_select(self, event=None):
        selection = self.memory_listbox.curselection()
        if not selection:
            self._clear_selection_details()
            return
        
        selected_idx = selection[0]
        self.selected_memory_address.set(selected_idx)
        
        mem_cell = self.memory.read_from_memory(selected_idx)
        if mem_cell and mem_cell['data'] is not None:
            self.selected_addr_display.config(text=str(selected_idx))
            self.orig_data_display.config(text=''.join(map(str, mem_cell['data'])))
            self.orig_hc_display.config(text=''.join(map(str, mem_cell['original_hamming_code'])))
            self.current_hc_in_mem_display.config(text=''.join(map(str, mem_cell['hamming_code'])))
            
            self.introduce_error_button.config(state=tk.NORMAL)
            self.analyze_syndrome_button.config(state=tk.NORMAL)
            if mem_cell.get('error_info'):
                self.clear_error_button.config(state=tk.NORMAL)
            else:
                self.clear_error_button.config(state=tk.DISABLED)
            self.error_bit_entry.delete(0, tk.END)
            self.syndrome_result_display.config(text="-")
            self._update_status(f"{selected_idx} nolu bellek adresi seçildi.")
        else:
            self._clear_selection_details()
            self._update_status(f"{selected_idx} nolu adres boş veya geçersiz.", is_error=True)

    def _process_introduce_error(self):
        addr = self.selected_memory_address.get()
        if addr == -1:
            messagebox.showerror("Hata", "Lütfen bellekten bir adres seçin.")
            self._update_status("Hata eklemek için bellekten adres seçin.", is_error=True)
            return
        
        try:
            bit_pos_str = self.error_bit_entry.get()
            if not bit_pos_str:
                messagebox.showerror("Hata", "Hata eklenecek bit pozisyonunu (1-indeksli) girin.")
                return
            bit_position = int(bit_pos_str)

            # Mevcut HC'yi al ve üzerinde değişiklik yap
            mem_cell = self.memory.read_from_memory(addr)
            if not mem_cell or mem_cell['hamming_code'] is None:
                 messagebox.showerror("Hata", "Seçili adreste veri yok.")
                 return

            # Bellekteki introduce_error_at_bit fonksiyonunu kullanalım
            success, msg = self.memory.introduce_error_at_bit(addr, bit_position)
            
            if success:
                self.update_memory_listbox() # Liste güncellenecek
                self.memory_listbox.selection_set(addr) # Seçimi koru
                self._on_memory_select() # Detayları güncelle
                self._update_status(msg)
                self.syndrome_result_display.config(text="Hata eklendi. Sendromu analiz edin.")
            else:
                messagebox.showerror("Hata Oluşturma Başarısız", msg)
                self._update_status(f"Hata oluşturma başarısız: {msg}", is_error=True)

        except ValueError:
            messagebox.showerror("Giriş Hatası", "Geçerli bir bit pozisyonu (sayı) giriniz.")

    def _process_clear_error(self):
        addr = self.selected_memory_address.get()
        if addr == -1:
            messagebox.showerror("Hata", "Lütfen bellekten bir adres seçin.")
            return
        
        success, msg = self.memory.clear_error_at_address(addr)
        if success:
            self.update_memory_listbox()
            self.memory_listbox.selection_set(addr)
            self._on_memory_select()
            self._update_status(msg)
            self.syndrome_result_display.config(text="Hata temizlendi.")
        else:
            messagebox.showerror("Hata Temizleme Başarısız", msg)
            self._update_status(f"Hata temizleme başarısız: {msg}", is_error=True)

    def _process_analyze_syndrome(self):
        addr = self.selected_memory_address.get()
        if addr == -1:
            messagebox.showerror("Hata", "Lütfen bellekten bir adres seçin.")
            self._update_status("Sendrom analizi için adres seçin.", is_error=True)
            return

        mem_cell = self.memory.read_from_memory(addr)
        if not mem_cell or mem_cell['hamming_code'] is None:
            messagebox.showerror("Okuma Hatası", f"{addr} adresinde okunacak HC bulunamadı.")
            self._update_status(f"{addr} adresinde HC yok.", is_error=True)
            return

        received_hc = list(mem_cell['hamming_code']) # Kopyasını alarak çalış
        self._update_status(f"Adres {addr} için sendrom hesaplanıyor (HC: {''.join(map(str, received_hc))})")
        
        # check_and_correct_hamming_code, düzeltilmiş kodu, hata tipini ve pozisyonu döner
        # Biz burada sadece hata tipini ve pozisyonunu kullanıcıya göstermek istiyoruz.
        # Otomatik düzeltme YAPMAYACAĞIZ.
        syndrome_val, overall_parity_failed, _p_sec, _parity_pos = calculate_syndrome_and_overall_parity_check(received_hc)
        
        # Hata pozisyonunu ve tipini yorumlamak için check_and_correct_hamming_code'un mantığını kullanalım
        # Ama düzeltilmiş kodu kullanmayacağız, sadece bilgiyi alacağız.
        _corrected_code, error_type, error_pos_or_syndrome = check_and_correct_hamming_code(list(received_hc))

        result_text = f"Alınan HC: {''.join(map(str, received_hc))}\n"
        result_text += f"Sendrom Değeri: {syndrome_val} (Binary: {syndrome_val:04b})\n"
        result_text += f"Genel Parite Kontrolü: {'Başarısız (Hata Var)' if overall_parity_failed else 'Başarılı (Hata Yok veya Çift Hata)'}\n\n"

        if error_type == "no_error":
            result_text += "Durum: Hata tespit edilmedi."
        elif error_type == "single_error_corrected":
            # error_pos_or_syndrome burada hatalı bitin pozisyonunu verir
            result_text += f"Durum: Tek bitlik hata tespit edildi!\nHatalı Bit Pozisyonu (HC'de 1-indeksli): {error_pos_or_syndrome}"
        elif error_type == "double_error_detected":
            result_text += "Durum: Çift bitlik hata tespit edildi (Düzeltilemez)." 
        elif error_type == "uncorrectable_error":
            # error_pos_or_syndrome burada sendrom değerini (veya bazen -1) verir
            result_text += f"Durum: Düzeltilemeyen hata (örn: genel parite bitinde hata olabilir veya >2 bit hata). Sendrom: {error_pos_or_syndrome}"
        else:
            result_text += f"Durum: Bilinmeyen hata durumu (Tip: {error_type}, Sendrom/Poz: {error_pos_or_syndrome})"

        self.syndrome_result_display.config(text=result_text)
        self._update_status(f"Sendrom analizi tamamlandı. Sonuçlar gösteriliyor.")

if __name__ == '__main__':
    main_window = tk.Tk()
    app = HammingApp(main_window)
    main_window.mainloop() 