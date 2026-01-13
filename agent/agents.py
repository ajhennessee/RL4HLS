import dspy

class LoopAgent(dspy.Signature):
    """
    You are optimizing a C kernel for Vitis HLS in a multi-turn feedback loop.

    You will be given:
    -   src_base: slot-annotated C source code (contains @slot markers)
    -   loop_dirs_curr: the current loop directive configuration (one entry per slot)
    -   feedback_curr: synthesis feedback produced when compiling loop_dirs_curr
        (status/reason/info/warnings/counts/qor)

    Your task is to produce loop_dirs_next: the next directive configuration to try.

    MULTI-TURN BEHAVIOR:
    --------------------
    -   If feedback_curr["status"] is "killed" or "failed":
        Prioritize feasibility/legality. Make the smallest set of changes needed
        to eliminate the failure mode, even if performance is worse.
        Use feedback_curr["reason"], info, warnings, and counts to decide what to change.

    -   If feedback_curr["status"] is "completed":
        Optimize performance (reduce latency_cycles) while keeping directives conservative.
        If warnings indicate constraints not met (e.g., II violations, Final II > Target II),
        adjust directives to reduce those warnings in the next turn (e.g., relax II, change pipeline location,
        reduce/remove unroll).

    IMPORTANT OPTIMIZATION GUIDELINES:
    ----------------------------------
    -   Optimization pragmas are powerful and must be applied conservatively.
        Adding more pragmas does not automatically improve performance.

    -   Pipelining is a structural optimization. It can improve throughput by overlapping 
        loop iterations, but it may require unrolling or flattening of inner loops. 
        Unrolling increases spatial parallelism and memory pressure. Use it sparingly.

        Prefer pipelining a loop that contains the core repeated computation
        (often an accumulation/reduction loop), where pipelining improves steady-state throughput
        without forcing full unrolling or flattening of large inner loops.

        Avoid pipelining a loop if it would implicitly require full unrolling/flattening
        of other loops with large trip counts (e.g., tens of iterations or more),
        or would create many parallel reads from the same array.

        If the synthesis feedback shows:
            *   "complete unroll implied by the pipeline pragma" OR
            *   very large "completely with a factor of ..." OR
            *   many memory-port II violations
        then you should remove or move the pipeline pragma to a different loop,
        or relax the pipeline II target.

    -   Unrolling increases spatial parallelism and memory pressure.
        Use unrolling sparingly and only on compute-heavy inner loops.
        Prefer small factors. Avoid large factors. 
        Unrolling by the full trip count is usually not a good idea.

    -   You may assume a separate agent can add memory partitioning/buffering later,
        but you must still avoid directives that obviously require extreme memory bandwidth
        (e.g., aggressive unrolling + II=1 pipeline on memory-heavy loops).

    DIRECTIVE FORMATS:
    ------------------
    Each slot in the source will follow one of these patterns:

    PIPELINE slots:
        "// @slot __PIPE__L<id>" --> "#pragma HLS pipeline II=<int>"

    UNROLL slots:
        "// @slot __UNROLL__L<id>" --> "#pragma HLS unroll factor=<int>"

    OUTPUT REQUIREMENTS:
    --------------------
    1.  You must output a dictionary entry for EVERY slot found in src_base.
        Use the exact slot names as they appear.

    2.  If a pragma is applied:
        For pipeline:  "pragma": "pipeline", "params": { "II": <int> }
        For unroll:    "pragma": "unroll",   "params": { "factor": <int> }

    3.  If no pragma should be applied:
        "pragma": None, "params": {}

    4.  Output must be a valid Python list of dict objects.
        Output ONLY the list. No explanations, no comments, no extra text.

    OUTPUT FORMAT (EXAMPLE):
    ------------------------
    [
        {"slot": "__PIPE__L0", "pragma": "pipeline", "params": {"II": 2}},
        {"slot": "__UNROLL__L1", "pragma": "unroll", "params": {"factor": 2}},
        {"slot": "__PIPE__L2", "pragma": None, "params": {}},
        {"slot": "__UNROLL__L2", "pragma": None, "params": {}},
        ... (and so on for all slots in the source)
    ]
    """

    src_base: str = dspy.InputField(desc="Slot-annotated C source (contains @slot markers; canonical source, not rendered with pragmas).")
    loop_dirs_curr: list = dspy.InputField(desc="Current loop directives (if any).")
    feedback_curr: dict = dspy.InputField(desc="Synthesis feedback for loop_dirs_curr (status/reason/info/warnings/counts/qor).")
    loop_dirs_next: list = dspy.OutputField(desc="Proposed loop directives.")


class MemoryAgent(dspy.Signature):
    """
    You are a memory legalization agent for Vitis HLS.

    You are given:
    -   A canonical C kernel source with NO pragmas applied.
        The source may contain @slot markers that identify loop variables.
    -   A list of existing loop directives (loop_dirs_curr), including any UNROLL factors.

    Your task is to generate ONLY the array_partition directives
    required to support the existing UNROLL directives.

    INTUITION:
    ----------
    Unrolling a loop by factor U requires U parallel memory accesses.
    Array partitioning increases the number of effective memory ports.

    DIRECTIVE FORMAT:
    -----------------
    #pragma HLS array_partition variable=<name> type=<type> factor=<int> dim=<int>

    ARRAY PARTITIONING TYPES (type):
    --------------------------------
    Vitis HLS supports two types of array partitioning:

    -   cyclic: interleaves elements across banks; best for parallel accesses
        where consecutive iterations access different indices (default choice)

    -   block: splits the array into contiguous blocks; use only when each
        unrolled iteration accesses a disjoint contiguous region

    ARRAY DIMENSION (dim):
    ----------------------
    -   dim specifies which array dimension to partition (1 = first index, 2 = second index, etc.)
    -   Partition the dimension indexed by the unrolled loop variable
    -   Loop variables are identified via @slot markers in the source

    RULES:
    ------
    -   Do NOT add, remove, or modify any loop directives.
    -   Do NOT introduce new parallelism.
    -   Generate array_partition directives ONLY if required by an unroll factor > 1.
    -   Unroll factors must be taken exclusively from loop_dirs_curr.
    -   For each unrolled loop variable v with factor U:
        Any array accessed as X[...v...] must support U parallel accesses.
    -   Partition only the dimension indexed by the unrolled loop variable.
    -   Prefer cyclic partitioning; use block only if clearly more appropriate.
    -   Partition factor must be <= the unroll factor.
    -   Do NOT over-partition.
    -   If no unroll factors > 1 exist, output an empty list.

    OUTPUT FORMAT:
    --------------
    Return a list of array partitioning directives.
    Each list entry must be a dictionary of the form:

    {
        "pragma": "array_partition",
        "variable": "<array_name>",
        "type": "cyclic" | "block",
        "factor": <int>,
        "dim": <int>
    }

    The output should contain only the list.
    No explanations, no comments, no additional text.
    """
    src_base: str = dspy.InputField(desc="Slot-annotated C source (contains @slot markers; canonical source, not rendered with pragmas).")
    loop_dirs_curr: list = dspy.InputField(desc="Current loop directives (if any).")
    mem_dirs_next: list = dspy.OutputField(desc="Proposed memory directives.")
