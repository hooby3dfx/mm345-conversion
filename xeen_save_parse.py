import struct
import argparse
from dataclasses import dataclass
from typing import List

# Helper function to unpack bitfields into simple boolean lists (LSB-first)
def unpack_bitfield_lsb(byte_data: bytes) -> List[bool]:
    return [bool(b & (1 << i)) for b in byte_data for i in range(8)]

def unpack_bitfield_msb(byte_data: bytes) -> List[bool]:
    # Shift from left-to-right (bit 7 down to bit 0) within each byte
    return [bool(b & (1 << (7 - i))) for b in byte_data for i in range(8)]

def pack_bitfield_compact_lsb(bool_array: List[bool]) -> bytes:
    # Group into 8-bit slices and sum them using bit-shifting
    return bytes(
        sum(int(bit) << i for i, bit in enumerate(bool_array[strt : strt + 8]))
        for strt in range(0, len(bool_array), 8)
    )

def pack_bitfield_compact_msb(bool_array: List[bool]) -> bytes:
    # Group into 8-bit slices and sum them using inverted bit-shifting (7 - i)
    return bytes(
        sum(int(bit) << (7 - i) for i, bit in enumerate(bool_array[strt : strt + 8]))
        for strt in range(0, len(bool_array), 8)
    )


@dataclass
class XeenPartyData:
    # save_name: str
    current_map_id: int
    party_x: int
    party_y: int
    party_direction: int
    gold: int
    gems: int
    food: int
    # active_party_slots: List[int]
    quest_bits: List[bool]
    autonotes_bits: List[bool]
    gameflag_bits: List[bool]

class XeenPtyParser:
    def __init__(self, data):
        self.data = data

    def parse(self) -> XeenPartyData:
        data = self.data
        print(f"{len(data)}")

        # --- 1. PARSE HEADER STRINGS & METADATA ---
        # The save title/name is usually the first 20-28 bytes null-terminated ASCIIZ
        # save_name_raw = data[0x00:0x1C]
        # save_name = save_name_raw.split(b'\x00')[0].decode('ascii', errors='ignore').strip()

        # --- 2. PARSE LOCATION DATA ---
        # Grabbing Coordinates (Typically stored right around the game state segment)
        # Using hypothetical common Xeen engine state layout offsets:
        # (Adjust exact offsets if your specific mod offset sheet differs slightly)
        current_map_id = data[0x0D]
        party_x = data[0x01]
        print(f"{party_x}")
        party_y = data[0x0C]
        party_direction = data[0x0A]

        # --- 3. PARSE ECONOMY & SUPPLIES (Unpacked via standard unsigned Int formats) ---
        # '<I' indicates Little-Endian 4-byte Unsigned Integer (uint32)
        # '<H' indicates Little-Endian 2-byte Unsigned Short (uint16)
        gold = struct.unpack("<I", data[0x27E:0x282])[0]
        gems = struct.unpack("<I", data[0x282:0x286])[0]
        food = struct.unpack("<H", data[0x26A:0x26C])[0]

        # --- 4. PARSE ACTIVE COMPANION SLOTS ---
        # The PTY maps which characters out of MAZE.CHR are actively traveling with you.
        # It's an array of 6 distinct bytes containing active database index IDs.
        # active_party_slots = list(data[0x50:0x56])

        # --- 5. UNPACK PROGRESSION BITFIELDS ---
        # Quest/Autonote progression arrays are chunks of contiguous raw byte segments.
        # We slice them out and convert them cleanly to flat Boolean flags.
        
        # Example: Global Quest Bits (e.g., 32-byte field at 0x60)
        raw_quest_bytes = data[0x2E3:0x2EB]
        quest_bits = unpack_bitfield_msb(raw_quest_bytes)

        # Example: Global Autonotes Bitfield (e.g., 16-byte field at 0x80)
        raw_autonote_bytes = data[0x2D3:0x2E3]
        autonotes_bits = unpack_bitfield_msb(raw_autonote_bytes)

        # raw_gameflag_bytes = data[0x293:0x2B3]#clouds
        raw_gameflag_bytes = data[0x2B3:0x2D3]#darkside
        gameflag_bits = unpack_bitfield_msb(raw_gameflag_bytes)

        return XeenPartyData(
            # save_name=save_name,
            current_map_id=current_map_id,
            party_x=party_x,
            party_y=party_y,
            party_direction=party_direction,
            gold=gold,
            gems=gems,
            food=food,
            # active_party_slots=active_party_slots,
            quest_bits=quest_bits,
            autonotes_bits=autonotes_bits,
            gameflag_bits=gameflag_bits,
        )


    # def write_autonotes(self, autonote_index: int, state: bool):
    #     """
    #     Modifies a single specific autonote bit directly inside the binary save file
    #     while perfectly preserving all surrounding game bytes.
    #     """
    #     # Determine exact bit configuration properties
    #     byte_offset = 0x80 + (autonote_index // 8)
    #     bit_position = autonote_index % 8

    #     with open(self.filepath, "r+b") as f:
    #         # Step 1: Read the targeted current byte mask container
    #         f.seek(byte_offset)
    #         current_byte = int.from_bytes(f.read(1), byteorder="little")

    #         # Step 2: Perform logic bitwise manipulation
    #         if state:
    #             # Turn the single bit flag ON
    #             new_byte = current_byte | (1 << bit_position)
    #         else:
    #             # Turn the single bit flag OFF
    #             new_byte = current_byte & ~(1 << bit_position)

    #         # Step 3: Flush modification cleanly back to your file stream
    #         f.seek(byte_offset)
    #         f.write(bytes([new_byte]))





