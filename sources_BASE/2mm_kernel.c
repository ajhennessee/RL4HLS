
void kernel_2mm(double alpha, double beta, double tmp[40][50], double A[40][70], double B[70][50], double C[50][80], double D[40][80]) {
    
    int i;
    int j;
    int k;

    /* D := alpha*A*B*C + beta*D */

    L0: for (i = 0; i < 40; i++) {
        // @slot __PIPE__L0
        // @slot __UNROLL__L0

        L2: for (j = 0; j < 50; j++) {
            // @slot __PIPE__L2
            // @slot __UNROLL__L2

            tmp[i][j] = 0.0;

            L4: for (k = 0; k < 70; ++k) {
                // @slot __PIPE__L4
                // @slot __UNROLL__L4

                tmp[i][j] += alpha * A[i][k] * B[k][j];
            }
        }
    }

    L1: for (i = 0; i < 40; i++) {
        // @slot __PIPE__L1
        // @slot __UNROLL__L1

        L3: for (j = 0; j < 80; j++) {
            // @slot __PIPE__L3
            // @slot __UNROLL__L3

            D[i][j] *= beta;

            L5: for (k = 0; k < 50; ++k) {
                // @slot __PIPE__L5
                // @slot __UNROLL__L5

                D[i][j] += tmp[i][k] * C[k][j];
            }
        }
    }
}
