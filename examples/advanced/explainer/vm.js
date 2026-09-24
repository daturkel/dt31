// Interpreter for the subset of dt31 used by sudoku.dt
const DT31 = (() => {
  function stripComment(line) {
    let quoted = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === "'") quoted = !quoted;
      else if (ch === ";" && !quoted) return line.slice(0, i);
    }
    return line;
  }

  function parse(src) {
    const prog = [];
    const labels = {};
    const pending = [];
    src.split("\n").forEach((raw, ln) => {
      let text = stripComment(raw).trim();
      if (!text) return;
      const lm = text.match(/^(\w+):\s*(.*)$/);
      if (lm) {
        labels[lm[1]] = prog.length;
        text = lm[2].trim();
        if (!text) return;
      }
      const sp = text.search(/\s/);
      const op = (sp < 0 ? text : text.slice(0, sp)).toUpperCase();
      const rest = sp < 0 ? "" : text.slice(sp + 1).trim();
      const args = rest ? rest.split(",").map((s) => s.trim()) : [];
      prog.push({ op, args, line: ln });
    });

    const regNames = [];
    const regIndex = {};
    const reg = (n) => {
      if (!(n in regIndex)) {
        regIndex[n] = regNames.length;
        regNames.push(n);
      }
      return regIndex[n];
    };
    const term = (s) => {
      s = s.trim();
      let m;
      if ((m = s.match(/^R\.(\w+)$/))) return { k: 1, i: reg(m[1]) };
      if (/^-?\d+$/.test(s)) return { k: 0, v: parseInt(s, 10) };
      if ((m = s.match(/^'(.)'$/))) return { k: 0, v: m[1].charCodeAt(0) };
      return null;
    };
    const operand = (s) => {
      const mm = s.match(/^M?\[(.*)\]$/);
      if (mm) {
        const pm = mm[1].match(/^(.+?)\s*([+-])\s*(.+)$/);
        if (pm) return { k: 2, a: term(pm[1]), b: term(pm[3]), neg: pm[2] === "-" };
        return { k: 2, a: term(mm[1]), b: null, neg: false };
      }
      const t = term(s);
      if (t) return t;
      if (s in labels) return { k: 0, v: labels[s], label: s };
      throw new Error("Unknown operand " + s);
    };
    for (const ins of prog) {
      ins.a = ins.args.map(operand);
      ins.out = ins.a[2] || ins.a[0];
    }
    return { prog, labels, regNames, regIndex };
  }

  class VM {
    constructor(parsed) {
      this.p = parsed;
      this.prog = parsed.prog;
      // Instruction indices just after each `CALL draw_cell`: reached once per placement or undo
      this.afterDraw = new Uint8Array(this.prog.length + 1);
      this.prog.forEach((ins, i) => {
        if (ins.op === "CALL" && ins.args[0] === "draw_cell") this.afterDraw[i + 1] = 1;
      });
      this.onOutput = () => {};
    }

    reset(inputText) {
      this.R = new Float64Array(this.p.regNames.length);
      this.M = new Int32Array(2048);
      this.S = [];
      this.ip = 0;
      this.steps = 0;
      this.halted = false;
      this.exitCode = null;
      this.error = null;
      this.input = inputText.replace(/\n$/, "").split("\n");
      this.inPos = 0;
    }

    reg(name) {
      return this.R[this.p.regIndex[name]];
    }

    addr(o) {
      let a = this.val(o.a);
      if (o.b) a = o.neg ? a - this.val(o.b) : a + this.val(o.b);
      if (a < 0 || a >= 2048) throw new Error("memory has no index " + a);
      return a;
    }

    val(o) {
      if (o.k === 0) return o.v;
      if (o.k === 1) return this.R[o.i];
      return this.M[this.addr(o)];
    }

    set(o, v) {
      if (o.k === 1) this.R[o.i] = v;
      else this.M[this.addr(o)] = v;
    }

    step() {
      const ins = this.prog[this.ip];
      if (!ins) {
        this.halted = true;
        return;
      }
      const a = ins.a;
      this.steps++;
      switch (ins.op) {
        case "CP": this.set(a[1], this.val(a[0])); this.ip++; break;
        case "ADD": this.set(ins.out, this.val(a[0]) + this.val(a[1])); this.ip++; break;
        case "SUB": this.set(ins.out, this.val(a[0]) - this.val(a[1])); this.ip++; break;
        case "MUL": this.set(ins.out, this.val(a[0]) * this.val(a[1])); this.ip++; break;
        case "DIV": this.set(ins.out, Math.floor(this.val(a[0]) / this.val(a[1]))); this.ip++; break;
        case "MOD": {
          const y = this.val(a[1]);
          this.set(ins.out, ((this.val(a[0]) % y) + y) % y);
          this.ip++;
          break;
        }
        case "BAND": this.set(ins.out, this.val(a[0]) & this.val(a[1])); this.ip++; break;
        case "BOR": this.set(ins.out, this.val(a[0]) | this.val(a[1])); this.ip++; break;
        case "BXOR": this.set(ins.out, this.val(a[0]) ^ this.val(a[1])); this.ip++; break;
        case "BSL": this.set(ins.out, this.val(a[0]) << this.val(a[1])); this.ip++; break;
        case "BSR": this.set(ins.out, this.val(a[0]) >> this.val(a[1])); this.ip++; break;
        case "JMP": this.ip = a[0].v; break;
        case "JEQ": this.ip = this.val(a[1]) === this.val(a[2]) ? a[0].v : this.ip + 1; break;
        case "JNE": this.ip = this.val(a[1]) !== this.val(a[2]) ? a[0].v : this.ip + 1; break;
        case "JLT": this.ip = this.val(a[1]) < this.val(a[2]) ? a[0].v : this.ip + 1; break;
        case "JLE": this.ip = this.val(a[1]) <= this.val(a[2]) ? a[0].v : this.ip + 1; break;
        case "JGT": this.ip = this.val(a[1]) > this.val(a[2]) ? a[0].v : this.ip + 1; break;
        case "JGE": this.ip = this.val(a[1]) >= this.val(a[2]) ? a[0].v : this.ip + 1; break;
        case "JIF": this.ip = this.val(a[1]) ? a[0].v : this.ip + 1; break;
        case "CALL": this.S.push(this.ip + 1); this.ip = a[0].v; break;
        case "RET": this.ip = this.S.pop(); break;
        case "PUSH": this.S.push(this.val(a[0])); this.ip++; break;
        case "POP": this.set(a[0], this.S.pop()); this.ip++; break;
        case "COUT":
          this.onOutput(String.fromCharCode(this.val(a[0])) + (a[1] && this.val(a[1]) ? "\n" : ""));
          this.ip++;
          break;
        case "NOUT":
          this.onOutput(String(this.val(a[0])) + (a[1] && this.val(a[1]) ? "\n" : ""));
          this.ip++;
          break;
        case "SSTRIN": {
          if (this.inPos >= this.input.length) {
            this.set(a[1], 0);
          } else {
            const s = this.input[this.inPos++];
            const base = this.addr(a[0]);
            for (let k = 0; k < s.length; k++) this.M[base + k] = s.charCodeAt(k);
            this.M[base + s.length] = 0;
            this.set(a[1], 1);
          }
          this.ip++;
          break;
        }
        case "EXIT":
          this.steps--;
          this.halted = true;
          this.exitCode = a[0] ? this.val(a[0]) : 0;
          break;
        default:
          throw new Error("Unsupported instruction " + ins.op);
      }
    }
  }

  return { parse, VM };
})();
if (typeof module !== "undefined") module.exports = DT31;
