MAX_MEMORY_LOCATIONS = 64 # Örneğin, 64 satırlık bir bellek

class MemorySimulator:
    def __init__(self, size=MAX_MEMORY_LOCATIONS):
        self.size = size
        # Bellek, her biri bir sözlük olan bir liste olarak temsil edilecek
        # Her sözlük şunları içerebilir: {'data': bit_list, 'hamming_code': bit_list, 'has_error': bool}
        self.memory_array = [None] * size
        self.initialize_memory()

    def initialize_memory(self):
        """Belleği boşaltır (None ile doldurur)."""
        self.memory_array = [{'data': None, 'hamming_code': None, 'original_hamming_code': None, 'error_info': None} for _ in range(self.size)]

    def write_to_memory(self, address, data_bits, hamming_code_bits):
        """
        Belirli bir adrese veri ve Hamming kodunu yazar.
        data_bits: Orijinal veri bitlerinin listesi.
        hamming_code_bits: Verinin Hamming kodlanmış bitlerinin listesi.
        """
        if 0 <= address < self.size:
            self.memory_array[address] = {
                'data': list(data_bits), 
                'hamming_code': list(hamming_code_bits),
                'original_hamming_code': list(hamming_code_bits), # Hata ekleme sonrası karşılaştırma için
                'error_info': None # 'single_error_introduced_at_bit_X' or 'no_error' etc.
            }
            return True
        return False # Adres geçersiz

    def read_from_memory(self, address):
        """
        Belirli bir adresten saklanan veriyi ve Hamming kodunu okur.
        """
        if 0 <= address < self.size and self.memory_array[address] and self.memory_array[address]['data'] is not None:
            return self.memory_array[address]
        return None # Adres boş veya geçersiz

    def get_memory_snapshot(self):
        """Belleğin mevcut durumunun bir kopyasını döndürür."""
        return [dict(entry) if entry['data'] is not None else None for entry in self.memory_array]

    def introduce_error_at_bit(self, address, bit_position_in_hamming_code):
        """
        Bellekteki belirli bir adresteki Hamming kodunun belirli bir bitini bozar (0 ise 1, 1 ise 0 yapar).
        bit_position_in_hamming_code: Hamming kodundaki bitin 1-indeksli pozisyonu.
        """
        if not (0 <= address < self.size):
            return False, "Invalid memory address."
        
        memory_cell = self.memory_array[address]
        if not memory_cell or memory_cell['hamming_code'] is None:
            return False, "No data at this memory address."

        hamming_code = memory_cell['hamming_code']
        if not (1 <= bit_position_in_hamming_code <= len(hamming_code)):
            return False, f"Invalid bit position. Must be between 1 and {len(hamming_code)}."

        # Biti boz (0->1, 1->0)
        bit_index = bit_position_in_hamming_code - 1 # 0-indeksli
        hamming_code[bit_index] = 1 - hamming_code[bit_index]
        memory_cell['error_info'] = f"error_introduced_at_bit_{bit_position_in_hamming_code}"
        return True, f"Error introduced at address {address}, bit {bit_position_in_hamming_code} of Hamming code."

    def clear_error_at_address(self, address):
        """
        Belirli bir adresteki hatayı temizler, Hamming kodunu orijinal haline döndürür.
        """
        if not (0 <= address < self.size):
            return False, "Invalid memory address."
        
        memory_cell = self.memory_array[address]
        if not memory_cell or memory_cell['original_hamming_code'] is None:
            return False, "No original data to restore at this memory address."

        memory_cell['hamming_code'] = list(memory_cell['original_hamming_code'])
        memory_cell['error_info'] = None
        return True, f"Error cleared at address {address}. Hamming code restored."

# Örnek Kullanım (test için):
if __name__ == '__main__':
    mem = MemorySimulator(size=16)
    sample_data = [1,0,1,0,1,0,1,0] # 8 bit data
    # Bu kısım için hamming_codec.py'dan fonksiyonlar çağrılmalı normalde
    # Şimdilik örnek bir hamming kodu kullanalım
    from hamming_codec import generate_hamming_code, check_and_correct_hamming_code

    # Test generate_hamming_code
    data_8_bit = [1,0,1,0,1,1,0,0] # m=8
    print(f"Original 8-bit Data: {data_8_bit}")
    hamming_code_8 = generate_hamming_code(data_8_bit)
    print(f"Generated SEC-DED Code (13 bits): {hamming_code_8}") # p_needed = 4 (SEC) + 1 (DED) = 5. m+p = 8+5 = 13.
    mem.write_to_memory(0, data_8_bit, hamming_code_8)

    read_val = mem.read_from_memory(0)
    print(f"Read from mem[0]: {read_val}")

    # Hata ekleme testi
    success, msg = mem.introduce_error_at_bit(0, 5) # 5. bitte hata (1-indeksli)
    print(msg)
    read_val_after_error = mem.read_from_memory(0)
    print(f"Read from mem[0] after error: {read_val_after_error}")

    # Hata düzeltme testi
    # check_and_correct_hamming_code, hamming_codec.py içinde
    if read_val_after_error:
        received_hc = read_val_after_error['hamming_code']
        corrected_code, error_type, error_pos = check_and_correct_hamming_code(received_hc)
        print(f"Error check: Type: {error_type}, Position: {error_pos}")
        print(f"Original HC: {read_val_after_error['original_hamming_code']}")
        print(f"Received HC: {received_hc}")
        print(f"Corrected HC: {corrected_code}")

        # Çift hata testi
        mem.introduce_error_at_bit(0, 7) # İkinci bir hata ekle (5. bit hala hatalı)
        read_val_double_error = mem.read_from_memory(0)
        received_hc_double = read_val_double_error['hamming_code']
        corrected_code_d, error_type_d, error_pos_d = check_and_correct_hamming_code(received_hc_double)
        print(f"\nDouble Error check: Type: {error_type_d}, Position: {error_pos_d}")
        print(f"Received HC (double error): {received_hc_double}")
        print(f"Attempted Correction: {corrected_code_d}")

    mem.clear_error_at_address(0)
    print(f"Read from mem[0] after clearing error: {mem.read_from_memory(0)}") 