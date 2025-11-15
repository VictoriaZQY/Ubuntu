# Simulation Topology
#              n1                  n5
#               \                  /
#   4000Mb,500ms \   1000Mb,50ms  / 4000Mb,500ms
#              n3 --------------- n4
#   4000Mb,800ms /                \ 4000Mb,800ms
#               /                  \
#             n2                   n6 


set ns [new Simulator]

# Accept command line arguments for random seed
if {$argc >= 3} {
    set seed [lindex $argv 0]          ;# 1st arg: Random seed (controls simulation randomness)
    set tracefile_arg [lindex $argv 1] ;# 2nd arg: Path for trace file (includes seed to avoid overwrites)
    set namfile_arg [lindex $argv 2]   ;# 3rd arg: Path for NAM visualization file
    puts "Using random seed: $seed"
    puts "Trace file saved to: $tracefile_arg"
    puts "NAM file saved to: $namfile_arg"
    ns-random $seed  ;# Critical: Initialize random number generator for reproducibility
} else {
    # Fallback for standalone testing (NOT for Part C batch runs)
    set seed 0
    set tracefile_arg "yeahTrace_default.tr"
    set namfile_arg "yeah_default.nam"
    puts "Warning: Insufficient CLI arguments. Use: ns yeahCode.tcl <seed> <trace_file> <nam_file>"
    ns-random $seed
}


# Derive jitter deterministically from seed (same seed → same jitter for consistency)
set jitter0 [expr {double($seed % 100) / 1000.0}]  ;# Jitter 1: 0-99ms (for n1-n3/n4-n5)
set jitter1 [expr {double(($seed / 100) % 100) / 1000.0}] ;# Jitter 2: 0-99ms (for n2-n3/n4-n6)
# Calculate final link delays (base delay + jitter; convert to seconds for ns2)
set delay_n1n3 [expr {0.5 + $jitter0}]  ;# n1-n3: 500ms base + 0-99ms jitter
set delay_n2n3 [expr {0.8 + $jitter1}]  ;# n2-n3: 800ms base + 0-99ms jitter
set delay_n4n5 [expr {0.5 + $jitter0}]  ;# n4-n5: Symmetric to n1-n3 (preserve topology balance)
set delay_n4n6 [expr {0.8 + $jitter1}]  ;# n4-n6: Symmetric to n2-n3
set delay_n3n4 0.05                     ;# Bottleneck link (n3-n4): Fixed 50ms (core variable → no jitter)

$ns color 1 Blue
$ns color 2 Red

set namfile [open $namfile_arg w]
$ns namtrace-all $namfile
set tracefile1 [open $tracefile_arg w]
$ns trace-all $tracefile1

proc finish {} {
    global ns namfile tracefile1  ;# New: Added tracefile1 to global scope
    $ns flush-trace  ;# Write all buffered simulation data to files
    # Close all open files
    close $namfile
    close $tracefile1  ;# New: Critical for saving trace data
    # Uncomment below to auto-launch NAM (not recommended for batch runs)
    # exec nam $namfile_arg &
    exit 0
}

set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node]

$ns duplex-link $n1 $n3 4000Mb $delay_n1n3 DropTail  ;# New: Jitter-adjusted (prev: 500ms)
$ns duplex-link $n2 $n3 4000Mb $delay_n2n3 DropTail  ;# New: Jitter-adjusted (prev: 800ms)
$ns duplex-link $n3 $n4 1000Mb $delay_n3n4 DropTail  ;# Unchanged: Bottleneck (1000Mb/50ms)
$ns duplex-link $n4 $n5 4000Mb $delay_n4n5 DropTail  ;# New: Jitter-adjusted (prev: 500ms)
$ns duplex-link $n4 $n6 4000Mb $delay_n4n6 DropTail  ;# New: Jitter-adjusted (prev: 800ms)

$ns queue-limit $n3 $n4 10
$ns queue-limit $n4 $n3 10

$ns duplex-link-op $n1 $n3 orient right-down
$ns duplex-link-op $n2 $n3 orient right-up
$ns duplex-link-op $n3 $n4 orient right
$ns duplex-link-op $n4 $n5 orient right-up
$ns duplex-link-op $n4 $n6 orient right-down

set source1 [new Agent/TCP/Linux]
$ns at 0.0 "$source1 select_ca yeah"
$source1 set class_ 2
$source1 set ttl_ 64
$source1 set windowSize_ 8
$source1 set window_ 1000
$source1 set packet_size_ 1000

$ns attach-agent $n1 $source1
set sink1 [new Agent/TCPSink/Sack1]
$ns attach-agent $n5 $sink1
$ns connect $source1 $sink1
$source1 set fid_ 1

set source2 [new Agent/TCP/Linux]
$ns at 0.0 "$source2 select_ca yeah"
$source2 set class_ 1
$source2 set ttl_ 64
$source2 set windowSize_ 8
$source2 set window_ 1000
$source2 set packet_size_ 1000

$ns attach-agent $n2 $source2
set sink2 [new Agent/TCPSink/Sack1]
$ns attach-agent $n6 $sink2
$ns connect $source2 $sink2
$source2 set fid_ 2

$source1 attach $tracefile1
$source1 tracevar cwnd_
$source1 tracevar ssthresh_
$source1 tracevar ack_
$source1 tracevar maxseq_
$source1 tracevar rtt_

$source2 attach $tracefile1
$source2 tracevar cwnd_ 
$source2 tracevar ssthresh_
$source2 tracevar ack_
$source2 tracevar maxseq_
$source2 tracevar rtt_


set myftp1 [new Application/FTP]
$myftp1 attach-agent $source1


set myftp2 [new Application/FTP]
$myftp2 attach-agent $source2


$ns at 0.0 "$myftp2 start"
$ns at 0.0 "$myftp1 start"

$ns at 100.0 "finish"

$ns run
