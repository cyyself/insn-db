.PHONY: all clean
all: out/riscv64-class.json out/aarch64-class.json
out/riscv64-class.json: ext/binutils-gdb/opcodes/riscv-opc.c src/insn_db.py out
	python3 src/insn_db.py riscv64 $@ $<

out/aarch64-class.json: build/aarch64-tbl-preprocessed.h src/insn_db.py out
	python3 src/insn_db.py aarch64 $@ $<

build/aarch64-tbl-preprocessed.h: build/aarch64-tbl-noinc.h
	gcc -DVERIFIER -E $< -o $@

build/aarch64-tbl-noinc.h: ext/binutils-gdb/opcodes/aarch64-tbl.h build
	cat $< | grep -v "#include" > $@

out:
	mkdir -p out

build:
	mkdir -p build

ext/binutils-gdb/opcodes/riscv-opc.c:
	git submodule update --init ext/binutils-gdb

ext/binutils-gdb/opcodes/aarch64-tbl.h:
	git submodule update --init ext/binutils-gdb

clean:
	rm -rf out build
