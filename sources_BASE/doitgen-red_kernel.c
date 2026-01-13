void kernel_doitgen(double A[25][20][30], double C4[30][30], double sum[30]) {
    int r;
    int q;
    int p;
    int s;

    L0: for (r = 0; r < 25; r++) {
        // @slot __PIPE__L0

        L1: for (q = 0; q < 20; q++) {
            // @slot __PIPE__L1

            L2: for (p = 0; p < 30; p++) {
                // @slot __PIPE__L2

                double sum_tmp = 0.0;

                L4: for (s = 0; s < 30; s++) {
                    // @slot __UNROLL__L4

                    sum_tmp += A[r][q][s] * C4[s][p];
                }
                sum[p] = sum_tmp;
            }
            L3: for (p = 0; p < 30; p++) {
                A[r][q][p] = sum[p];
            }
        }
    }
}
