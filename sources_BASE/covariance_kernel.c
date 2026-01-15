
void kernel_covariance(double float_n, double data[100][80], double cov[80][80],
                       double mean[80]) {
    int i;
    int j;
    int k;

    L0: for (j = 0; j < 80; j++) {
    // @slot __PIPE__L0
    // @slot __UNROLL__L0

        mean[j] = 0.0;

        L3: for (i = 0; i < 100; i++) {
        // @slot __PIPE__L3
        // @slot __UNROLL__L3

            mean[j] += data[i][j];
        }
        mean[j] /= float_n;
    }

    L1: for (i = 0; i < 100; i++) {
    // @slot __PIPE__L1
    // @slot __UNROLL__L1

        L4: for (j = 0; j < 80; j++) {
        // @slot __PIPE__L4
        // @slot __UNROLL__L4

            data[i][j] -= mean[j];
        }
    }

    L2: for (i = 0; i < 80; i++) {
    // @slot __PIPE__L2
    // @slot __UNROLL__L2

        L5: for (j = i; j < 80; j++) {
        // @slot __PIPE__L5
        // @slot __UNROLL__L5

            cov[i][j] = 0.0;

            L6: for (k = 0; k < 100; k++) {
            // @slot __PIPE__L6
            // @slot __UNROLL__L6

                cov[i][j] += data[k][i] * data[k][j];
            }
            cov[i][j] /= float_n - 1.0;
            cov[j][i] = cov[i][j];
        }
    }
}
