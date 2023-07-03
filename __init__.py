from binaryninja.binaryview import BinaryView, DataVariable
from binaryninja.log import Logger
from binaryninja.types import IntegerType, PointerType

from typing import List

logger = Logger(session_id=0, logger_name="rust_string_slicer")


def recover_string_slices_from_readonly_data(bv: BinaryView):
    if bv.arch is None:
        logger.log_error("Could not get architecture of current binary view, exiting")
        return

    readonly_segments = list(
        filter(
            lambda segment: segment.readable
            and not segment.writable
            and not segment.executable,
            bv.segments,
        )
    )

    # Obtain all data vars which are pointers to data in readonly data segments
    data_vars_to_ro_segment_data: List[DataVariable] = []
    for _data_var_addr, candidate_string_slice_data_ptr in bv.data_vars.items():
        if isinstance(candidate_string_slice_data_ptr.type, PointerType):
            for readonly_segment in readonly_segments:
                if candidate_string_slice_data_ptr.value in readonly_segment:
                    data_vars_to_ro_segment_data.append(candidate_string_slice_data_ptr)
                    logger.log_debug(
                        f"Found pointer var at {candidate_string_slice_data_ptr.address:#x} ({candidate_string_slice_data_ptr}) pointing to {candidate_string_slice_data_ptr.value:#x} "
                    )

    # Try to read an integer following the data var,
    # and treat it as a candidate for a string slice length.
    for candidate_string_slice_data_ptr in data_vars_to_ro_segment_data:
        candidate_string_slice_len_addr = (
            candidate_string_slice_data_ptr.address
            + candidate_string_slice_data_ptr.type.width
        )

        # Filter out anything at the candidate address
        # that's already defined as any data var type which is not an integer.
        existing_data_var_at_candidate_string_slice_len_addr = bv.get_data_var_at(
            candidate_string_slice_len_addr
        )
        if existing_data_var_at_candidate_string_slice_len_addr is not None:
            if not isinstance(
                existing_data_var_at_candidate_string_slice_len_addr.type, IntegerType
            ):
                continue

        candidate_string_slice_len = bv.read_int(
            address=candidate_string_slice_len_addr,
            size=bv.arch.default_int_size,
            sign=False,
            endian=bv.arch.endianness,
        )

        logger.log_debug(
            f"Pointer var at {candidate_string_slice_data_ptr.address:#x} is followed by integer with value {candidate_string_slice_len:#x}"
        )

        # Filter out any potential string slice which has length 0
        if candidate_string_slice_len == 0:
            continue

        # Attempt to read out the pointed to value as a string slice, with the length obtained above.
        candidate_string_slice = bv.read(
            addr=candidate_string_slice_data_ptr.value,
            length=candidate_string_slice_len,
        )

        logger.log_debug(
            f"Obtained candidate string slice with addr {candidate_string_slice_data_ptr.value:#x}, len {candidate_string_slice_len:#x}: {candidate_string_slice}"
        )

        # Sanity check whether the recovered string is valid UTF-8
        try:
            candidate_utf8_string = candidate_string_slice.decode("utf-8")
            logger.log_info(
                f'Recovered string at addr {candidate_string_slice_data_ptr.value:#x}, len {candidate_string_slice_len:#x}: "{candidate_utf8_string}"'
            )
        except UnicodeDecodeError as err:
            logger.log_warn(
                "Candidate string slice {candidate_string_slice} does not decode to a valid UTF-8 string; excluding from final results: {err}"
            )
            continue


recover_string_slices_from_readonly_data(bv)
