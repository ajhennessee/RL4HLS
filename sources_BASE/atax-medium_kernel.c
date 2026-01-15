
void kernel_atax(double A[390][410], double x[410], double y[410],
                 double tmp[390]) {
    int i;
    int j;
    
    for (i = 0; i < 410; i++)
        y[i] = ((double)0);

    L0: for (i = 0; i < 390; i++) {
    // @slot __PIPE__L0
    // @slot __UNROLL__L0

        tmp[i] = 0.0;

        L1: for (j = 0; j < 410; j++) {
        // @slot __PIPE__L1
        // @slot __UNROLL__L1

            tmp[i] += A[i][j] * x[j];
        }

        L2: for (j = 0; j < 410; j++) {
        // @slot __PIPE__L2
        // @slot __UNROLL__L2

            y[j] += A[i][j] * tmp[i];
        }
    }
}
