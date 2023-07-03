
# CS 656 - Assignment 2

Author : Prerona Ghosh

Student ID: 21048873



## Description

The goal of this assignment is to implement a Congestion Controlled pipelined Reliable Data Transfer (RDT) protocol over UDP, which could be used to transfer a text file from one host to another across an unreliable network. The protocol implemented is unidirectional and we can transfer data from only sender to the receiver programs and not the other way around.

The sender and receiver programs are written in Python3. So, there is no need for a makefile or compilation to run them. 


## Execution Instructions

The programs are written in Python3. So, there is no need for a makefile or compilation.

To start the tests, run the following commands either on the same hosts or three different hosts: 

Start the unreliable network:
```bash
   python3 network_emulator.py 9991 host2 9994 9993 host3 9992 1 0.2 0
```

Start the receiver:
```bash
  python3 receiver.py host1 9993 9994 output.txt
```

Start the sender:
```bash
  python3 sender.py host1 9991 9992 50 input.txt
```


## Testing/Examples

The above programs have been tested on Windows 11 machine, as well as the CS Ubuntu student servers at the University of Waterloo. The details of the tests run on UW Ubuntu servers are as follows:

First start the network emulator on host `ubuntu2204-002`:
```bash
python3 network_emulator.py 50412 ubuntu2004-004 50413 50414 ubuntu2004-006 50415 1 0.2 0
```

Secondly, start the receiver on host `ubuntu2204-004`:

```bash
python3 receiver.py ubuntu2004-002 50414 50413 output
```

Finally, start the sender on host `ubuntu2204-006`:

```bash
python3 sender.py ubuntu2004-002 50412 50415 50 sampledata
```

Here, `sampledata` is the input data file that has to be transferred and `output` is the file that will contain the data received by the receiver program.  

Finally, I have compared the sampledata file to the output file to check for any differences by using the following command:

```bash
diff sampledata output
```

I have made sure that there were no differences between the two files.

I have used the file `sampledata` which would require more than 32 packets to transmit and the file `input2` to test data transfer which would need less than 32 packets.
## Versions

I have used Python version `3.10.11` to implement this assignment.

