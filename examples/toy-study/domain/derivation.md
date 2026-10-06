# Known-answer derivation

Let X₁,…,Xₙ be independent with P(X=−1)=P(X=1)=1/2. Then E[X]=0
and Var(X)=1. Independence gives E[mean(X)²]=1/n. For a fixed b,
E[(mean(X)+b)²]=1/n+2b E[mean(X)]+b²=1/n+b².

This establishes an expectation over the generator, not an ordering on every
finite sample. In a particular sample the paired squared-error difference is
2b mean(X)+b² and may be nonpositive. The analysis estimates its mean and
uncertainty across held-out seeds. With n=64 and b=0.25, the exact expected
MSEs are 0.015625 and 0.078125; the expected difference is 0.0625.
