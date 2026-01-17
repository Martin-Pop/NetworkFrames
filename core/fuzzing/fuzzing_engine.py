import logging
import random

log = logging.getLogger(__name__)


class FuzzingEngine:
    def __init__(self, frame_manager):
        self.frame_manager = frame_manager

    def execute_fuzzing(self, base_frame_id, config):
        """
        Main entry point for fuzzing.
        :param base_frame_id: id of the source packet
        :param config: config from gui (strategy, count, target, params)
        :return: list of new frame ids
        """
        base_frame = self.frame_manager.get_frame(base_frame_id)
        if not base_frame:
            log.error(f"Fuzzing failed: Frame {base_frame_id} not found.")
            return []

        original_scapy = base_frame.scapy
        if not original_scapy:
            log.error("Fuzzing failed: No valid scapy packet data.")
            return []

        target_layer = config.get("target_layer")
        target_field = config.get("target_field")
        strategy = config.get("strategy")
        count = config.get("count", 10)
        params = config.get("params", {})

        new_frame_ids = []

        for i in range(count):
            try:
                pkt = original_scapy.copy()

                if target_layer not in pkt:
                    log.warning(f"Layer {target_layer} not found in packet.")
                    break

                layer_obj = pkt[target_layer]
                mutated_value = self._generate_value(strategy, params, layer_obj, target_field)

                setattr(layer_obj, target_field, mutated_value)

                # remove auto calculated attributes
                if hasattr(layer_obj, "chksum"):
                    del layer_obj.chksum
                if hasattr(layer_obj, "len"):
                    del layer_obj.len
                if hasattr(pkt, "len"):
                    del pkt.len

                # save
                new_frame = self.frame_manager.add(pkt)
                new_frame_ids.append(new_frame.id)

            except Exception as e:
                log.debug(f"Failed to generate fuzz packet #{i}: {e}")
                continue

        return new_frame_ids

    def _get_field_size_bits(self, layer_obj, field_name):
        """
        Helper to get bit size
        :param layer_obj: layer object
        :param field_name: field name
        :return:
        """
        try:
            for field_desc in layer_obj.fields_desc:
                if field_desc.name == field_name:
                    if hasattr(field_desc, "size"):
                        return field_desc.size
                    elif hasattr(field_desc, "sz"):
                        return field_desc.sz * 8

            # fallback 32 bits (2 bytes)
            return 32
        except Exception:
            return 32

    def _generate_value(self, strategy, params, layer_obj, field_name):
        """
        Generates a single mutated value based on strategy.
        :param strategy: generating strategy
        :param params: parameters
        :param layer_obj: packet layer
        :param field_name: layers field name
        :return: generated value
        """

        bit_width = self._get_field_size_bits(layer_obj, field_name)
        max_possible_val = (1 << bit_width) - 1

        # random int
        if strategy == "Random Integer":
            min_val = params.get("min", 0)
            max_val = params.get("max", 65535)

            val = random.randint(min_val, max_val)

            # mask to ensure it fits the field size
            return val & max_possible_val

        # bit-flip
        elif strategy == "Bit Flip":
            current_val = getattr(layer_obj, field_name)

            if isinstance(current_val, int):
                bit_to_flip = random.randint(0, bit_width - 1)
                new_val = current_val ^ (1 << bit_to_flip)

                return new_val & max_possible_val

            elif isinstance(current_val, (bytes, str)):
                if not current_val: return current_val  # empty

                is_string = isinstance(current_val, str)
                if is_string:
                    data = bytearray(current_val.encode())
                else:
                    data = bytearray(current_val)

                byte_idx = random.randint(0, len(data) - 1)
                bit_idx = random.randint(0, 7)

                data[byte_idx] ^= (1 << bit_idx)
                return data.decode(errors='ignore') if is_string else bytes(data)

            else:
                return current_val

        return None