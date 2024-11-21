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

if __name__ == '__main__':
    import sys
    insts = extract_aarch64(sys.argv[2])
    import json
    with open(sys.argv[1], 'w') as f:
        json.dump(insts, f, indent=2)
