from dataclasses import dataclass
from typing import List

from binaryninja.binaryview import BinaryView, DataVariable
from binaryninja.enums import MediumLevelILOperation, SectionSemantics
from binaryninja.log import Logger
from binaryninja.mediumlevelil import MediumLevelILConst
from binaryninja.plugin import BackgroundTaskThread
from binaryninja.types import (
    ArrayType,
    IntegerType,
    PointerType,
    StructureBuilder,
    Type,
)

logger = Logger(session_id=0, logger_name=__name__)


@dataclass
class RustStringSlice:
    address: int
    length: int
    data: bytes

    def __repr__(self):
        return f"StringSlice(address={self.address:#x}, length={self.length:#x}, data={self.data!r})"

    @classmethod
    def check_binary_ninja_type_exists(cls, bv: BinaryView) -> bool:
        return bv.get_type_by_name("RustStringSlice") is not None

    @classmethod
    def create_binary_ninja_type(cls, bv: BinaryView):
        if bv.arch is not None:
            rust_string_slice_bn_type_obj = StructureBuilder.create(packed=True)
            rust_string_slice_bn_type_obj.append(
                type=PointerType.create(arch=bv.arch, type=Type.char()), name="address"
            )
            rust_string_slice_bn_type_obj.append(
                type=IntegerType.create(width=bv.arch.address_size), name="length"
            )

            bv.define_user_type(
                name="RustStringSlice",
                type_obj=rust_string_slice_bn_type_obj,
            )
            logger.log_info(f"Defined new RustStringSlice type")

    @classmethod
    def create_binary_ninja_instance(cls, bv: BinaryView, location: int, name: str):
        bv.define_user_data_var(addr=location, var_type="RustStringSlice", name=name)
        logger.log_info(f"Defined new RustStringSlice at {location:#x}")


class RecoverStringFromReadOnlyDataTask(BackgroundTaskThread):
    def __init__(self, bv: BinaryView):
        super().__init__(
            initial_progress_text="Recovering strings from readonly data...",
            can_cancel=True,
        )
        self.bv = bv

    def run(self):
        if self.bv.arch is None:
            logger.log_error(
                "Could not get architecture of current binary view, exiting"
            )
            return

        readonly_segments = list(
            filter(
                lambda segment: segment.readable
                and not segment.writable
                and not segment.executable,
                self.bv.segments,
            )
        )

        readonly_sections = list(
            filter(
                lambda section: section.semantics
                == SectionSemantics.ReadOnlyDataSectionSemantics,
                self.bv.sections.values(),
            )
        )

        if len(readonly_segments) == 0 and len(readonly_sections) == 0:
            logger.log_error(
                "Could not find any read-only segments or sections in binary, exiting"
            )
            return

        self.bv.begin_undo_actions()
        # Obtain all data vars which are pointers to data in read-only data segments or sections
        data_vars_to_readonly_data: List[DataVariable] = []
        for (
            _data_var_addr,
            candidate_string_slice_data_ptr,
        ) in self.bv.data_vars.items():
            if isinstance(candidate_string_slice_data_ptr.type, PointerType):
                for readonly_segment_or_section in (
                    readonly_segments + readonly_sections
                ):
                    if (
                        candidate_string_slice_data_ptr.value
                        in readonly_segment_or_section
                    ):
                        data_vars_to_readonly_data.append(
                            candidate_string_slice_data_ptr
                        )
                        logger.log_debug(
                            f"Found pointer var at {candidate_string_slice_data_ptr.address:#x} ({candidate_string_slice_data_ptr}) pointing to {candidate_string_slice_data_ptr.value:#x} "
                        )

        recovered_string_slices: List[RustStringSlice] = []
        for candidate_string_slice_data_ptr in data_vars_to_readonly_data:
            # Try to read an integer following the data var,
            # and treat it as a candidate for a string slice length.
            candidate_string_slice_len_addr = (
                candidate_string_slice_data_ptr.address
                + candidate_string_slice_data_ptr.type.width
            )

            # Filter out anything at the candidate address
            # that's already defined as any data var type which is not an integer.
            existing_data_var_at_candidate_string_slice_len_addr = (
                self.bv.get_data_var_at(candidate_string_slice_len_addr)
            )
            if existing_data_var_at_candidate_string_slice_len_addr is not None:
                if not isinstance(
                    existing_data_var_at_candidate_string_slice_len_addr.type,
                    IntegerType,
                ):
                    continue

            candidate_string_slice_len = self.bv.read_int(
                address=candidate_string_slice_len_addr,
                size=self.bv.arch.address_size,  # In Rust's definition of the `str` type, this length is a `usize`, which is defined to be the same size as the size of pointers for the platform.
                sign=False,
                endian=self.bv.arch.endianness,
            )

            logger.log_debug(
                f"Pointer var at {candidate_string_slice_data_ptr.address:#x} is followed by integer with value {candidate_string_slice_len:#x}"
            )

            # Filter out any potential string slice which has length 0
            if candidate_string_slice_len == 0:
                continue
            # Filter out any potential string slice which is too long
            if candidate_string_slice_len >= 0x1000:  # TODO: maybe change this limit
                continue

            # Attempt to read out the pointed to value as a string slice, with the length obtained above.
            try:
                candidate_string_slice = self.bv.read(
                    addr=candidate_string_slice_data_ptr.value,
                    length=candidate_string_slice_len,
                )
            except Exception as err:
                logger.log_error(
                    f"Failed to read from address {candidate_string_slice_data_ptr.value} with length {candidate_string_slice_len}: {err}"
                )
                continue

            logger.log_debug(
                f"Obtained candidate string slice with addr {candidate_string_slice_data_ptr.value:#x}, len {candidate_string_slice_len:#x}: {candidate_string_slice}"
            )

            # Sanity check whether the recovered string is valid UTF-8
            try:
                candidate_utf8_string = candidate_string_slice.decode("utf-8")
                logger.log_info(
                    f'Recovered string at addr {candidate_string_slice_data_ptr.value:#x}, len {candidate_string_slice_len:#x}: "{candidate_utf8_string}"'
                )

                # Append the final string slice object to the list of recovered strings.
                recovered_string_slices.append(
                    RustStringSlice(
                        address=candidate_string_slice_data_ptr.value,
                        length=candidate_string_slice_len,
                        data=candidate_string_slice,
                    )
                )

                # Set the char[<candidate_string_slice_len>] type on the location pointed to by the data var.
                existing_string_slice_data = self.bv.get_data_var_at(
                    candidate_string_slice_data_ptr.value
                )
                if existing_string_slice_data is not None:
                    self.bv.undefine_user_data_var(
                        addr=candidate_string_slice_data_ptr.value
                    )

                self.bv.define_user_data_var(
                    addr=candidate_string_slice_data_ptr.value,
                    var_type=Type.array(
                        type=Type.char(), count=candidate_string_slice_len
                    ),
                )

                # Set the RustStringSlice type on the location of the data var.
                RustStringSlice.create_binary_ninja_instance(
                    bv=self.bv,
                    location=candidate_string_slice_data_ptr.address,
                    name=f'str_"{candidate_utf8_string}"',
                )

            except UnicodeDecodeError as err:
                logger.log_warn(
                    f"Candidate string slice {candidate_string_slice} does not decode to a valid UTF-8 string; excluding from final results: {err}"
                )
                continue
        self.bv.commit_undo_actions()
        self.bv.update_analysis()