if __name__ == "__main__":

    aparser = argparse.ArgumentParser(description="Inspect Xeen save file data")
    aparser.add_argument("file", help="The .SAV or .CUR file to inspect")
    args = aparser.parse_args()

    with open(args.file, "rb") as f:
        fdata = f.read()

        sav_cc_pty_offset = 14269
        sav_cc_pty_len = 1528
    
        pty_data = fdata[sav_cc_pty_offset:sav_cc_pty_offset+sav_cc_pty_len]
        print(f"{len(pty_data)}")
        # print(f"{pty_data}")

        # Point this directly to an unpacked/temporary live save file instance
        pty_parser = XeenPtyParser(pty_data)
        
        try:
            party_state = pty_parser.parse()
            # print(f"Loaded Save String: {party_state.save_name}")
            print(f"Current Position  : Map {party_state.current_map_id} at ({party_state.party_x}, {party_state.party_y})")
            # print(f"Active Roster IDs : {party_state.active_party_slots}")
            # print(f"Autonote #4 Status: {party_state.autonotes_bits[4]}")

            # print(f"quest_bits ({len(party_state.quest_bits)}): {party_state.quest_bits}")
            # print(f"autonotes_bits ({len(party_state.autonotes_bits)}): {party_state.autonotes_bits}")
            # print(f"gameflag_bits ({len(party_state.gameflag_bits)}): {party_state.gameflag_bits}")

            gameflags_true_set = [index for index, value in enumerate(party_state.gameflag_bits) if value]
            print(f"gameflags_true_set: {gameflags_true_set}")

            autonotes_true_set = [index for index, value in enumerate(party_state.autonotes_bits) if value]
            print(f"autonotes_true_set: {autonotes_true_set}")

            questbits_true_set = [index for index, value in enumerate(party_state.quest_bits) if value]
            print(f"questbits_true_set: {questbits_true_set}")

            #set autonote based on current mapid (for coraks note)
            if party_state.current_map_id < 65:
                print(f"setting autonote to {party_state.current_map_id}")
                # pty_parser.write_autonote(autonote_index=party_state.current_map_id, state=True)
                party_state.autonotes_bits = [False]*len(party_state.autonotes_bits)
                party_state.autonotes_bits[party_state.current_map_id] = True
            
            updated_autonote_bytes = pack_bitfield_compact_msb(party_state.autonotes_bits)
            print(f"updated_autonote_bytes {len(updated_autonote_bytes)} {updated_autonote_bytes}")
            #0x2D3:0x2E3


            # 01 Take the precious sea shells to the nymph Athea, and become enchanted by her siren's song.
            # 02 Present the Pirate Queen with Pearls to pacify her plunderous heart.
            # 03 Bring love to Princess Trueberry that she may once again step beyond the darkend walls of her loveless shack.
            # 04 Return the relic to the shrine of Icarus to resurrect the lonely Unicorn.
            # 05 Set free the soul of Greywind the Illusionist from the stone walls of the ruined castle.
            # 06 Release the spirit of Blackwind the Spellbinder from it's captivity in the broken keep.
            # 07 Return the Artifacts of Good to their rightful seat in castle Whiteshield.
            # 08 Return the Artifacts of Neutrality to their rightful seat in castle Bloodreign.
            # 09 Return the Artifacts of Evil to their rightful seat in castle Dragontooth.
            # 10 Render the Ultimate Power Orbs unto Zealot, King Righteous, and give strength to the hands of the good.
            # 11 Render the Ultimate Power Orbs unto Tumult, King Chaotic, and give strength to the hands of the neutral.
            # 12 Render the Ultimate Power Orbs unto Malefactor, King Malicious, and give strength to the hands of the evil.
            # 13 Find the final steps to your destiny below the Ancient Pyramids.
            # 14 Find Morphose, the Protector of Fountain Head, and release him from his magic cell.
            # 15 Deliver five Silver Skulls to Kranion, in Fountain Head, so he may finish his shrine to the Forces.
            # 16 Seek Brother Beta in the cavern under Baywatch.
            # 17 Seek Brother Gamma in Wildabar.
            # 18 Seek Brother Delta in the cavern below Wildabar
            # 19 Seek Brother Zeta in Arachnoid Cavern

            #set questbits based on mapping of gameflags set by mm3
            MM3_GAMEFLAG_TO_QUEST_MAP = {
                1:(16, True),#baywatch; alpha->beta; START
                2:(17, True),#baywatch cavern; beta->gamma; START

                4:(15, True),#fountain head; silver skulls; START
                5:(15, True),#fountain head; silver skulls; PROGRESS
                6:(15, True),#fountain head; silver skulls; PROGRESS
                7:(15, True),#fountain head; silver skulls; PROGRESS
                8:(15, True),#fountain head; silver skulls; PROGRESS
                9:(15, False),#fountain head; silver skulls; END

                170:(14, False),#fountain head; Morphose; END


            }

            updated_quest_bits = [False]*len(party_state.quest_bits)

            for gameflag in gameflags_true_set:
                if gameflag in MM3_GAMEFLAG_TO_QUEST_MAP:
                    quest_state_update = MM3_GAMEFLAG_TO_QUEST_MAP[gameflag]
                    print(f"for gameflag {gameflag}: quest_state_update {quest_state_update}")
                    party_state.quest_bits[quest_state_update[0]] = quest_state_update[1]
                    updated_quest_bits[quest_state_update[0]] = quest_state_update[1]

            updated_quest_bit_bytes = pack_bitfield_compact_msb(updated_quest_bits)
            print(f"updated_quest_bit_bytes {len(updated_quest_bit_bytes)} {updated_quest_bit_bytes}")
            #0x2E3:0x2EB

            with open(args.file+"m", "wb") as outfile:
                dest_buffer = bytearray(fdata)
                dest_buffer[sav_cc_pty_offset+0x2D3:sav_cc_pty_offset+0x2E3] = updated_autonote_bytes
                dest_buffer[sav_cc_pty_offset+0x2E3:sav_cc_pty_offset+0x2EB] = updated_quest_bit_bytes
                outfile.write(dest_buffer)



            # Automator Action: If map conditions align, trigger target note automatically
            # if party_state.current_map_id == 15 and not party_state.autonotes_bits[4]:
            #     pty_parser.write_autonote(autonote_index=4, state=True)
            #     print("Successfully flipped Note 4 to Active State via binary slice manipulation!")
                
        except FileNotFoundError:
            print("Waiting for save pipeline initialization container...")


