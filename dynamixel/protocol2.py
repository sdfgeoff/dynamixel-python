'''Handles encoding and decoding packets for dynamixel protocol-2. This
includes constructing the various packet types (eg read packet, write packet,
ping)'''
import logging

LOGGER = logging.getLogger(__name__)


class Protocol2Bus:
    """Constructs a higher abstraction over the UART to allow sending and
    receiving protocol2 packets.
    The uart should support .read() and .write(), which should both
    return bytearrays."""
    def __init__(self, uart):
        self.uart = uart

    def ping(self, address):
        """Attempts to ping a servo. Returns the servo model number if it is
        present, or None if no servo was detected"""
        LOGGER.debug("Pinging servo %d", address)
        data = self.send_and_wait(address, 0x01, [])
        if data is not None:
            servo_id = data[1] + (data[2]<<8)
            LOGGER.debug(
                "Found servo at %d with model number %d",
                address, servo_id
            )
            return servo_id
        LOGGER.debug("No servo found at %d", address)
        return None

    def read(self, address, register, length):
        """Reads the registers on a device. Returns the data from the
        specified registers or None if there was an issue talking to the servo.
        Note that the first value returned is not the requested data but is
        the "alarm bit" that is set to non-zero if there is a problem with the
        servo.
        """
        LOGGER.debug(
            "Reading from servo %d (register %d, length %d) ",
            address, register, length
        )
        data = self.send_and_wait(address, 0x02, [
            register % 256,
            (register >> 8),
            length % 256,
            (length >> 8),
        ])
        if data is not None:
            return data
        LOGGER.debug("No useful response from servo at %d", address)
        return None

    def write(self, address, register, data):
        """Writes to an address on the device."""
        LOGGER.debug(
            "Setting servo %d (register %d, value %s) ",
            address, register, data
        )
        out_bufer = [
            register % 256,
            (register >> 8),
        ] + data
        result = self.send_and_wait(address, 0x03, out_bufer)
        return result


    def send_and_wait(self, address, instruction, parameters):
        """Sends a packet on the bus. Waits for up to max_timeout_us for
        a response. If a valid response is retrieved, it returns the servo
        error state and data as a single array (error state is the first byte
        and is zero if no error. Otherwise it returns None"""

        self.uart.flush() # Clear buffer
        packet = self._build_packet(address, instruction, parameters)
        LOGGER.debug("Sending %s", packet)
        self.uart.write(packet)
        self.uart.flush()
        sent = self.uart.read(len(packet))

        if sent != packet:
            LOGGER.error(
                'Packet sent from UART does not match what should'
                ' have been transmitted. This could be due to a bus collision'
                ' or because the timeout on the serial object did not wait'
                ' long enough'
            )
            return None

        rx_header = self.uart.read(7)
        LOGGER.debug("Got Header %s", rx_header)
        if len(rx_header) != 7:
            LOGGER.error(
                "Recieved Header incorrect length (should be 7, got %d)",
                len(rx_header)
            )
            return None

        if rx_header[0:5] != packet[0:5]:
            LOGGER.error(
                "Revieved packet with bad header or from incorrect servo"
            )
            return None
        packet_len = rx_header[5] + (rx_header[6] << 8)
        LOGGER.debug("Expecting length %d", packet_len)
        remaining = self.uart.read(packet_len)
        LOGGER.debug("Got Remaining %s (length=%d)", remaining, len(remaining))
        if len(remaining) != packet_len:
            LOGGER.error("Recieved incomplete Packet")
            return None

        full_packet = rx_header + remaining
        LOGGER.debug("Full Packet: %s", full_packet)
        read_crc = full_packet[-2] + (full_packet[-1] << 8)
        calc_crc = crc16(full_packet[:-2])
        if read_crc != calc_crc:
            LOGGER.error("Incorrect CRC")
            return None

        if full_packet[7] != 0x055:
            # All packets from servos have the "instruction" 0x55
            LOGGER.error("Not a status packet")
            return None

        error_byte = remaining[1]
        if (error_byte & 0x7F) != 0:
            LOGGER.error("Servo reports communication error: %d", error_byte)
            return None

        return remaining[1:-2]

    @staticmethod
    def _build_packet(address, instruction, parameters):
        packet = [0xFF, 0xFF, 0xFD, 0x00]
        packet.append(address)
        packet.append(len(parameters)+3 % 256)  # Packet_length_lower
        packet.append(len(parameters)+3 >> 8)  # Packet_length_higher
        packet.append(instruction)
        packet += parameters
        crc = crc16(packet)
        packet.append(crc % 256)  # crc low
        packet.append(crc >> 8)   # crc high
        return bytes(packet)

    def send_blind(self, address, instruction, parameters):
        """Sends a message without attempting to receive. This is done
        to send messages faster"""
        self.uart.write(self._build_packet(address, instruction, parameters))


# ----------------------------- CRC ------------------------------------------
CRC_TABLE = [
    0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
    0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027, 0x0022,
    0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D, 0x8077, 0x0072,
    0x0050, 0x8055, 0x805F, 0x005A, 0x804B, 0x004E, 0x0044, 0x8041,
    0x80C3, 0x00C6, 0x00CC, 0x80C9, 0x00D8, 0x80DD, 0x80D7, 0x00D2,
    0x00F0, 0x80F5, 0x80FF, 0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1,
    0x00A0, 0x80A5, 0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1,
    0x8093, 0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
    0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197, 0x0192,
    0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE, 0x01A4, 0x81A1,
    0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB, 0x01FE, 0x01F4, 0x81F1,
    0x81D3, 0x01D6, 0x01DC, 0x81D9, 0x01C8, 0x81CD, 0x81C7, 0x01C2,
    0x0140, 0x8145, 0x814F, 0x014A, 0x815B, 0x015E, 0x0154, 0x8151,
    0x8173, 0x0176, 0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162,
    0x8123, 0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
    0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104, 0x8101,
    0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D, 0x8317, 0x0312,
    0x0330, 0x8335, 0x833F, 0x033A, 0x832B, 0x032E, 0x0324, 0x8321,
    0x0360, 0x8365, 0x836F, 0x036A, 0x837B, 0x037E, 0x0374, 0x8371,
    0x8353, 0x0356, 0x035C, 0x8359, 0x0348, 0x834D, 0x8347, 0x0342,
    0x03C0, 0x83C5, 0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1,
    0x83F3, 0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
    0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7, 0x03B2,
    0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E, 0x0384, 0x8381,
    0x0280, 0x8285, 0x828F, 0x028A, 0x829B, 0x029E, 0x0294, 0x8291,
    0x82B3, 0x02B6, 0x02BC, 0x82B9, 0x02A8, 0x82AD, 0x82A7, 0x02A2,
    0x82E3, 0x02E6, 0x02EC, 0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2,
    0x02D0, 0x82D5, 0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1,
    0x8243, 0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
    0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264, 0x8261,
    0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E, 0x0234, 0x8231,
    0x8213, 0x0216, 0x021C, 0x8219, 0x0208, 0x820D, 0x8207, 0x0202
]


def crc16(data, val=0):
    """Computes dynamixels CRC"""
    val = 0
    for sample in data:
        i = (val >> 8) ^ sample & 0xFF
        val = ((val << 8) ^ CRC_TABLE[i]) % (1<<16)
    return val
