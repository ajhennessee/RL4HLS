from pprint import pprint
import dspy
from pathlib import Path
import subprocess
import re
import os
import signal

from agents import LoopAgent, MemoryAgent

MODEL = "openai/gpt-4.1-mini"
# TEMP = 1
# API_BASE = "http://ga013:8000/v1/"
# MAX_TOKENS = 30000
CACHE = False

class Trajectory(dspy.Module):
    def __init__(self):
        super().__init__()
        self.loop_agent = dspy.ChainOfThought(LoopAgent)
        self.memory_agent = dspy.ChainOfThought(MemoryAgent)

        lm = dspy.LM(model=MODEL, cache=CACHE)
        self.loop_agent.set_lm(lm)
        self.memory_agent.set_lm(lm)

    def refactor_loops(
        self,
        src: str,
        dirs: list,
    ) -> str:
        """
        Given the original source code and the proposed loop directives,
        return the source code with pragmas inserted at the appropriate slots
        """
        out = []
        lines = src.splitlines()

        directives = {d["slot"]: d for d in dirs}

        for line in lines:
            
            if "// @slot" in line:
                slot = line.split("// @slot")[1].strip()
                directive = directives.get(slot, {})
                pragma = directive.get("pragma")
                params = directive.get("params", {})

                if pragma == "pipeline":
                    ii = params.get("II", 1)
                    pragma_line = f"#pragma HLS pipeline II={ii}"
                elif pragma == "unroll":
                    factor = params.get("factor", 1)
                    pragma_line = f"#pragma HLS unroll factor={factor}"
                else:
                    pragma_line = ""  # No pragma

                if pragma_line:
                    out.append(pragma_line)
            else:
                out.append(line)

        return "\n".join(out)
    
    def refactor_mem(
        self,
        top_fxn: str,
        src: str,
        dirs: list,
    ) -> str:
        """
        Given the source code refactored with loop directives,
        return the source code with memory partitioning directives
        """
        out = []
        lines = src.splitlines()
        
        for line in lines:
            out.append(line)
            
            if line.strip().startswith(f"void {top_fxn}("):
                for d in dirs:
                    assert d["pragma"] == "array_partition"
                    
                    pragma_line = (
                        f"#pragma HLS array_partition "
                        f"variable={d.get('variable')} "
                        f"type={d.get('type')} "
                        f"factor={d.get('factor')} "
                        f"dim={d.get('dim')}"
                    )
                    
                    out.append(pragma_line)
            
        return "\n".join(out)
    
    LOOP_LABEL_PAT = r"L(?:\d+)(?:_L\d+)*"
    
    # detect instruction count explosion during compilation
    INFO_INSTR_COUNT_COMPILE_RE = re.compile(r"INFO:\s*\[HLS 200-1995\].*There were ([\d,]+) instructions in the design after the 'Compile/Link' phase of compilation")
    WARN_INSTR_COUNT_OTHER_RE = re.compile(r"WARNING:\s*\[HLS 200-1995\].*There were ([\d,]+) instructions in the design after the '([^']+)' phase of compilation")
    
    # detect II violations of memory ports (often diagnosed by implied unrolls)
    INFO_IMPLIED_UNROLL_RE = re.compile(rf"INFO:\s*\[HLS 214-291\].*Loop '{LOOP_LABEL_PAT}' is marked as complete unroll implied by the pipeline pragma")
    INFO_COMPLETE_UNROLL_FACTOR_RE = re.compile(rf"INFO:\s*\[HLS 214-186\].*Unrolling loop '{LOOP_LABEL_PAT}'.*completely with a factor of (\d+)")
    WARN_II_MEM_PORT_VIOL_RE = re.compile(r"WARNING:\s*\[HLS 200-885\].*II Violation.*limited memory ports")
    
    # detect II violations of loop dependencies
    WARN_II_LOOP_DEP_VIOL_RE = re.compile(r"WARNING:\s*\[HLS 200-880\].*II Violation.*carried dependence constraint")
    INFO_PIPE_RESULT_RE = re.compile(r"INFO:\s*\[HLS 200-1470\].*Pipelining result\s*:\s*Target II\s*=\s*(\d+),\s*Final II\s*=\s*(\d+),\s*Depth\s*=\s*(\d+)")
    
    def _parse_synthesis_output(self, line: str):
        if self.INFO_INSTR_COUNT_COMPILE_RE.search(line):
            return {"type": "instr_count_compile", "message": line.strip()}
        
        if self.WARN_INSTR_COUNT_OTHER_RE.search(line):
            return {"type": "instr_count_warn", "message": line.strip()}
        
        if self.INFO_IMPLIED_UNROLL_RE.search(line):
            return {"type": "implied_unroll", "message": line.strip()}
        
        if self.INFO_COMPLETE_UNROLL_FACTOR_RE.search(line):
            return {"type": "complete_unroll_factor", "message": line.strip()}
        
        if self.WARN_II_MEM_PORT_VIOL_RE.search(line):
            return {"type": "ii_mem_port_violation", "message": line.strip()}
        
        if self.WARN_II_LOOP_DEP_VIOL_RE.search(line):
            return {"type": "ii_loop_dep_violation", "message": line.strip()}
        
        if self.INFO_PIPE_RESULT_RE.search(line):
            return {"type": "pipe_result", "message": line.strip()}
        
        return None
    
    class EarlyKill(Exception):
        pass

    def synthesize_design(
        self,
        episode_no: int,
        turn_no: int,
        kernel: str,
        top_fxn: str
    ) -> dict:
        log_path = Path(f"./EP_{episode_no}/logs/{kernel}_{episode_no}_{turn_no}.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = ["vitis_hls", "syn.tcl", str(episode_no), str(turn_no), kernel, top_fxn]
        
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        with open(log_path, "w", buffering=1) as log:
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                start_new_session=True,
            )
            
            try:
                assert proc.stdout is not None
                
                instr_count_compile = []
                instr_count_warn = []
                instr_count_warn_count = 0
                
                implied_unroll = []
                complete_unroll_factor = []
                ii_mem_port_viol = []
                ii_mem_port_viol_count = 0
                
                ii_loop_dep_viol = []
                ii_loop_dep_viol_count = 0
                pipe_result = []
                
                for line in proc.stdout:
                    # print(line, end="")
                    log.write(line)
                    detect = self._parse_synthesis_output(line)
                    if detect is not None:
                        if detect["type"] == "instr_count_compile":
                            instr_count_compile.append(detect["message"])
                        elif detect["type"] == "instr_count_warn":
                            instr_count_warn.append(detect["message"])
                            instr_count_warn_count += 1
                        elif detect["type"] == "implied_unroll":
                            implied_unroll.append(detect["message"])
                        elif detect["type"] == "complete_unroll_factor":
                            complete_unroll_factor.append(detect["message"])
                        elif detect["type"] == "ii_mem_port_violation":
                            ii_mem_port_viol.append(detect["message"])
                            ii_mem_port_viol_count += 1
                        elif detect["type"] == "ii_loop_dep_violation":
                            ii_loop_dep_viol.append(detect["message"])
                            ii_loop_dep_viol_count += 1
                        elif detect["type"] == "pipe_result":
                            pipe_result.append(detect["message"])
                        
                    if instr_count_warn_count >= 3:  # heuristic: if we see 3 instruction count warnings, it's likely a real issue and we can stop the synthesis early to save time
                        raise self.EarlyKill("Instruction count explosion detected.")
                    
                    if ii_mem_port_viol_count >= 3:  # heuristic: if we see 3 II violation messages, it's likely a real issue and we can stop the synthesis early to save time
                        raise self.EarlyKill("Memory port II violations detected.")
                    
                rc = proc.wait()
                
                log_excerpts = {
                    "info": {
                        "instr_count_compile": instr_count_compile,
                        "implied_unroll": implied_unroll,
                        "complete_unroll_factor": complete_unroll_factor,
                        "pipe_result": pipe_result,
                    },
                    "warnings": {
                        "instr_count_warn": instr_count_warn,
                        "ii_mem_port_viol": ii_mem_port_viol,
                        "ii_loop_dep_viol": ii_loop_dep_viol,
                    },
                    "counts": {
                        "instr_count_warn_count": instr_count_warn_count,
                        "ii_mem_port_viol_count": ii_mem_port_viol_count,
                        "ii_loop_dep_viol_count": ii_loop_dep_viol_count,
                    }
                }
                
                if rc == 0:
                    status = {
                        "status": "completed",
                        "log_excerpts": log_excerpts
                    }
                else:
                    status = {
                        "status": "failed", 
                        "reason": f"Vitis HLS exited with code {rc}", 
                        "log_excerpts": log_excerpts
                    }
                    
            except self.EarlyKill as e:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()

                log_excerpts = {
                    "info": {
                        "instr_count_compile": instr_count_compile,
                        "implied_unroll": implied_unroll,
                        "complete_unroll_factor": complete_unroll_factor,
                        "pipe_result": pipe_result,
                    },
                    "warnings": {
                        "instr_count_warn": instr_count_warn,
                        "ii_mem_port_viol": ii_mem_port_viol,
                        "ii_loop_dep_viol": ii_loop_dep_viol,
                    },
                    "counts": {
                        "instr_count_warn_count": instr_count_warn_count,
                        "ii_mem_port_viol_count": ii_mem_port_viol_count,
                        "ii_loop_dep_viol_count": ii_loop_dep_viol_count,
                    }
                }
                
                log.write(f"\n[EARLY_KILL] {e}\n")
                status = {
                    "status": "killed",
                    "reason": str(e),
                    "log_excerpts": log_excerpts
                }
            
        # move project to results
        proj_src = Path(f"./{kernel}_{episode_no}_{turn_no}")
        proj_dst = Path(f"./EP_{episode_no}/results/{kernel}_{episode_no}_{turn_no}")
        proj_dst.parent.mkdir(parents=True, exist_ok=True)
        if proj_src.exists():
            proj_src.rename(proj_dst)
        
        return status

    def retrieve_qor(
        self,
        episode_no: int,
        turn_no: int,
        kernel: str,
    ) -> dict:
        
        util_patt = re.compile(r'\((?:~)?(\d+)%\)')
        
        rpt_path = Path(f"./EP_{episode_no}/results/{kernel}_{episode_no}_{turn_no}/solution1/syn/report/csynth.rpt")
        if not rpt_path.exists():
            return None
        
        with rpt_path.open("r", encoding="utf-8") as rpt:
            lines = rpt.readlines()
            for line in lines:
                line = line.strip()
                
                if line.startswith("|+"):
                    
                    latency_cycles = line.split("|")[4].strip()
                    
                    bram_tot = line.split("|")[10].strip().split()[0]
                    if bram_tot != "-":
                        bram_util = util_patt.search(line.split("|")[10].strip()).group(1)
                    else:
                        bram_tot = None
                        bram_util = None
                        
                    dsp_tot = line.split("|")[11].strip().split()[0]
                    if dsp_tot != "-":
                        dsp_util = util_patt.search(line.split("|")[11].strip()).group(1)
                    else:
                        dsp_tot = None
                        dsp_util = None
                        
                    ff_tot = line.split("|")[12].strip().split()[0]
                    if ff_tot != "-":
                        ff_util = util_patt.search(line.split("|")[12].strip()).group(1)
                    else:
                        ff_tot = None
                        ff_util = None
                    
                    lut_tot = line.split("|")[13].strip().split()[0]
                    if lut_tot != "-":
                        lut_util = util_patt.search(line.split("|")[13].strip()).group(1)
                    else:
                        lut_tot = None
                        lut_util = None
                    
            return {
                "latency_cycles": int(latency_cycles) if latency_cycles is not None else None,
                # "bram_tot": int(bram_tot) if bram_tot is not None else None,
                # "dsp_tot": int(dsp_tot) if dsp_tot is not None else None,
                # "ff_tot": int(ff_tot) if ff_tot is not None else None,
                # "lut_tot": int(lut_tot) if lut_tot is not None else None,
                # "bram_util": float(bram_util) if bram_util is not None else None,
                # "dsp_util": float(dsp_util) if dsp_util is not None else None,
                # "ff_util": float(ff_util) if ff_util is not None else None,
                # "lut_util": float(lut_util) if lut_util is not None else None,
            }

    def forward(
        self,
        episode_no: int,
        kernel: str,
        top_fxn: str,
        src_base: str,
    ):
        turn_no = 0
        loop_dirs_curr = []

        # retrieve and save base source
        src_base_path = Path(f"./EP_{episode_no}/sources/{kernel}_{episode_no}_{turn_no}.c")
        src_base_path.parent.mkdir(parents=True, exist_ok=True)
        src_base_path.write_text(src_base, encoding="utf-8")
        
        # synthesize base design with Vitis HLS
        status_curr = self.synthesize_design(
            episode_no=episode_no,
            turn_no=turn_no,
            kernel=kernel,
            top_fxn=top_fxn,
        )
        # pprint(status_curr)
        
        # retrieve QoR for base design
        qor_curr = None
        if status_curr["status"] == "completed":
            qor_curr = self.retrieve_qor(
                episode_no=episode_no,
                turn_no=turn_no,
                kernel=kernel,
            )
            # pprint(qor_curr)
        
        log_excerpts = status_curr.get("log_excerpts", {})
        feedback_curr = {
            "status": status_curr["status"],
            "reason": status_curr.get("reason", ""),
            "info": log_excerpts.get("info", {}),
            "warnings": log_excerpts.get("warnings", {}),
            "counts": log_excerpts.get("counts", {}),   
            "qor": qor_curr,
        }
        pprint(feedback_curr)
        
        T = 4 # number of turns per trajectory
        for t in range(1, T+1):
            print(f"\n=== TURN {t} ===")
            loop_dirs_next = self.loop_agent(src_base=src_base, loop_dirs_curr=loop_dirs_curr, feedback_curr=feedback_curr).loop_dirs_next
            pprint(loop_dirs_next)
        
            # refactor source with loop directives
            src_next = self.refactor_loops(src=src_base, dirs=loop_dirs_next)
            
            # legalize loop optimizations with memory directives
            mem_dirs_next = self.memory_agent(src_base=src_base, loop_dirs_curr=loop_dirs_next).mem_dirs_next
            if mem_dirs_next:
                src_next = self.refactor_mem(
                    top_fxn=top_fxn,
                    src=src_next,
                    dirs=mem_dirs_next,
                )
            
            # save refactored source
            src_next_path = Path(f"./EP_{episode_no}/sources/{kernel}_{episode_no}_{t}.c")
            src_next_path.parent.mkdir(parents=True, exist_ok=True)
            src_next_path.write_text(src_next, encoding="utf-8")
        
            # synthesize refactored design with Vitis HLS
            status_next = self.synthesize_design(
                episode_no=episode_no,
                turn_no=t,
                kernel=kernel,
                top_fxn=top_fxn,
            )
            pprint(status_next)
        
            # retrieve QoR for refactored design
            qor_next = None
            if status_next["status"] == "completed":
                qor_next = self.retrieve_qor(
                    episode_no=episode_no,
                    turn_no=t,
                    kernel=kernel,
                )
                pprint(qor_next)
            
            loop_dirs_curr = loop_dirs_next
            feedback_curr = {
                "status": status_next["status"],
                "reason": status_next.get("reason", ""),
                "info": status_next.get("log_excerpts", {}).get("info", {}),
                "warnings": status_next.get("log_excerpts", {}).get("warnings", {}),
                "counts": status_next.get("log_excerpts", {}).get("counts", {}),
                "qor": qor_next,
            }
        
# one episode is composed of many trajectories per kernel (K kernels with T trajectories each, all running in parallel)
# one trajectory is composed of many turns of design sampling and synthesis (t turns per trajectory, running sequentially)
