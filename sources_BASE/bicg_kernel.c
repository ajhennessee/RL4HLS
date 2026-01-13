
void kernel_bicg(double A[124][116], double s[116], double q[124],
                 double p[116], double r[124]) {
    int i;
    int j;

    L0: for (i = 0; i < 116; i++) {
        // @slot __UNROLL__L0

        s[i] = ((double)0);
    }

    L1: for (i = 0; i < 124; i++) {
        // @slot __PIPE__L1
        // @slot __UNROLL__L1

        q[i] = 0.0;

        L2: for (j = 0; j < 116; j++) {
            // @slot __UNROLL__L2

            s[j] += r[i] * A[i][j];
            q[i] += A[i][j] * p[j];
        }
    }
}