class RecoverStringFromCodeTask(BackgroundTaskThread):
    def __init__(self, bv: BinaryView):
        super().__init__(
            initial_progress_text="Recovering strings from code...",
            can_cancel=True,
        )
        self.bv = bv

    def run(self):
        # char const data_14003ca50[0x27] = "{size limit reached}SizeLimitExhausted", 0
        # ->
        # 0 @ 14002c910  (MLIL_SET_VAR rcx_1 = (MLIL_VAR rdx))
        # 1 @ 14002c913  (MLIL_SET_VAR rdx_1 = (MLIL_CONST_PTR "SizeLimitExhausted"))
        # 2 @ 14002c91a  (MLIL_SET_VAR r8 = (MLIL_CONST 0x12))
        # 3 @ 14002c920  (MLIL_TAILCALL return (MLIL_CONST_PTR core::fmt::Formatter::write_str)() __tailcall)
        #
        # ->
        # 61 @ 14002c89b  (MLIL_SET_VAR rdx_4 = (MLIL_CONST_PTR "{size limit reached}SizeLimitExhausted"))
        # 62 @ 14002c8a2  (MLIL_SET_VAR r8_2 = (MLIL_CONST 0x14))
        # 63 @ 14002c8a8  (MLIL_SET_VAR rcx_5 = (MLIL_VAR rsi))
        # 64 @ 14002c8ab  (MLIL_CALL rax_2 = (MLIL_CONST_PTR core::fmt::Formatter::write_str)())
        # 65 @ 14002c8b2  (MLIL_IF if ((MLIL_CMP_NE (MLIL_VAR rax_2) != (MLIL_CONST 0))) then 59 @ 0x14002c8ba else 72 @ 0x14002c8b4)

        # 14003ca00  char const data_14003ca00[0x38] = "`fmt::Error` from `SizeLimitedFmtAdapter` was discarded", 0
        # ->
        # 66 @ 14002c8e5  (MLIL_SET_VAR var_b8 = (MLIL_CONST_PTR &str_"C:\Users\runneradmi...01f\rustc-demangle-0.1.21\src\lib.rs"))
        # 67 @ 14002c8ea  (MLIL_SET_VAR rcx_7 = (MLIL_CONST_PTR "`fmt::Error` from `SizeLimitedFmtAdapter` was discarded"))
        # 68 @ 14002c8f1  (MLIL_SET_VAR r9 = (MLIL_CONST_PTR &data_14003c198))
        # 69 @ 14002c8fd  (MLIL_SET_VAR rdx_6 = (MLIL_CONST 0x37))
        # 70 @ 14002c902  (MLIL_CALL (MLIL_CONST_PTR _ZN4core6result13unwrap_failed17h45a312f1aaedd5feE)())
        # 71 @ 14002c902  (MLIL_NORET noreturn)

        if self.bv.arch is None:
            logger.log_error(
                "Could not get architecture of current binary view, exiting"
            )
            return None

        readonly_segments = list(
            filter(
                lambda segment: segment.readable
                and not segment.writable
                and not segment.executable,
                self.bv.segments,
            )
        )
        if len(readonly_segments) == 0:
            logger.log_error("Could not find any read-only segment in binary, exiting")
            return None

        # TODO: Since the xref from data method is more reliable, we probably want to always do that as the first pass
        # track which ones didn't work after that first pass, and only do the ones that didn't work after the first pass here

        # Obtain all data vars which are themselves already identified char arays, in readonly data segments.
        # TODO: what about non-ascii strings? will binja type them to char arrays in its initial autoanalysis?
        self.bv.begin_undo_actions()
        char_array_data_vars_in_ro_segment: List[DataVariable] = []
        for _data_var_addr, candidate_string_slice_data in self.bv.data_vars.items():
            if isinstance(candidate_string_slice_data.type, ArrayType):
                for readonly_segment in readonly_segments:
                    if candidate_string_slice_data.address in readonly_segment:
                        char_array_data_vars_in_ro_segment.append(
                            candidate_string_slice_data
                        )
                        logger.log_debug(
                            f"Found char array var at {candidate_string_slice_data.address:#x} ({candidate_string_slice_data}) with value {candidate_string_slice_data.value} "
                        )

        # Find cross-references to those data vars, from code.
        for data_var in char_array_data_vars_in_ro_segment:
            code_refs = self.bv.get_code_refs(data_var.address)
            for code_ref in code_refs:
                if code_ref.mlil is not None:
                    logger.log_info(f"{code_ref.address:#x}: {code_ref.mlil.instr}")

                    # Obtain more information about the instruction at the cross reference.
                    # Is the pointer being read, or written to?
                    # Is the other operand a register, or a memory location?
                    if code_ref.mlil.instr.operation in (
                        MediumLevelILOperation.MLIL_SET_VAR,
                        MediumLevelILOperation.MLIL_SET_VAR_FIELD,
                    ):
                        # Data pointer is being written to a var; look for a write of a constant to a var, for the length.
                        # Note that it may not be the next instruction!
                        # Filter so that we only look after the cross-referenced instruction, but still within the same basic block.
                        for instruction in filter(
                            lambda instr: instr.instr_index > code_ref.mlil.instr_index,
                            code_ref.mlil.il_basic_block,
                        ):
                            logger.log_info(
                                f"instruction: {instruction.instr_index}, {instruction}"
                            )
                            for detailed_operand in instruction.detailed_operands:
                                if detailed_operand[0] == "src" and isinstance(
                                    detailed_operand[1], MediumLevelILConst
                                ):
                                    candidate_string_slice_data = data_var.value
                                    candidate_string_slice_length = detailed_operand[
                                        1
                                    ].value.value
                                    logger.log_info(
                                        f"Reference to data var at {data_var.address:#x} with value {candidate_string_slice_data} is followed by store of integer with value {candidate_string_slice_length}"
                                    )
                                    logger.log_info(
                                        f"Candidate string: {candidate_string_slice_data[:candidate_string_slice_length]}"
                                    )

                                    self.bv.define_user_data_var(
                                        addr=data_var.address,
                                        var_type=Type.array(
                                            type=Type.char(),
                                            count=candidate_string_slice_length,
                                        ),
                                    )
                                    logger.log_info(
                                        f"Defined string: {candidate_string_slice_data[:candidate_string_slice_length]}"
                                    )

        self.bv.commit_undo_actions()
        self.bv.update_analysis()


def action_recover_string_slices_from_code(bv: BinaryView):
    if not RustStringSlice.check_binary_ninja_type_exists(bv):
        RustStringSlice.create_binary_ninja_type(bv)
    RecoverStringFromCodeTask(bv=bv).start()


def action_recover_string_slices_from_readonly_data(bv: BinaryView):
    if not RustStringSlice.check_binary_ninja_type_exists(bv):
        RustStringSlice.create_binary_ninja_type(bv)
    RecoverStringFromReadOnlyDataTask(bv=bv).start()
