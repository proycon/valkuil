#! /bin/csh -f

partition-factor $1 10 0 24101997
timbl -f $1.0.data -t $1.0.test -a1 +D +vdb
foreach t ( 0.5 0.6 0.7 0.75 0.8 0.85 0.9 0.925 0.95 0.975 0.99 )
  abstaining-classifier $t $1.0.test.IGTree.gr.out
end
