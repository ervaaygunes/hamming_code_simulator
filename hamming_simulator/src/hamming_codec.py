def get_num_hamming_parities(data_length):
    """
    Calculates the number of Hamming parity bits (p_sec) needed for SEC for a given data length (m).
    Condition: 2^p_sec >= m + p_sec + 1
    """
    p_sec = 0
    while (2**p_sec) < (data_length + p_sec + 1):
        p_sec += 1
    return p_sec

def get_hamming_parity_positions(num_hamming_parities, sec_code_length):
    """
    Returns a list of 1-indexed positions for Hamming parity bits.
    """
    positions = []
    for i in range(num_hamming_parities):
        pos = 2**i
        if pos <= sec_code_length: # Ensure position is within the SEC code length
             positions.append(pos)
        else: # Should not happen if p_sec is calculated correctly for m
            break 
    return positions

def generate_hamming_code(data_bits_input):
    """
    Generates the Hamming SEC-DED code for the given data bits (list of 0s and 1s).
    1. Creates an SEC code (data + Hamming parities).
    2. Appends an overall parity bit to make it SEC-DED.
    """
    m = len(data_bits_input)
    if m not in [8, 16, 32]:
        raise ValueError("Data length must be 8, 16, or 32 bits.")
    
    data_bits = list(data_bits_input)
    p_sec = get_num_hamming_parities(m)
    n_sec = m + p_sec  # Length of the SEC codeword part

    # Determine positions for Hamming parity bits within the SEC codeword
    hamming_parity_actual_positions = get_hamming_parity_positions(p_sec, n_sec)

    # Initialize SEC codeword
    sec_codeword = [0] * n_sec
    data_idx = 0
    # Place data bits in non-parity positions
    for i in range(n_sec):
        current_pos = i + 1
        if current_pos not in hamming_parity_actual_positions:
            if data_idx < m:
                sec_codeword[i] = data_bits[data_idx]
                data_idx += 1
            # Else, it's a non-parity, non-data slot, should not happen with correct p_sec

    # Calculate and set Hamming parity bits in the SEC codeword
    for p_pos in hamming_parity_actual_positions:
        ones_count = 0
        for bit_idx_check in range(n_sec):
            current_check_pos = bit_idx_check + 1
            if current_check_pos == p_pos: # Do not include the parity bit itself in its own sum calculation (for setting)
                continue
            if (current_check_pos & p_pos) != 0: # Check if p_pos bit is set in current_check_pos's binary form
                if sec_codeword[bit_idx_check] == 1:
                    ones_count += 1
        # Set parity bit for even parity sum (XOR sum of covered bits should be 0)
        # Standard Hamming uses odd parity for the check bits (parity bit is 1 if covered data bits sum to odd)
        # Let's stick to the convention: parity bit is set to make the number of 1s in the positions it checks (itself included for syndrome) even.
        # So, if ones_count of data bits it covers is odd, parity bit is 1. If even, parity bit is 0.
        sec_codeword[p_pos-1] = 1 if ones_count % 2 != 0 else 0

    # Calculate the overall parity bit for SEC-DED (appended at the end)
    # This bit makes the total number of 1s in the (sec_codeword + overall_parity_bit) even.
    overall_parity_val = sum(sec_codeword) % 2 # if sum(sec_codeword) is odd, P_overall=1. if even, P_overall=0
    
    secded_codeword = sec_codeword + [overall_parity_val]
    return secded_codeword


