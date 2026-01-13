
void kernel_bicg(double A[410][390], double s[390], double q[410],
                 double p[390], double r[410]) {
    int i;
    int j;

    L0: for (i = 0; i < 390; i++) {
        // @slot __UNROLL__L0

        s[i] = ((double)0);
    }

    L1: for (i = 0; i < 410; i++) {
        // @slot __PIPE__L1
        // @slot __UNROLL__L1

        q[i] = 0.0;

        L2: for (j = 0; j < 390; j++) {
            // @slot __UNROLL__L2

            s[j] += r[i] * A[i][j];
            q[i] += A[i][j] * p[j];
        }
    }
}
