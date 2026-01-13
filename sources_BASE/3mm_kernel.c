
void kernel_3mm(double E[40][50], double A[40][60], double B[60][50], double F[50][70], double C[50][80], double D[80][70], double G[40][70]) {

    int i;
    int j;
    int k;

    /* E := A*B */

    L0: for (i = 0; i < 40; i++) {
        // @slot __PIPE__L0
        // @slot __UNROLL__L0

        L3: for (j = 0; j < 50; j++) {
            // @slot __PIPE__L3
            // @slot __UNROLL__L3

            E[i][j] = 0.0;

            L6: for (k = 0; k < 60; ++k) {
                // @slot __PIPE__L6
                // @slot __UNROLL__L6

                E[i][j] += A[i][k] * B[k][j];
            }
        }
    }

    /* F := C*D */

    L1: for (i = 0; i < 50; i++) {
        // @slot __PIPE__L1
        // @slot __UNROLL__L1

        L4: for (j = 0; j < 70; j++) {
            // @slot __PIPE__L4
            // @slot __UNROLL__L4

            F[i][j] = 0.0;

            L7: for (k = 0; k < 80; ++k) {
                // @slot __PIPE__L7
                // @slot __UNROLL__L7

                F[i][j] += C[i][k] * D[k][j];
            }
        }
    }

    /* G := E*F */

    L2:for (i = 0; i < 40; i++) {
        // @slot __PIPE__L2
        // @slot __UNROLL__L2

        L5:for (j = 0; j < 70; j++) {
            // @slot __PIPE__L5
            // @slot __UNROLL__L5

            G[i][j] = 0.0;
            
            L8: for (k = 0; k < 50; ++k) {
                // @slot __PIPE__L8
                // @slot __UNROLL__L8

                G[i][j] += E[i][k] * F[k][j];
            }
        }
    }
}