def calculate_syndrome_and_overall_parity_check(secded_codeword_input):
    """
    Calculates the syndrome from the SEC part of the SEC-DED codeword
    and checks the overall parity bit.
    Returns:
        - syndrome (int): The syndrome value (0 if no error in SEC part check bits).
        - overall_parity_is_odd (bool): True if the received SEC-DED codeword has an odd number of 1s (overall parity fails).
        - p_sec_inferred (int): Number of Hamming parity bits inferred.
        - hamming_parity_positions (list): List of 1-indexed Hamming parity bit positions used for syndrome.
    """
    secded_codeword = list(secded_codeword_input)
    n_secded = len(secded_codeword)

    if n_secded == 0:
        return 0, False, 0, []

    sec_part = secded_codeword[:-1]
    n_sec = len(sec_part)

    # Infer p_sec (number of Hamming parity bits) from n_sec
    # p_sec is the largest k such that 2^k <= n_sec
    # More accurately, it's the count of power-of-2 positions up to n_sec.
    p_sec_inferred = 0
    temp_idx = 0
    hamming_parity_positions = []
    while True:
        pos = 2**temp_idx
        if pos <= n_sec:
            p_sec_inferred += 1
            hamming_parity_positions.append(pos)
            temp_idx += 1
        else:
            break
        if temp_idx > 10: break # Safety break for unexpected n_sec

    # Calculate syndrome using Hamming parity bits for the sec_part
    syndrome = 0
    for p_pos in hamming_parity_positions: # These are 1, 2, 4, 8...
        ones_count = 0
        # Each parity bit p_pos checks all positions (including itself) in sec_part
        # where the p_pos bit is set in the position's binary representation.
        for bit_idx in range(n_sec):
            current_check_pos = bit_idx + 1 # 1-indexed position in sec_part
            if (current_check_pos & p_pos) != 0:
                if sec_part[bit_idx] == 1:
                    ones_count += 1
        
        if ones_count % 2 != 0: # If an odd number of 1s are found in the checked bits, this parity check fails
            syndrome += p_pos # Add the position of the failed parity check to the syndrome

    # Check overall parity of the full SEC-DED codeword
    total_ones_in_secded = sum(secded_codeword)
    overall_parity_is_odd = (total_ones_in_secded % 2 != 0) # True if odd (means check fails for even convention)

    return syndrome, overall_parity_is_odd, p_sec_inferred, hamming_parity_positions


def check_and_correct_hamming_code(secded_codeword_input):
    """
    Checks the received SEC-DED Hamming code for errors.
    Returns:
        - corrected_code (list of 0s and 1s) - For UI, this is not auto-applied to memory.
        - error_type (str: "no_error", "single_error_corrected", "double_error_detected", "uncorrectable_error")
        - error_position (int: 1-indexed position of error, 0 if no error, -1 for double error, syndrome for uncorrected)
    """
    secded_codeword = list(secded_codeword_input)
    n_secded = len(secded_codeword)

    if n_secded == 0:
        return [], "uncorrectable_error", -1 # Or some indicator of empty input

    syndrome, overall_parity_is_odd, p_sec, _ = calculate_syndrome_and_overall_parity_check(secded_codeword)
    
    # P is the state of the overall parity check on the received word.
    # If overall_parity_is_odd is True, P Fails (P=1). If False, P is OK (P=0).

    if syndrome == 0:
        if not overall_parity_is_odd:  # S=0, P=0 (overall parity OK)
            return secded_codeword, "no_error", 0
        else:  # S=0, P=1 (overall parity Fails)
            # This indicates an error in the overall parity bit itself.
            error_pos = n_secded  # The overall parity bit is the last bit (1-indexed)
            corrected_code = list(secded_codeword)
            corrected_code[error_pos - 1] = 1 - corrected_code[error_pos - 1]
            return corrected_code, "single_error_corrected", error_pos
    else:  # syndrome != 0
        if overall_parity_is_odd:  # S!=0, P=1 (overall parity Fails)
            # This indicates a single error in the SEC part (data or Hamming parity bits).
            # The syndrome value directly indicates the 1-indexed error position within the SEC part.
            error_pos_in_secded = syndrome 
            
            if 0 < error_pos_in_secded <= (n_secded -1) : # Error is within the SEC part
                corrected_code = list(secded_codeword)
                corrected_code[error_pos_in_secded - 1] = 1 - corrected_code[error_pos_in_secded - 1]
                
                # Verify this correction actually results in S'=0 and P'=0
                s_prime, p_prime_is_odd, _, _ = calculate_syndrome_and_overall_parity_check(corrected_code)
                if s_prime == 0 and not p_prime_is_odd:
                    return corrected_code, "single_error_corrected", error_pos_in_secded
                else:
                    # If flipping bit 'syndrome' does not lead to S=0,P=0, it's an uncorrectable error
                    # (e.g., more than one error in SEC part, or a three-bit error in total code).
                    return secded_codeword, "uncorrectable_error", syndrome 
            else: # Syndrome points to an invalid position (e.g. outside SEC part, or 0)
                 return secded_codeword, "uncorrectable_error", syndrome
        else:  # S!=0, P=0 (overall parity OK)
            # This indicates a double bit error.
            return secded_codeword, "double_error_detected", -1 # Syndrome value is not the error position here. 