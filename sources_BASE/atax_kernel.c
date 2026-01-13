
void kernel_atax(double A[116][124], double x[124], double y[124],
                 double tmp[116]) {
    int i;
    int j;

    L0: for (i = 0; i < 124; i++)
        y[i] = ((double)0);

    L1: for (i = 0; i < 116; i++) {
        // @slot __PIPE__L1
        // @slot __UNROLL__L1

        tmp[i] = 0.0;

        L2: for (j = 0; j < 124; j++) {
            // @slot __UNROLL__L2

            tmp[i] += A[i][j] * x[j];
        }

        L3: for (j = 0; j < 124; j++) {
            // @slot __UNROLL__L3

            y[j] += A[i][j] * tmp[i];
        }
    }
}
