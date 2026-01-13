
# get kernel and corresponding top function names from command line
if { $argc != 4 } {
    puts "Usage: vitis_hls syn.tcl <episode_no> <turn_no> <kernel> <top_fxn>"
    exit 1
}

set episode_no [lindex $argv 0]
set turn_no [lindex $argv 1]
set kernel [lindex $argv 2]
set top_fxn [lindex $argv 3]

##########################
### VITIS HLS COMMANDS ###
##########################

open_project ${kernel}_${episode_no}_${turn_no}

set_top $top_fxn

add_files ./EP_${episode_no}/sources/${kernel}_${episode_no}_${turn_no}.c
open_solution "solution1" -flow_target vivado

set_part { xcvh1582-vsva3697-2MP-e-S }

create_clock -period 4 -name default

config_compile -pipeline_loops 0

#source "./${kernel}_XPRAG/solution1/directives.tcl"
#csim_design
csynth_design
#cosim_design
# export_design -format ip_catalog

exit
