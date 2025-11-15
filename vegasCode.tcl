
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
    set tracefile_arg [lindex $argv 1] ;# 2nd arg: Trace file path (e.g., vegas_seed12345.tr)
    set namfile_arg [lindex $argv 2]   ;# 3rd arg: NAM file path (e.g., vegas_seed12345.nam)
    puts "Using random seed: $seed"
    puts "Trace file: $tracefile_arg"
    puts "NAM file: $namfile_arg"
    ns-random $seed  ;# Initialize random generator (critical for reproducibility)
} else {
    # Fallback for standalone testing (not for Part C)
    set seed 0
    set tracefile_arg "vegasTrace_default.tr"
    set namfile_arg "vegas_default.nam"
    puts "Warning: Use CLI args for Part C: ns vegasCode.tcl <seed> <trace> <nam>"
    ns-random $seed
}



# derive jitter values deterministically from seed
# jitter ranges can be tuned: currently 0.00 .. 0.99 seconds (coarse but visible)
set jitter0 [expr {double($seed % 100) / 1000.0}]  ;# Jitter 1: 0-99ms (divided by 1000 instead of 100)
set jitter1 [expr {double(($seed / 100) % 100) / 1000.0}] ;# Jitter 2: 0-99ms
# Calculate final link delays (base delay + jitter; convert to seconds)
set delay_n1n3 [expr {0.5 + $jitter0}]  ;# n1-n3: 500ms base + 0-99ms jitter
set delay_n2n3 [expr {0.8 + $jitter1}]  ;# n2-n3: 800ms base + 0-99ms jitter
set delay_n4n5 [expr {0.5 + $jitter0}]  ;# n4-n5: Symmetric to n1-n3
set delay_n4n6 [expr {0.8 + $jitter1}]  ;# n4-n6: Symmetric to n2-n3
set delay_n3n4 0.05                     ;# Bottleneck (n3-n4): Fixed 50ms (no jitter → control variable)


$ns color 1 Blue
$ns color 2 Red

set namfile [open $namfile_arg w]
$ns namtrace-all $namfile
set tracefile1 [open $tracefile_arg w]
$ns trace-all $tracefile1

proc finish {} {
    global ns namfile tracefile1  ;# New: Include tracefile1 (previously missing)
    $ns flush-trace  ;# Write all buffered data to files
    close $namfile
    close $tracefile1  ;# New: Close trace file (avoids data corruption)
    # exec nam $namfile_arg &  ;# Uncomment for manual NAM visualization
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

set source1 [new Agent/TCP/Vegas]
#$ns at 0 "$source1 select_ca vegas"
$source1 set class_ 2
$source1 set ttl_ 64
$source1 set window_ 1000
$source1 set packet_size_ 1000

$ns attach-agent $n1 $source1
set sink1 [new Agent/TCPSink/Sack1]
$ns attach-agent $n5 $sink1
$ns connect $source1 $sink1
$source1 set fid_ 1

set source2 [new Agent/TCP/Vegas]
#$ns at 0.0 "$source2 select_ca vegas"
$source2 set class_ 1
$source2 set ttl_ 64
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
