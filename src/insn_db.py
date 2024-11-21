#!/usr/bin/env python3

# {instr_name: { "opcode,mask": [feature1, feature2, ...] } }
def extract_aarch64(tbl_path):
    path = tbl_path
    result = dict()
    feature_map = dict()
    with open(path, 'r') as f:
        lines = f.readlines()
        opcodes_start = lines.index('const struct aarch64_opcode aarch64_opcode_table[] =\n')
        for i in range(0, opcodes_start):
            if lines[i].startswith('static const aarch64_feature_set aarch64_feature_'):
                feature_name = lines[i].strip().split(" ")[-2].strip()
                line = lines[i+1].strip()
                if line.startswith("AARCH64_FEATURE ("):
                    feature_map[feature_name] = [line[17:-2].strip()]
                elif line.startswith("AARCH64_FEATURES ("):
                    feature_list = line[18:-2].strip().split(",")
                    feature_map[feature_name] = [x.strip() for x in feature_list[1:]]
        for lines in lines[opcodes_start:]:
            if lines.startswith('  { \"'):
                inst_info = lines.strip()[3:-3].split(",")
                inst_str = inst_info[0].replace("\"","")
                inst_op = inst_info[1].strip()
                inst_mask = inst_info[2].strip()
                inst_type = feature_map[inst_info[5].strip()[1:]]
                if inst_str not in result:
                    result[inst_str] = dict()
                if f"{inst_op},{inst_mask}" in result[inst_str]:
                    assert(result[inst_str][f"{inst_op},{inst_mask}"] == inst_type)
                result[inst_str][f"{inst_op},{inst_mask}"] = inst_type
    return result

def find_aarch64_class_from_objdump_line(s, db):
    # Note: objdump should use -M no-aliases
    each = s.strip().split("\t")
    if each[0][-1] == ':':
        # GNU
        inst = each[2].strip().split()[0]
        hex = each[1].strip()
    else:
        # LLVM
        inst = each[1].strip().split()[0]
        hex = each[0].strip().split(":")[1].strip()
    x = int(hex, 16)
    for k, v in db[inst].items():
        op, mask = k.split(",")
        if (x & int(mask, 16)) == int(op, 16):
            return v
    return None

# {instr_name: [feature1, feature2, ...] }
def extract_riscv64(riscv_opc_path):
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

def find_riscv64_class_from_objdump_line(s, db):
    # Note: objdump should use -M no-aliases
    each = s.strip().split("\t")
    if each[0][-1] == ':':
        # GNU
        inst = each[2].strip().split()[0]
        return db[inst]
    else:
        # LLVM
        inst = each[1].strip().split()[0]
        return db[inst]

if __name__ == '__main__':
    import sys
    insts = dict()
    if sys.argv[1] == 'aarch64':
        insts = extract_aarch64(sys.argv[3])
    elif sys.argv[1] == 'riscv64':
        insts = extract_riscv64(sys.argv[3])
    import json
    with open(sys.argv[2], 'w') as f:
        json.dump(insts, f, indent=2)
