#!/usr/bin/env python3

inst_class_replace = {
    # Both ZFH and ZFHMIN imply ZFA
    "INSN_CLASS_ZFH_OR_ZVFH_AND_ZFA": "INSN_CLASS_ZFHMIN_AND_ZFA",
    # Simplify Bitmanip classes
    "INSN_CLASS_ZBB_OR_ZBKB": "INSN_CLASS_ZBB",
    "INSN_CLASS_ZBC_OR_ZBKC": "INSN_CLASS_ZBC",
    # Use first class name for Zk* and Zvk*
    "INSN_CLASS_ZKND_OR_ZKNE": "INSN_CLASS_ZKND",
    "INSN_CLASS_ZVKNHA_OR_ZVKNHB": "INSN_CLASS_ZVKNHA",
    # Ignore I
    "INSN_CLASS_I": ""
}

# {instr_name: [feature1, feature2, ...] }
def extract_riscv64(riscv_opc_path):
    result = dict()
    with open(riscv_opc_path, 'r') as f:
        lines = f.readlines()
        opcodes_start = lines.index('const struct riscv_opcode riscv_opcodes[] =\n')
        for lines in lines[opcodes_start:]:
            if "_INX" in lines:
                continue
            if "INSN_MACRO" in lines:
                continue
            if "INSN_ALIAS" in lines:
                continue
            if lines.startswith('{\"'):
                inst_info = lines.strip()[1:-2].split(",")
                inst_xlen = inst_info[1].strip()
                if inst_xlen != "0" and inst_xlen != "64":
                    continue
                inst_str = inst_info[0].replace("\"","")
                inst_class = inst_info[2].strip()
                if inst_class in inst_class_replace:
                    inst_class = inst_class_replace[inst_class]
                inst_class = inst_class.replace("INSN_CLASS_","") \
                             .lower().split("_and_")
                if inst_class == [""]:
                    inst_class = []
                if inst_str in result:
                    # Compare if the only difference is C, if yes, remove C
                    if result[inst_str] != inst_class:
                        if len(result[inst_str]) == len(inst_class) + 1:
                            if 'C' in result[inst_str]:
                                result[inst_str] = inst_class
                        elif len(result[inst_str]) == len(inst_class) - 1:
                            assert('C' in inst_class and 'C' not in result[inst_str])
                        else:
                            print(f"Error: {inst_str} has different classes: {result[inst_str]} and {inst_class}")
                else:
                    result[inst_str] = inst_class
            elif lines.startswith('};'):
                break
    return result

if __name__ == '__main__':
    import sys
    insts = extract_riscv64(sys.argv[2])
    import json
    import sys
    with open(sys.argv[1], 'w') as f:
        json.dump(insts, f, indent=2)
